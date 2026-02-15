from pathlib import Path
from typing import Any, Optional

from poks.domain import PoksConfig
from pypeline.steps.poks_install import PoksInstall as BasePoksInstall

from yanga.domain.config_utils import collect_configs_by_id, parse_config
from yanga.domain.execution_context import ExecutionContext


class PoksInstall(BasePoksInstall[ExecutionContext]):
    def __init__(self, execution_context: ExecutionContext, group_name: str, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__(execution_context, group_name, config)
        self.artifacts_locator = execution_context.create_artifacts_locator()

    def _collect_dependencies(self) -> PoksConfig:
        collected = super()._collect_dependencies()

        # Collect configs with id="poks" from variant, platform, variant-platform
        configs = collect_configs_by_id(self.execution_context, "poks")
        for cfg in configs:
            manifest = parse_config(cfg, PoksConfig, self.project_root_dir)
            self._merge_buckets(collected, manifest.buckets)
            self._merge_apps(collected, manifest.apps)

        return collected

    @property
    def output_dir(self) -> Path:
        return self.artifacts_locator.variant_build_dir

    def get_name(self) -> str:
        return self.__class__.__name__
