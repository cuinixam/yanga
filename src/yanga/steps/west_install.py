import io
import json
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Optional

import yaml
from mashumaro.config import TO_DICT_ADD_OMIT_NONE_FLAG, BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from pypeline.domain.pipeline import PipelineStep

from yanga.domain.config import WestManifest, WestManifestFile
from yanga.domain.execution_context import ExecutionContext


@dataclass
class WestInstallExecutionInfo(DataClassJSONMixin):
    dependency_dirs: list[Path] = field(default_factory=list)

    class Config(BaseConfig):
        """Base configuration for JSON serialization with omitted None values."""

        code_generation_options: ClassVar[list[str]] = [TO_DICT_ADD_OMIT_NONE_FLAG]

    @classmethod
    def from_json_file(cls, file_path: Path) -> "WestInstallExecutionInfo":
        try:
            result = cls.from_dict(json.loads(file_path.read_text()))
        except Exception as e:
            output = io.StringIO()
            traceback.print_exc(file=output)
            raise UserNotificationException(output.getvalue()) from e
        return result

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict(omit_none=True), indent=2)

    def to_json_file(self, file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.to_json_string())


class WestInstall(PipelineStep[ExecutionContext]):
    def __init__(self, execution_context: ExecutionContext, group_name: str, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__(execution_context, group_name, config)
        self.logger = logger.bind()
        self.artifacts_locator = execution_context.create_artifacts_locator()
        self._collected_dependencies: Optional[WestManifest] = None
        self.execution_info = WestInstallExecutionInfo()
        # One needs to keep track of the installed external dependencies to get the required paths
        # even if the step does not need to run.
        self.execution_info_file = self.output_dir.joinpath("west_install_exec_info.json")

    @property
    def output_dir(self) -> Path:
        return self.execution_context.create_artifacts_locator().variant_build_dir

    def get_name(self) -> str:
        return self.__class__.__name__

    @property
    def dependency_dirs(self) -> list[Path]:
        return self.execution_info.dependency_dirs

    @property
    def west_manifest_file(self) -> Path:
        """Generated west.yaml file path in variant-specific directory."""
        return self.artifacts_locator.variant_build_dir.joinpath("west.yaml")

    @property
    def global_west_manifest_file(self) -> Path:
        """Global west.yaml file path (if exists)."""
        return self.project_root_dir.joinpath("west.yaml")

    def _collect_dependencies(self) -> WestManifest:
        """Collect West dependencies from global, platform, and variant configurations."""
        collected_manifest = WestManifest()

        # Start with global west.yaml if it exists
        if self.global_west_manifest_file.exists():
            try:
                global_manifest_file = WestManifestFile.from_file(self.global_west_manifest_file)
                global_manifest = global_manifest_file.manifest

                # Merge remotes
                for remote in global_manifest.remotes:
                    if remote not in collected_manifest.remotes:
                        collected_manifest.remotes.append(remote)

                # Merge projects (dependencies)
                for project in global_manifest.projects:
                    if project not in collected_manifest.projects:
                        collected_manifest.projects.append(project)

            except Exception as e:
                self.logger.warning(f"Failed to parse global west.yaml: {e}")

        # Add platform dependencies
        if self.execution_context.platform and self.execution_context.platform.west_manifest:
            platform_manifest = self.execution_context.platform.west_manifest

            # Merge remotes
            for remote in platform_manifest.remotes:
                if remote not in collected_manifest.remotes:
                    collected_manifest.remotes.append(remote)

            # Merge projects (dependencies)
            for project in platform_manifest.projects:
                if project not in collected_manifest.projects:
                    collected_manifest.projects.append(project)

        # Add variant dependencies
        if self.execution_context.variant and self.execution_context.variant.west_manifest:
            variant_manifest = self.execution_context.variant.west_manifest

            # Merge remotes
            for remote in variant_manifest.remotes:
                if remote not in collected_manifest.remotes:
                    collected_manifest.remotes.append(remote)

            # Merge projects (dependencies)
            for project in variant_manifest.projects:
                if project not in collected_manifest.projects:
                    collected_manifest.projects.append(project)

        return collected_manifest

    def _generate_west_manifest(self, manifest: WestManifest) -> None:
        """Generate west.yaml file from collected dependencies."""
        if not manifest.remotes and not manifest.projects:
            self.logger.info("No West dependencies found. Skipping west.yaml generation.")
            return

        west_config = {"manifest": {"remotes": [remote.to_dict() for remote in manifest.remotes], "projects": [project.to_dict() for project in manifest.projects]}}

        # Convert url_base back to url-base for west compatibility
        for remote in west_config["manifest"]["remotes"]:
            if "url_base" in remote:
                remote["url-base"] = remote.pop("url_base")

        # Ensure build directory exists
        self.west_manifest_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.west_manifest_file, "w") as f:
            yaml.dump(west_config, f, default_flow_style=False)

        self.logger.info(f"Generated west.yaml with {len(manifest.projects)} dependencies")

    def run(self) -> int:
        self.logger.debug(f"Run {self.get_name()} step. Output dir: {self.output_dir}")

        try:
            # Collect dependencies from all sources
            self._collected_dependencies = self._collect_dependencies()

            # Generate the combined west.yaml file
            self._generate_west_manifest(self._collected_dependencies)

            # Only proceed with west commands if we have dependencies
            if not self._collected_dependencies.projects:
                self.logger.info("No West dependencies to install.")
                return 0

            # Initialize west workspace with shared external directory
            # The west.yaml is variant-specific, but dependencies go to shared build/external
            self.execution_context.create_process_executor(
                [
                    "west",
                    "init",
                    "-l",
                    "--mf",
                    self.west_manifest_file.as_posix(),
                    self.artifacts_locator.external_dependencies_dir.as_posix(),
                ],
                cwd=self.project_root_dir,
            ).execute()

            # Update dependencies in the shared external directory
            self.execution_context.create_process_executor(
                ["west", "update"],
                cwd=self.artifacts_locator.external_dependencies_dir.parent,  # build directory
            ).execute()

            # Track the created dependency directories
            self._track_dependency_directories()

            # Save execution info for dependency tracking
            self.execution_info.to_json_file(self.execution_info_file)

        except Exception as e:
            raise UserNotificationException(f"Failed to initialize and update with west: {e}") from e

        return 0

    def _track_dependency_directories(self) -> None:
        """Track all directories created by west for dependencies."""
        if not self._collected_dependencies:
            return

        external_dir = self.artifacts_locator.external_dependencies_dir

        # Add the main external dependencies directory
        if external_dir.exists():
            self.execution_info.dependency_dirs.append(external_dir)

        # Add individual dependency directories based on their configured paths
        for project in self._collected_dependencies.projects:
            # Extract the actual directory name from the path
            # If path is "external/clanguru", we want just "clanguru"
            # because west creates directories relative to the external_dir
            path_parts = Path(project.path).parts
            if path_parts and path_parts[0] == "external" and len(path_parts) > 1:
                # Use the directory name after "external/"
                dependency_dir = external_dir / path_parts[1]
            else:
                # Use the full path as-is
                dependency_dir = external_dir / project.path

            if dependency_dir.exists():
                self.execution_info.dependency_dirs.append(dependency_dir)
                self.logger.debug(f"Tracked dependency directory: {dependency_dir}")

        # Make the list unique while preserving order
        self.execution_info.dependency_dirs = list(dict.fromkeys(self.execution_info.dependency_dirs))

    def get_inputs(self) -> list[Path]:
        inputs = []

        # Add global west.yaml if it exists
        if self.global_west_manifest_file.exists():
            inputs.append(self.global_west_manifest_file)

        # Add user config files (platform and variant configs are in there)
        inputs.extend(self.execution_context.user_config_files)

        return inputs

    def get_outputs(self) -> list[Path]:
        outputs = [self.west_manifest_file, self.execution_info_file]

        # Add tracked dependency directories if available (after run() has been called)
        if self.execution_info.dependency_dirs:
            outputs.extend(self.execution_info.dependency_dirs)
        # Fallback: add main external directory if dependencies exist but haven't been tracked yet
        elif self._collected_dependencies and self._collected_dependencies.projects:
            outputs.append(self.artifacts_locator.external_dependencies_dir)

        return outputs

    def update_execution_context(self) -> None:
        if self.execution_info_file.exists():
            execution_info = WestInstallExecutionInfo.from_json_file(self.execution_info_file)
            # Make the dependency directories available to subsequent steps
            if execution_info.dependency_dirs:
                # Make the list unique and keep the order
                unique_paths = list(dict.fromkeys(execution_info.dependency_dirs))
                self.execution_context.add_install_dirs(unique_paths)
