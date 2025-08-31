from collections import OrderedDict
from pathlib import Path
from typing import Optional

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from pypeline.domain.pipeline import PipelineConfig, PipelineConfigIterator

from yanga.domain.artifacts import ProjectArtifactsLocator

from .components import Component
from .config import ComponentConfig, PlatformConfig, TestingConfiguration, VariantConfig, YangaUserConfig
from .config_slurper import YangaConfigSlurper


class ComponentFactory:
    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir

    def create(self, component_config: ComponentConfig) -> Component:
        component_path = self.project_dir / component_config.path if component_config.path else None
        if not component_path:
            component_path = component_config.file if component_config.file else None
            if not component_path:
                component_path = self.project_dir
        component = Component(
            component_config.name,
            component_path,
        )
        component.sources = component_config.sources
        component.docs_sources = component_config.docs_sources
        component.testing = component_config.testing if component_config.testing else TestingConfiguration()
        if component_config.test_sources:
            component.testing.sources.extend(component_config.test_sources)
        return component


class ComponentsConfigsPool:
    def __init__(self, component_factory: ComponentFactory) -> None:
        self._pool: dict[str, ComponentConfig] = {}
        self.component_factory = component_factory

    @classmethod
    def from_configs(cls, configs: list[ComponentConfig], component_factory: ComponentFactory) -> "ComponentsConfigsPool":
        pool = cls(component_factory)
        for config in configs:
            if config.name in pool._pool:
                raise UserNotificationException(f"Component '{config.name}' is already defined in the pool.")
            pool._pool[config.name] = config
        return pool

    def __getitem__(self, name: str) -> ComponentConfig:
        """Get a component configuration by name, raising KeyError if not found."""
        if name not in self._pool:
            raise KeyError(f"Component '{name}' not found in the configuration pool.")
        return self._pool[name]

    def __setitem__(self, name: str, config: ComponentConfig) -> None:
        """Set a component configuration by name, replacing any existing configuration."""
        self._pool[name] = config

    def values(self) -> list[ComponentConfig]:
        """Return a list of all component configurations in the pool."""
        return list(self._pool.values())

    def get(self, name: str, default: Optional[ComponentConfig] = None) -> Optional[ComponentConfig]:
        """Get a component configuration by name, returning None if not found."""
        return self._pool.get(name, default)

    def get_component_config(self, name: str) -> Optional[ComponentConfig]:
        return self.get(name)

    def get_component(self, name: str) -> Optional[Component]:
        component_config = self.get_component_config(name)
        return self.component_factory.create(component_config) if component_config else None


class IncludeDirectoriesResolver:
    """
    Resolve include directories for each component.

    Collects the private include directories and all public include directories
    from the required components. This is transitive, meaning that if a component requires
    other components, the public include directories of the required component are also added
    to the component's include directories. The resulted list is uniques and keeps the order
    of the include directories as they were defined in the configuration.
    """

    def __init__(self, components_configs_pool: ComponentsConfigsPool) -> None:
        self._components_configs_pool = components_configs_pool
        self._cache: dict[str, list[Path]] = {}

    def populate(self, components: list[Component]) -> None:
        for component in components:
            config = self._components_configs_pool.get_component_config(component.name)
            if config is None:
                continue
            visited: set[str] = set()
            public_includes = self._collect_public_includes(config, visited)
            includes = [component.path.joinpath(inc_dir) for inc_dir in config.private_include_directories] + public_includes
            # Remove duplicates but preserve order
            component.include_dirs = list(OrderedDict.fromkeys(includes))

    def _collect_public_includes(self, component_config: ComponentConfig, visited: set[str]) -> list[Path]:
        if component_config.name in self._cache:
            return self._cache[component_config.name]

        if component_config.name in visited:
            return []  # Prevent infinite recursion in case of circular dependencies

        visited.add(component_config.name)
        component = self._components_configs_pool.get_component(component_config.name)
        if not component:
            raise UserNotificationException(f"Component '{component_config.name}' not found in the configuration pool.")
        includes = [component.path.joinpath(inc_dir) for inc_dir in component_config.public_include_directories]

        for dep_name in component_config.required_components:
            dep_config = self._components_configs_pool.get(dep_name)
            if dep_config:
                includes.extend(self._collect_public_includes(dep_config, visited))

        # Remove duplicates but preserve order
        deduped_includes = list(OrderedDict.fromkeys(includes))
        self._cache[component_config.name] = deduped_includes
        return deduped_includes


class YangaProjectSlurper:
    def __init__(self, project_dir: Path, configuration_file_name: Optional[str] = None, exclude_dirs: Optional[list[str]] = None) -> None:
        self.logger = logger.bind()
        self.project_dir = project_dir
        self.component_factory = ComponentFactory(self.project_dir)
        exclude = exclude_dirs if exclude_dirs else []
        # Merge the exclude directories with the hardcoded ones
        exclude = list({*exclude, ".git", ".github", ".vscode", "build", ".venv"})
        # TODO: Get rid of the exclude directories hardcoded list. Maybe use an ini file?
        self.user_configs: list[YangaUserConfig] = YangaConfigSlurper(project_dir=self.project_dir, exclude_dirs=exclude, configuration_file_name=configuration_file_name).slurp()
        self.components_configs_pool: ComponentsConfigsPool = self._collect_components_configs(self.user_configs)
        self.pipeline: Optional[PipelineConfig] = self._find_pipeline_config(self.user_configs)
        self.variants: list[VariantConfig] = self._collect_variants(self.user_configs)
        self.platforms: list[PlatformConfig] = self._collect_platforms(self.user_configs)

    @property
    def user_config_files(self) -> list[Path]:
        return [user_config.file for user_config in self.user_configs if user_config.file]

    def get_variant_config(self, variant_name: str) -> VariantConfig:
        variant = next((v for v in self.variants if v.name == variant_name), None)
        if not variant:
            raise UserNotificationException(f"Variant '{variant_name}' not found in the configuration.")

        return variant

    def get_variant_config_file(self, variant_name: str) -> Optional[Path]:
        variant = self.get_variant_config(variant_name)
        artifacts_locator = ProjectArtifactsLocator(self.project_dir, variant_name, None, None)
        return artifacts_locator.locate_artifact(variant.features_selection_file, [variant.file]) if variant.features_selection_file else None

    def get_variant_components(self, variant_name: str) -> list[Component]:
        return self._collect_variant_components(self.get_variant_config(variant_name))

    def get_platform(self, platform_name: Optional[str]) -> Optional[PlatformConfig]:
        if not platform_name:
            return None
        platform = next((p for p in self.platforms if p.name == platform_name), None)
        if not platform:
            raise UserNotificationException(f"Platform '{platform_name}' not found in the configuration.")
        return platform

    def _collect_variant_components(self, variant: VariantConfig) -> list[Component]:
        """
        Collect all components for the given variant.

        Look for components in the component pool and add them to the list.
        """
        components = []
        if not variant.bom:
            raise UserNotificationException(f"Variant '{variant.name}' is empty (no 'bom' found).")
        for component_name in variant.bom.components:
            component_config = self.components_configs_pool.get(component_name, None)
            if not component_config:
                raise UserNotificationException(f"Component '{component_name}' not found in the configuration.")
            components.append(self.component_factory.create(component_config))
        self._resolve_subcomponents(components, self.components_configs_pool)
        IncludeDirectoriesResolver(self.components_configs_pool).populate(components)
        return components

    def _collect_components_configs(self, user_configs: list[YangaUserConfig]) -> ComponentsConfigsPool:
        components_config = ComponentsConfigsPool(self.component_factory)
        for user_config in user_configs:
            for component_config in user_config.components:
                if components_config.get(component_config.name, None):
                    raise UserNotificationException(
                        f"Component '{component_config.name}' is defined in multiple configuration files.See {components_config[component_config.name].file} and {user_config.file}"
                    )
                # TODO: shall the project slurper be responsible for updating the source file for the configuration?
                component_config.file = user_config.file
                components_config[component_config.name] = component_config
        return components_config

    def _resolve_subcomponents(
        self,
        components: list[Component],
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

    def _find_pipeline_config(self, user_configs: list[YangaUserConfig]) -> Optional[PipelineConfig]:
        return next(
            (user_config.pipeline for user_config in user_configs if user_config.pipeline),
            None,
        )

    def _collect_variants(self, user_configs: list[YangaUserConfig]) -> list[VariantConfig]:
        variants = []
        for user_config in user_configs:
            for variant in user_config.variants:
                variant.file = user_config.file
                variants.append(variant)
        return variants

    def _collect_platforms(self, user_configs: list[YangaUserConfig]) -> list[PlatformConfig]:
        platforms: list[PlatformConfig] = []
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
        if self.pipeline:
            self.logger.info("Found pipeline config:")
            for group, step_configs in PipelineConfigIterator(self.pipeline):
                if group:
                    logger.info(f"    Group: {group}")
                for step_config in step_configs:
                    logger.info(f"        {step_config.step}")
        self.logger.info("-" * 80)
