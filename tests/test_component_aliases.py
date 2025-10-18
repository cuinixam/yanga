from pathlib import Path

from tests.utils import assert_element_of_type, assert_elements_of_type
from yanga.domain.components import Component
from yanga.domain.config import ComponentConfig, IncludeDirectory, IncludeDirectoryScope, PlatformConfig, VariantConfig
from yanga.domain.project_slurper import ComponentFactory, ComponentsConfigsPool, YangaProjectSlurper


def test_component_alias_reproduction(tmp_path: Path) -> None:
    project_dir = tmp_path
    component_factory = ComponentFactory(project_dir)
    components_pool = ComponentsConfigsPool(component_factory)

    arduino_core = ComponentConfig(
        name="arduino_core",
        sources=["wiring.c"],
        required_components=["pins"],
        include_directories=[IncludeDirectory(path="core", scope=IncludeDirectoryScope.PUBLIC)],
    )
    uno_pins_component = ComponentConfig(
        name="uno_pins",
        alias="pins",
        sources=[],
        include_directories=[IncludeDirectory(path="uno_pins", scope=IncludeDirectoryScope.PUBLIC)],
    )
    nano_pins_component = ComponentConfig(
        name="nano_pins",
        alias="pins",
        sources=[],
        include_directories=[IncludeDirectory(path="pins_pins", scope=IncludeDirectoryScope.PUBLIC)],
    )

    components_pool[arduino_core.name] = arduino_core
    components_pool[uno_pins_component.name] = uno_pins_component
    components_pool[nano_pins_component.name] = nano_pins_component

    variant_config = VariantConfig(name="arduino_demo", components=[arduino_core.name])
    platform_config = PlatformConfig(name="arduino_platform", components=["uno_pins"])

    project_slurper = YangaProjectSlurper(project_dir=project_dir, create_yanga_build_dir=False)
    project_slurper.components_configs_pool = components_pool
    project_slurper.platforms = [platform_config]

    variant_components = project_slurper._collect_variant_components(variant_config, platform_config.name)
    components = assert_elements_of_type(variant_components, Component, 2)
    assert {c.name for c in components} == {"arduino_core", "uno_pins"}
    core_component = assert_element_of_type(components, Component, lambda c: c.name == "arduino_core")
    # Expect pins include to be resolved via alias
    assert any("uno_pins" in str(p) for p in core_component.include_dirs), "Alias resolution missing: expected uno_pins include dir via alias"
