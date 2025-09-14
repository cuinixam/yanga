import io
import json
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from mashumaro.config import BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from py_app_dev.core.scoop_wrapper import ScoopWrapper
from pypeline.domain.pipeline import PipelineStep

from yanga.domain.config import ScoopApp, ScoopBucket, ScoopManifest, ScoopManifestFile
from yanga.domain.execution_context import ExecutionContext


@dataclass
class ScoopInstallExecutionInfo(DataClassJSONMixin):
    install_dirs: list[Path] = field(default_factory=list)
    env_vars: dict[str, Any] = field(default_factory=dict)

    class Config(BaseConfig):
        # Make sure to omit None values during serialization
        omit_none = True

    @classmethod
    def from_json_file(cls, file_path: Path) -> "ScoopInstallExecutionInfo":
        try:
            result = cls.from_dict(json.loads(file_path.read_text()))
        except Exception as e:
            output = io.StringIO()
            traceback.print_exc(file=output)
            raise UserNotificationException(output.getvalue()) from e
        return result

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_json_file(self, file_path: Path) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.to_json_string())


def create_scoop_wrapper() -> ScoopWrapper:
    return ScoopWrapper()


class ScoopInstall(PipelineStep[ExecutionContext]):
    def __init__(self, execution_context: ExecutionContext, group_name: str, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__(execution_context, group_name, config)
        self.logger = logger.bind()
        self.artifacts_locator = execution_context.create_artifacts_locator()
        self._collected_dependencies: Optional[ScoopManifest] = None
        self.execution_info = ScoopInstallExecutionInfo()
        # One needs to keep track of the installed apps to get the required paths
        # even if the step does not need to run.
        self.execution_info_file = self.output_dir.joinpath("scoop_install_exec_info.json")

    @property
    def output_dir(self) -> Path:
        return self.execution_context.create_artifacts_locator().variant_build_dir

    def get_name(self) -> str:
        return self.__class__.__name__

    @property
    def install_dirs(self) -> list[Path]:
        return self.execution_info.install_dirs

    @property
    def scoop_manifest_file(self) -> Path:
        """Generated scoopfile.json file path in variant-specific directory."""
        return self.artifacts_locator.variant_build_dir.joinpath("scoopfile.json")

    @property
    def global_scoop_manifest_file(self) -> Path:
        """Global scoopfile.json file path (if exists)."""
        return self.project_root_dir.joinpath("scoopfile.json")

    def _collect_dependencies(self) -> ScoopManifest:
        """Collect Scoop dependencies from global, platform, and variant configurations."""
        collected_manifest = ScoopManifest()

        # Start with global scoopfile.json if it exists
        if self.global_scoop_manifest_file.exists():
            try:
                global_manifest_file = ScoopManifestFile.from_file(self.global_scoop_manifest_file)

                # Merge buckets
                self._merge_buckets(collected_manifest, global_manifest_file.buckets)

                # Merge apps
                self._merge_apps(collected_manifest, global_manifest_file.apps)

            except Exception as e:
                self.logger.warning(f"Failed to parse global scoopfile.json: {e}")

        # Add platform dependencies
        if self.execution_context.platform and self.execution_context.platform.scoop_manifest:
            platform_manifest = self.execution_context.platform.scoop_manifest

            # Merge buckets
            self._merge_buckets(collected_manifest, platform_manifest.buckets)

            # Merge apps
            self._merge_apps(collected_manifest, platform_manifest.apps)

        # Add variant dependencies
        if self.execution_context.variant and self.execution_context.variant.scoop_manifest:
            variant_manifest = self.execution_context.variant.scoop_manifest

            # Merge buckets
            self._merge_buckets(collected_manifest, variant_manifest.buckets)

            # Merge apps
            self._merge_apps(collected_manifest, variant_manifest.apps)

        return collected_manifest

    def _merge_buckets(self, target_manifest: ScoopManifest, source_buckets: list[ScoopBucket]) -> None:
        """Merge buckets, handling conflicts when same name has different sources."""
        for bucket in source_buckets:
            # Check if a bucket with this name already exists
            existing_bucket = next((b for b in target_manifest.buckets if b.name == bucket.name), None)

            if existing_bucket is None:
                # No conflict, add the bucket
                target_manifest.buckets.append(bucket)
            elif existing_bucket.source != bucket.source:
                # Conflict: same name, different source
                self.logger.warning(
                    f"Bucket '{bucket.name}' defined multiple times with different sources:\n"
                    f"  Existing: {existing_bucket.source}\n"
                    f"  New: {bucket.source}\n"
                    f"  Keeping existing definition."
                )
                # Keep the first definition (existing_bucket), ignore the new one

    def _merge_apps(self, target_manifest: ScoopManifest, source_apps: list[ScoopApp]) -> None:
        """Merge apps, avoiding duplicates."""
        for app in source_apps:
            if app not in target_manifest.apps:
                target_manifest.apps.append(app)

    def _generate_scoop_manifest(self, manifest: ScoopManifest) -> None:
        """Generate scoopfile.json file from collected dependencies."""
        if not manifest.buckets and not manifest.apps:
            self.logger.info("No Scoop dependencies found. Skipping scoopfile.json generation.")
            return

        scoop_config = {
            "buckets": [bucket.to_dict() for bucket in manifest.buckets],
            "apps": [app.to_dict() for app in manifest.apps],
        }

        # Convert field names to the format expected by ScoopWrapper
        for bucket in scoop_config["buckets"]:
            bucket["Name"] = bucket.pop("name")
            bucket["Source"] = bucket.pop("source")

        for app in scoop_config["apps"]:
            app["Name"] = app.pop("name")
            app["Source"] = app.pop("source")
            # Handle optional version field
            if "version" in app:
                app["Version"] = app.pop("version")

        # Ensure build directory exists
        self.scoop_manifest_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.scoop_manifest_file, "w") as f:
            json.dump(scoop_config, f, indent=2)

        self.logger.info(f"Generated scoopfile.json with {len(manifest.buckets)} buckets and {len(manifest.apps)} apps")

    def run(self) -> int:
        self.logger.debug(f"Run {self.get_name()} step. Output dir: {self.output_dir}")

        try:
            # Collect dependencies from all sources
            self._collected_dependencies = self._collect_dependencies()

            # Generate the combined scoopfile.json file
            self._generate_scoop_manifest(self._collected_dependencies)

            # Only proceed with scoop commands if we have dependencies
            if not self._collected_dependencies.apps:
                self.logger.info("No Scoop dependencies to install.")
                return 0

            # Install scoop dependencies using the generated manifest file
            installed_apps = create_scoop_wrapper().install(self.scoop_manifest_file)

            self.logger.debug("Installed apps:")
            for app in installed_apps:
                self.logger.debug(f" - {app.name} ({app.version})")
                self.execution_info.install_dirs.extend(app.get_all_required_paths())
                # Collect environment variables from each app
                self.execution_info.env_vars.update(app.env_vars)

            # Save execution info for dependency tracking
            self.execution_info.to_json_file(self.execution_info_file)

        except Exception as e:
            raise UserNotificationException(f"Failed to install scoop dependencies: {e}") from e

        return 0

    def get_inputs(self) -> list[Path]:
        inputs = []

        # Add global scoopfile.json if it exists
        if self.global_scoop_manifest_file.exists():
            inputs.append(self.global_scoop_manifest_file)

        # Add user config files (platform and variant configs are in there)
        inputs.extend(self.execution_context.user_config_files)

        return inputs

    def get_outputs(self) -> list[Path]:
        outputs = [self.scoop_manifest_file, self.execution_info_file]

        # Add tracked install directories if available (after run() has been called)
        if self.execution_info.install_dirs:
            outputs.extend(self.execution_info.install_dirs)

        return outputs

    def update_execution_context(self) -> None:
        if self.execution_info_file.exists():
            execution_info = ScoopInstallExecutionInfo.from_json_file(self.execution_info_file)
            # Make the list unique and keep the order
            unique_paths = list(dict.fromkeys(execution_info.install_dirs))
            # Update the install directories for the subsequent steps
            self.execution_context.add_install_dirs(unique_paths)
            if execution_info.env_vars:
                self.execution_context.add_env_vars(execution_info.env_vars)
