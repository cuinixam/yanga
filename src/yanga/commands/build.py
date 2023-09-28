from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, TypeAlias

from mashumaro import DataClassDictMixin

from yanga.core.cmd_line import Command, register_arguments_for_config_dataclass
from yanga.core.exceptions import UserNotificationException
from yanga.core.logging import logger, time_it
from yanga.ybuild.components import BuildComponent, BuildComponentType
from yanga.ybuild.config import ComponentConfig, PipelineConfig, YangaUserConfig
from yanga.ybuild.config_slurper import YangaConfigSlurper
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.pipeline import BuildStage, PipelineLoader, StageRunner

ComponentsConfigsPool: TypeAlias = Dict[str, ComponentConfig]


@dataclass
class BuildCommandConfig(DataClassDictMixin):
    variant_name: str = field(metadata={"help": "SPL variant name."})
    project_dir: Path = field(
        default=Path(".").absolute(),
        metadata={
            "help": "Project root directory. "
            "Defaults to the current directory if not specified."
        },
    )

    @classmethod
    def from_namespace(cls, namespace: Namespace) -> "BuildCommandConfig":
        return cls.from_dict(vars(namespace))


class BuildCommand(Command):
    def __init__(self) -> None:
        super().__init__("build", "Build a yanga project")
        self.logger = logger.bind()

    @time_it("Build")
    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        config = BuildCommandConfig.from_namespace(args)
        user_configs = YangaConfigSlurper(config.project_dir).slurp()
        components = self._collect_build_components(user_configs)
        stages = self._collect_stages(user_configs, config.project_dir)
        build_environment = BuildEnvironment(
            config.variant_name, config.project_dir, components
        )
        for stage in stages:
            StageRunner(build_environment, stage).run()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, BuildCommandConfig)

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
        self._resolve_subcomponents(components, components_configs_pool)
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
