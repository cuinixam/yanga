from pathlib import Path
from typing import Dict, List, TypeAlias

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger

from yanga.ybuild.components import BuildComponent, BuildComponentType
from yanga.ybuild.pipeline import BuildStage, PipelineLoader

from .config import ComponentConfig, PipelineConfig, VariantConfig, YangaUserConfig
from .config_slurper import YangaConfigSlurper

ComponentsConfigsPool: TypeAlias = Dict[str, ComponentConfig]


class YangaProject:
    def __init__(self, project_dir: Path) -> None:
        self.logger = logger.bind()
        self.project_dir = project_dir
        self.user_configs: List[YangaUserConfig] = YangaConfigSlurper(
            self.project_dir
        ).slurp()
        self.components: List[BuildComponent] = self._collect_build_components(
            self.user_configs
        )
        self.stages: List[BuildStage] = self._collect_stages(
            self.user_configs, self.project_dir
        )
        self.variants: List[VariantConfig] = self._collect_variants(self.user_configs)
        self.print_project_info()

    def print_project_info(self) -> None:
        self.logger.info("-" * 80)
        self.logger.info(f"Project directory: {self.project_dir}")
        self.logger.info(f"Parsed {len(self.user_configs)} configuration files.")
        self.logger.info(f"Found {len(self.components)} components.")
        self.logger.info(f"Found {len(self.stages)} stages.")
        self.logger.info(f"Found {len(self.variants)} variants.")
        self.logger.info("-" * 80)

    def _collect_build_components(
        self, user_configs: List[YangaUserConfig]
    ) -> List[BuildComponent]:
        """Create a set with all components found in the configuration files.
        In case the component already exists, throw an exception.
        """
        components_configs_pool = self._collect_components_configs(user_configs)
        components = []
        for component_config in components_configs_pool.values():
            # TODO: determine component type based on if it has sources, subcomponents
            component_type = BuildComponentType.COMPONENT
            components.append(
                BuildComponent(
                    component_config.name,
                    component_type,
                )
            )
        # After all components are created, resolve subcomponents
        # TODO: this shall not be done here. We only need to resolve components and subcomponents
        #       for the current variant. The rest of the components shall be ignored.
        # self._resolve_subcomponents(components, components_configs_pool)
        return components

    def _collect_components_configs(
        self, user_configs: List[YangaUserConfig]
    ) -> ComponentsConfigsPool:
        components_config: ComponentsConfigsPool = {}
        for user_config in user_configs:
            for component_config in user_config.components:
                if components_config.get(component_config.name, None):
                    # TODO: throw the UserNotificationException and mention the two files
                    #  where the components are defined
                    raise ValueError(
                        f"Component '{component_config}' already exists in the configuration."
                    )
                components_config[component_config.name] = component_config
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
            if component_config and component_config.components:
                for subcomponent_name in component_config.components:
                    subcomponent = components_pool.get(subcomponent_name, None)
                    if not subcomponent:
                        # TODO: throw the UserNotificationException and mention the file
                        # where the subcomponent was defined
                        raise UserNotificationException(
                            f"Component '{subcomponent_name}' not found in the configuration."
                        )
                    component.components.append(subcomponent)
                    subcomponent.is_subcomponent = True

    def _collect_stages(
        self, user_configs: List[YangaUserConfig], project_root_dir: Path
    ) -> List[BuildStage]:
        """Find the pipeline configuration and collect all stages.
        In case there are multiple pipeline configurations, throw an exception.
        """
        pipeline_config = self._find_pipeline_config(user_configs)
        return PipelineLoader(pipeline_config, project_root_dir).load_stages()

    def _find_pipeline_config(
        self, user_configs: List[YangaUserConfig]
    ) -> PipelineConfig:
        configs = [
            user_config.pipeline for user_config in user_configs if user_config.pipeline
        ]
        if not configs:
            raise UserNotificationException("No pipeline configuration found.")
        elif len(configs) > 1:
            raise UserNotificationException(
                "Multiple pipeline configurations found. "
                "Only one pipeline configuration is allowed."
            )
        return configs[0]

    def _collect_variants(
        self, user_configs: List[YangaUserConfig]
    ) -> List[VariantConfig]:
        variants = []
        for user_config in user_configs:
            variants.extend(user_config.variants)
        return variants
