from pathlib import Path
from typing import Dict, List, Optional, TypeAlias

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from pypeline.domain.pipeline import PipelineConfig

from yanga.domain.artifacts import ProjectArtifactsLocator

from .components import Component, ComponentType
from .config import ComponentConfig, PlatformConfig, VariantConfig, YangaUserConfig
from .config_slurper import YangaConfigSlurper

ComponentsConfigsPool: TypeAlias = Dict[str, ComponentConfig]


class YangaProjectSlurper:
    def __init__(self, project_dir: Path, configuration_file_name: Optional[str] = None, exclude_dirs: Optional[List[str]] = None) -> None:
        self.logger = logger.bind()
        self.project_dir = project_dir
        exclude = exclude_dirs if exclude_dirs else []
        # Merge the exclude directories with the hardcoded ones
        exclude = list({*exclude, ".git", ".github", ".vscode", "build", ".venv"})
        # TODO: Get rid of the exclude directories hardcoded list. Maybe use an ini file?
        self.user_configs: List[YangaUserConfig] = YangaConfigSlurper(project_dir=self.project_dir, exclude_dirs=exclude, configuration_file_name=configuration_file_name).slurp()
        self.components_configs_pool: ComponentsConfigsPool = self._collect_components_configs(self.user_configs)
        self.pipeline: Optional[PipelineConfig] = self._find_pipeline_config(self.user_configs)
        self.variants: List[VariantConfig] = self._collect_variants(self.user_configs)
        self.platforms: List[PlatformConfig] = self._collect_platforms(self.user_configs)

    @property
    def user_config_files(self) -> List[Path]:
        return [user_config.file for user_config in self.user_configs if user_config.file]

    def get_variant_config(self, variant_name: str) -> VariantConfig:
        variant = next((v for v in self.variants if v.name == variant_name), None)
        if not variant:
            raise UserNotificationException(f"Variant '{variant_name}' not found in the configuration.")

        return variant

    def get_variant_config_file(self, variant_name: str) -> Optional[Path]:
        variant = self.get_variant_config(variant_name)
        artifacts_locator = ProjectArtifactsLocator(self.project_dir, variant_name, None)
        return artifacts_locator.locate_artifact(variant.config_file, [variant.file]) if variant.config_file else None

    def get_variant_components(self, variant_name: str) -> List[Component]:
        return self._collect_variant_components(self.get_variant_config(variant_name))

    def get_platform(self, platform_name: Optional[str]) -> Optional[PlatformConfig]:
        if not platform_name:
            return None
        platform = next((p for p in self.platforms if p.name == platform_name), None)
        if not platform:
            raise UserNotificationException(f"Platform '{platform_name}' not found in the configuration.")
        return platform

    def _collect_variant_components(self, variant: VariantConfig) -> List[Component]:
        """
        "Collect all components for the given variant.
        Look for components in the component pool and add them to the list.
        """
        components = []
        if not variant.bom:
            raise UserNotificationException(f"Variant '{variant.name}' is empty (no 'bom' found).")
        for component_name in variant.bom.components:
            component_config = self.components_configs_pool.get(component_name, None)
            if not component_config:
                raise UserNotificationException(f"Component '{component_name}' not found in the configuration.")
            components.append(self._create_build_component(component_config))
        self._resolve_subcomponents(components, self.components_configs_pool)
        return components

    def _create_build_component(self, component_config: ComponentConfig) -> Component:
        # TODO: determine component type based on if it has sources, subcomponents
        component_type = ComponentType.COMPONENT
        component_path = component_config.file.parent if component_config.file else self.project_dir
        build_component = Component(
            component_config.name,
            component_type,
            component_path,
        )
        if component_config.sources:
            build_component.sources = component_config.sources
        if component_config.test_sources:
            build_component.test_sources = component_config.test_sources
        return build_component

    def _collect_components_configs(self, user_configs: List[YangaUserConfig]) -> ComponentsConfigsPool:
        components_config: ComponentsConfigsPool = {}
        for user_config in user_configs:
            for component_config in user_config.components:
                if components_config.get(component_config.name, None):
                    raise UserNotificationException(
                        f"Component '{component_config.name}' is defined in multiple configuration files."
                        f"See {components_config[component_config.name].file} and {user_config.file}"
                    )
                # TODO: shall the project slurper be responsible for updating the source file for the configuration?
                component_config.file = user_config.file
                components_config[component_config.name] = component_config
        return components_config

    def _resolve_subcomponents(
        self,
        components: List[Component],
        components_configs_pool: ComponentsConfigsPool,
    ) -> None:
        """Resolve subcomponents for each component."""
        components_pool = {c.name: c for c in components}
        for component in components:
            # It can not be that there is no configuration for the component,
            # otherwise it would not be in the list
            component_config = components_configs_pool.get(component.name)
            if component_config and component_config.components:
                for subcomponent_name in component_config.components:
                    subcomponent = components_pool.get(subcomponent_name, None)
                    if not subcomponent:
                        # TODO: throw the UserNotificationException and mention the file
                        # where the subcomponent was defined
                        raise UserNotificationException(f"Component '{subcomponent_name}' not found in the configuration.")
                    component.components.append(subcomponent)
                    subcomponent.is_subcomponent = True

    def _find_pipeline_config(self, user_configs: List[YangaUserConfig]) -> Optional[PipelineConfig]:
        return next(
            (user_config.pipeline for user_config in user_configs if user_config.pipeline),
            None,
        )

    def _collect_variants(self, user_configs: List[YangaUserConfig]) -> List[VariantConfig]:
        variants = []
        for user_config in user_configs:
            for variant in user_config.variants:
                variant.file = user_config.file
                variants.append(variant)
        return variants

    def _collect_platforms(self, user_configs: List[YangaUserConfig]) -> List[PlatformConfig]:
        platforms: List[PlatformConfig] = []
        for user_config in user_configs:
            for platform in user_config.platforms:
                # TODO: shall the project slurper be responsible for updating the source file for the configuration?
                platform.file = user_config.file
                platforms.append(platform)
        return platforms

    def print_project_info(self) -> None:
        self.logger.info("-" * 80)
        self.logger.info(f"Project directory: {self.project_dir}")
        self.logger.info(f"Parsed {len(self.user_configs)} configuration file(s).")
        self.logger.info(f"Found {len(self.components_configs_pool.values())} component(s).")
        self.logger.info(f"Found {len(self.variants)} variant(s):")
        for variant in self.variants:
            self.logger.info(f"  - {variant.name}")
        self.logger.info(f"Found {len(self.platforms)} platforms(s):")
        for platform in self.platforms:
            self.logger.info(f"  - {platform.name}")
        self.logger.info("Found pipeline config.")
        self.logger.info("-" * 80)
