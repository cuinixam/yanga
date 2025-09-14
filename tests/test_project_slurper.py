from pathlib import Path

from yanga.domain.config import ComponentConfig, VariantConfig, VariantPlatformsConfig
from yanga.domain.project_slurper import ComponentFactory, ComponentsConfigsPool, YangaProjectSlurper


def test_collect_variant_components_with_platform_specific(tmp_path: Path) -> None:
    project_dir = tmp_path

    # Create component configs
    component_factory = ComponentFactory(project_dir)
    components_pool = ComponentsConfigsPool(component_factory)

    # Add base components
    base_component = ComponentConfig(name="base_component", sources=["base.c"])
    platform_component = ComponentConfig(name="platform_component", sources=["platform.c"])

    components_pool["base_component"] = base_component
    components_pool["platform_component"] = platform_component

    # Create variant with platform-specific components
    variant = VariantConfig(
        name="test_variant",
        components=["base_component"],
        platforms={"test_platform": VariantPlatformsConfig(components=["platform_component"], config={"PLATFORM_CONFIG": "platform_value"})},
    )

    # Create a project slurper instance
    project_slurper = YangaProjectSlurper(project_dir=project_dir, create_yanga_build_dir=False)
    project_slurper.components_configs_pool = components_pool

    # Test with platform
    components_with_platform = project_slurper._collect_variant_components(variant, "test_platform")
    component_names_with_platform = [c.name for c in components_with_platform]

    # Should contain both base and platform-specific components
    assert "base_component" in component_names_with_platform
    assert "platform_component" in component_names_with_platform
    assert len(component_names_with_platform) == 2

    # Test without platform
    components_without_platform = project_slurper._collect_variant_components(variant, None)
    component_names_without_platform = [c.name for c in components_without_platform]

    # Should contain only base components
    assert "base_component" in component_names_without_platform
    assert "platform_component" not in component_names_without_platform
    assert len(component_names_without_platform) == 1

    # Test with different platform
    components_different_platform = project_slurper._collect_variant_components(variant, "other_platform")
    component_names_different_platform = [c.name for c in components_different_platform]

    # Should contain only base components
    assert "base_component" in component_names_different_platform
    assert "platform_component" not in component_names_different_platform
    assert len(component_names_different_platform) == 1


def test_collect_variant_components_no_platform_config(tmp_path: Path) -> None:
    project_dir = tmp_path

    # Create component configs
    component_factory = ComponentFactory(project_dir)
    components_pool = ComponentsConfigsPool(component_factory)

    # Add base component
    base_component = ComponentConfig(name="base_component", sources=["base.c"])
    components_pool["base_component"] = base_component

    # Create variant without platform-specific config
    variant = VariantConfig(name="test_variant", components=["base_component"])

    # Create a project slurper instance
    project_slurper = YangaProjectSlurper(project_dir=project_dir, create_yanga_build_dir=False)
    project_slurper.components_configs_pool = components_pool

    # Test with platform
    components = project_slurper._collect_variant_components(variant, "test_platform")
    component_names = [c.name for c in components]

    # Should contain only base components
    assert "base_component" in component_names
    assert len(component_names) == 1
