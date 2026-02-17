from pathlib import Path
from typing import Any, Optional

from pypeline.steps.west_install import WestInstall as PypelineWestInstallStep
from pypeline.steps.west_install import WestManifestFile, WestWorkspaceDir

from yanga.domain.config_utils import collect_configs_by_id, parse_config
from yanga.domain.execution_context import ExecutionContext


class WestInstall(PypelineWestInstallStep[ExecutionContext]):
    def __init__(self, execution_context: ExecutionContext, group_name: str, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__(execution_context, group_name, config)
        self.artifacts_locator = execution_context.create_artifacts_locator()

    def _collect_manifests(self) -> list[WestManifestFile]:
        manifests: list[WestManifestFile] = super()._collect_manifests()

        # Collect configs with id="west" from variant, platform, variant-platform
        configs = collect_configs_by_id(self.execution_context, "west")
        for cfg in configs:
            manifest = parse_config(cfg, WestManifestFile, self.project_root_dir)
            if not manifest.file and cfg.file:
                manifest.file = self.project_root_dir / cfg.file
            manifests.append(manifest)

        return manifests

    def _resolve_workspace_dir(self) -> Path:
        """Resolve workspace directory from data registry (priority) or config."""
        # Check data registry first (highest priority)
        registry_entries = self.execution_context.data_registry.find_data(WestWorkspaceDir)
        if registry_entries:
            return registry_entries[0].path

        # Check config
        if self.user_config.workspace_dir:
            return self.project_root_dir / self.user_config.workspace_dir

        # Fallback to build dir
        return self.execution_context.create_artifacts_locator().external_dependencies_dir

    @property
    def output_dir(self) -> Path:
        if self.execution_context.variant:
            return self.artifacts_locator.variant_build_dir
        else:
            return self.artifacts_locator.build_dir

    def get_name(self) -> str:
        return self.__class__.__name__
