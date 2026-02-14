import io
import json
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from mashumaro.config import BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin
from poks.domain import PoksApp, PoksBucket
from poks.domain import PoksConfig as _PoksConfig
from poks.poks import Poks
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from pypeline.domain.pipeline import PipelineStep

from yanga.domain.config_utils import collect_configs_by_id, parse_config
from yanga.domain.execution_context import ExecutionContext

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class PoksConfig(_PoksConfig):
    @classmethod
    def from_file(cls, file_path: Path) -> Self:
        return cls.from_json_file(file_path)


@dataclass
class PoksInstallExecutionInfo(DataClassJSONMixin):
    install_dirs: list[Path] = field(default_factory=list)
    env_vars: dict[str, Any] = field(default_factory=dict)

    class Config(BaseConfig):
        omit_none = True

    @classmethod
    def from_json_file(cls, file_path: Path) -> "PoksInstallExecutionInfo":
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


class PoksInstall(PipelineStep[ExecutionContext]):
    def __init__(self, execution_context: ExecutionContext, group_name: str, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__(execution_context, group_name, config)
        self.logger = logger.bind()
        self.artifacts_locator = execution_context.create_artifacts_locator()
        self._collected_dependencies: Optional[PoksConfig] = None
        self.execution_info = PoksInstallExecutionInfo()
        self.execution_info_file = self.output_dir.joinpath("poks_install_exec_info.json")

    @property
    def output_dir(self) -> Path:
        if self.execution_context.variant:
            return self.execution_context.create_artifacts_locator().variant_build_dir
        else:
            return self.artifacts_locator.build_dir

    def get_name(self) -> str:
        return self.__class__.__name__

    @property
    def install_dirs(self) -> list[Path]:
        return self.execution_info.install_dirs

    @property
    def poks_config_file(self) -> Path:
        """Generated poks.json file path in variant-specific directory."""
        return self.artifacts_locator.variant_build_dir.joinpath("poks.json")

    @property
    def global_poks_config_file(self) -> Path:
        """Global poks.json file path (if exists)."""
        return self.project_root_dir.joinpath("poks.json")

    def _collect_dependencies(self) -> PoksConfig:
        """Collect Poks dependencies from global, platform, and variant configurations."""
        collected = PoksConfig()

        # Start with global poks.json if it exists
        if self.global_poks_config_file.exists():
            try:
                global_config = PoksConfig.from_json_file(self.global_poks_config_file)
                self._merge_buckets(collected, global_config.buckets)
                self._merge_apps(collected, global_config.apps)
            except Exception as e:
                self.logger.warning(f"Failed to parse global poks.json: {e}")

        # Add dependencies from configuration
        configs = collect_configs_by_id(self.execution_context, "poks")
        for cfg in configs:
            manifest = parse_config(cfg, PoksConfig, self.project_root_dir)
            self._merge_buckets(collected, manifest.buckets)
            self._merge_apps(collected, manifest.apps)

        return collected

    def _merge_buckets(self, target: PoksConfig, source_buckets: list[PoksBucket]) -> None:
        """Merge buckets, handling conflicts when same name has different URLs."""
        for bucket in source_buckets:
            existing = next((b for b in target.buckets if b.name == bucket.name), None)

            if existing is None:
                target.buckets.append(bucket)
            elif existing.url != bucket.url:
                self.logger.warning(
                    f"Bucket '{bucket.name}' defined multiple times with different URLs:\n  Existing: {existing.url}\n  New: {bucket.url}\n  Keeping existing definition."
                )

    def _merge_apps(self, target: PoksConfig, source_apps: list[PoksApp]) -> None:
        """Merge apps, avoiding duplicates."""
        for app in source_apps:
            if app not in target.apps:
                target.apps.append(app)

    def _generate_poks_config(self, config: PoksConfig) -> None:
        """Generate poks.json file from collected dependencies."""
        if not config.buckets and not config.apps:
            self.logger.info("No Poks dependencies found. Skipping poks.json generation.")
            return

        self.poks_config_file.parent.mkdir(parents=True, exist_ok=True)
        self.poks_config_file.write_text(config.to_json_string())

        self.logger.info(f"Generated poks.json with {len(config.buckets)} buckets and {len(config.apps)} apps")

    def run(self) -> int:
        self.logger.debug(f"Run {self.get_name()} step. Output dir: {self.output_dir}")

        try:
            # Collect dependencies from all sources
            self._collected_dependencies = self._collect_dependencies()

            # Generate the combined poks.json file
            self._generate_poks_config(self._collected_dependencies)

            # Only proceed with installation if we have dependencies
            if not self._collected_dependencies.apps:
                self.logger.info("No Poks dependencies to install.")
                return 0

            # Install using the poks library
            poks = Poks(root_dir=Path.home() / ".poks")
            result = poks.install(self._collected_dependencies)

            self.execution_info.install_dirs.extend(result.dirs)
            self.execution_info.env_vars.update(result.env)

            # Save execution info for dependency tracking
            self.execution_info.to_json_file(self.execution_info_file)

        except Exception as e:
            raise UserNotificationException(f"Failed to install poks dependencies: {e}") from e

        return 0

    def get_inputs(self) -> list[Path]:
        inputs = []

        # Add global poks.json if it exists
        if self.global_poks_config_file.exists():
            inputs.append(self.global_poks_config_file)

        # Add user config files (platform and variant configs are in there)
        inputs.extend(self.execution_context.user_config_files)

        return inputs

    def get_outputs(self) -> list[Path]:
        outputs = [self.poks_config_file, self.execution_info_file]

        # Add tracked install directories if available (after run() has been called)
        if self.execution_info.install_dirs:
            outputs.extend(self.execution_info.install_dirs)

        return outputs

    def update_execution_context(self) -> None:
        if self.execution_info_file.exists():
            execution_info = PoksInstallExecutionInfo.from_json_file(self.execution_info_file)
            # Make the list unique and keep the order
            unique_paths = list(dict.fromkeys(execution_info.install_dirs))
            # Update the install directories for the subsequent steps
            self.execution_context.add_install_dirs(unique_paths)
            if execution_info.env_vars:
                self.execution_context.add_env_vars(execution_info.env_vars)
