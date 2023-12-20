from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, TypeAlias

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger

from yanga.ybuild.components import BuildComponent, BuildComponentType
from yanga.ybuild.pipeline import BuildStage, PipelineLoader

from .config import ComponentConfig, PipelineConfig, VariantConfig, YangaUserConfig
from .config_slurper import YangaConfigSlurper


@dataclass
class ComponentConfigWithLocation:
    config: ComponentConfig
    #: Path to the file where the component is defined
    file: Optional[Path] = None


ComponentsConfigsPool: TypeAlias = Dict[str, ComponentConfigWithLocation]


class YangaProjectSlurper:
    def __init__(self, project_dir: Path) -> None:
        self.logger = logger.bind()
        self.project_dir = project_dir
        self.user_configs: List[YangaUserConfig] = YangaConfigSlurper(
            self.project_dir, [".git", ".github", ".vscode", "build", ".venv"]
        ).slurp()
        self.components_configs_pool: ComponentsConfigsPool = self._collect_components_configs(self.user_configs)
        self.stages: List[BuildStage] = self._collect_stages(self.user_configs, self.project_dir)
        self.variants: List[VariantConfig] = self._collect_variants(self.user_configs)
        self.print_project_info()

    @property
    def user_config_files(self) -> List[Path]:
        return [user_config.file for user_config in self.user_configs if user_config.file]

    def print_project_info(self) -> None:
        self.logger.info("-" * 80)
        self.logger.info(f"Project directory: {self.project_dir}")
        self.logger.info(f"Parsed {len(self.user_configs)} configuration file(s).")
        self.logger.info(f"Found {len(self.components_configs_pool.values())} component(s).")
        self.logger.info(f"Found {len(self.stages)} stage(s).")
        self.logger.info(f"Found {len(self.variants)} variant(s).")
        self.logger.info("-" * 80)

    def get_variant_config(self, variant_name: str) -> VariantConfig:
        variant = next((v for v in self.variants if v.name == variant_name), None)
        if not variant:
            raise UserNotificationException(f"Variant '{variant_name}' not found in the configuration.")

        return variant

    def get_variant_config_file(self, variant_name: str) -> Optional[Path]:
        variant = self.get_variant_config(variant_name)
        return self.project_dir.joinpath(variant.config_file) if variant.config_file else None

    def get_variant_components(self, variant_name: str) -> List[BuildComponent]:
        return self._collect_variant_components(self.get_variant_config(variant_name))

    def _collect_variant_components(self, variant: VariantConfig) -> List[BuildComponent]:
        """ "Collect all components for the given variant.
        Look for components in the component pool and add them to the list."""
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

    def _create_build_component(self, component_config: ComponentConfigWithLocation) -> BuildComponent:
        # TODO: determine component type based on if it has sources, subcomponents
        component_type = BuildComponentType.COMPONENT
        component_path = component_config.file.parent if component_config.file else self.project_dir
        build_component = BuildComponent(
            component_config.config.name,
            component_type,
            component_path,
        )
        if component_config.config.sources:
            build_component.sources = component_config.config.sources
        if component_config.config.test_sources:
            build_component.test_sources = component_config.config.test_sources
        return build_component

    def _collect_components_configs(self, user_configs: List[YangaUserConfig]) -> ComponentsConfigsPool:
        components_config: ComponentsConfigsPool = {}
        for user_config in user_configs:
            for component_config in user_config.components:
                if components_config.get(component_config.name, None):
                    # TODO: throw the UserNotificationException and mention the two files
                    #  where the components are defined
                    raise UserNotificationException(
                        f"Component '{component_config.name}' is defined in multiple configuration files."
                        f"See {components_config[component_config.name].file} and {user_config.file}"
                    )
                components_config[component_config.name] = ComponentConfigWithLocation(
                    component_config, user_config.file
                )
        return components_config

    def _resolve_subcomponents(
        self,
        components: List[BuildComponent],
        components_configs_pool: ComponentsConfigsPool,
    ) -> None:
        """Resolve subcomponents for each component."""
        components_pool = {c.name: c for c in components}
        for component in components:
            # It can not be that there is no configuration for the component,
            # otherwise it would not be in the list
            component_config = components_configs_pool.get(component.name)
            if component_config and component_config.config.components:
                for subcomponent_name in component_config.config.components:
                    subcomponent = components_pool.get(subcomponent_name, None)
                    if not subcomponent:
                        # TODO: throw the UserNotificationException and mention the file
                        # where the subcomponent was defined
                        raise UserNotificationException(
                            f"Component '{subcomponent_name}' not found in the configuration."
                        )
                    component.components.append(subcomponent)
                    subcomponent.is_subcomponent = True

    def _collect_stages(self, user_configs: List[YangaUserConfig], project_root_dir: Path) -> List[BuildStage]:
        """Find the pipeline configuration and collect all stages.
        In case there are multiple pipeline configurations, throw an exception.
        """
        pipeline_config = self._find_pipeline_config(user_configs)
        return PipelineLoader(pipeline_config, project_root_dir).load_stages()

    def _find_pipeline_config(self, user_configs: List[YangaUserConfig]) -> PipelineConfig:
        configs = [user_config.pipeline for user_config in user_configs if user_config.pipeline]
        if not configs:
            raise UserNotificationException("No pipeline configuration found.")
        elif len(configs) > 1:
            raise UserNotificationException(
                "Multiple pipeline configurations found. " "Only one pipeline configuration is allowed."
            )
        return configs[0]

    def _collect_variants(self, user_configs: List[YangaUserConfig]) -> List[VariantConfig]:
        variants = []
        for user_config in user_configs:
            variants.extend(user_config.variants)
        return variants
