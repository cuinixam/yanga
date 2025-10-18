from pathlib import Path

import pytest
from py_app_dev.core.exceptions import UserNotificationException

from yanga.domain.components import Component
from yanga.domain.config import ComponentConfig, IncludeDirectory, IncludeDirectoryScope
from yanga.domain.project_slurper import ComponentFactory, ComponentsConfigsPool, IncludeDirectoriesResolver


def get_components(pool: ComponentsConfigsPool, *names: str) -> list[Component]:
    """Helper function to get multiple components from pool and assert they exist."""
    components = []
    for name in names:
        component = pool.get_component(name)
        assert component is not None, f"Component '{name}' should exist in pool"
        components.append(component)
    return components


@pytest.fixture
def components_configs_pool() -> ComponentsConfigsPool:
    return ComponentsConfigsPool.from_configs(
        [
            ComponentConfig(
                name="compA",
                required_components=["compB"],
                include_directories=[IncludeDirectory("inc", IncludeDirectoryScope.PUBLIC), IncludeDirectory("src", IncludeDirectoryScope.PRIVATE)],
                path=Path("a"),
            ),
            ComponentConfig(
                name="compB",
                required_components=["compC"],
                include_directories=[IncludeDirectory("inc", IncludeDirectoryScope.PUBLIC)],
                path=Path("b"),
            ),
            ComponentConfig(
                name="compC",
                include_directories=[IncludeDirectory("inc", IncludeDirectoryScope.PUBLIC), IncludeDirectory("src", IncludeDirectoryScope.PRIVATE)],
                path=Path("c"),
            ),
            ComponentConfig(
                name="compD",
                required_components=["compB", "compC"],
                include_directories=[IncludeDirectory("inc", IncludeDirectoryScope.PUBLIC)],
                path=Path("d"),
            ),
            ComponentConfig(name="compCircularA", required_components=["compCircularB"]),
            ComponentConfig(name="compCircularB", required_components=["compCircularA"]),
        ],
        ComponentFactory(Path("prj/root")),
    )


def test_populate_component_with_dependencies(components_configs_pool: ComponentsConfigsPool) -> None:
    resolver = IncludeDirectoriesResolver(components_configs_pool)
    comp_a, comp_b, comp_c = get_components(components_configs_pool, "compA", "compB", "compC")
    resolver.populate([comp_a, comp_b, comp_c])
    assert comp_a.include_dirs == [
        Path("prj/root/a/src"),
        Path("prj/root/a/inc"),
        Path("prj/root/b/inc"),
        Path("prj/root/c/inc"),
    ]


def test_populate_component_with_no_dependencies(components_configs_pool: ComponentsConfigsPool) -> None:
    resolver = IncludeDirectoriesResolver(components_configs_pool)
    comp_c = get_components(components_configs_pool, "compC")[0]
    resolver.populate([comp_c])
    assert comp_c.include_dirs == [Path("prj/root/c/src"), Path("prj/root/c/inc")]


def test_populate_multiple_components(components_configs_pool: ComponentsConfigsPool) -> None:
    resolver = IncludeDirectoriesResolver(components_configs_pool)
    comp_a, comp_b, comp_c, comp_d = get_components(components_configs_pool, "compA", "compB", "compC", "compD")
    resolver.populate([comp_a, comp_b, comp_c, comp_d])
    assert comp_a.include_dirs == [Path("prj/root/a/src"), Path("prj/root/a/inc"), Path("prj/root/b/inc"), Path("prj/root/c/inc")]
    assert comp_d.include_dirs == [Path("prj/root/d/inc"), Path("prj/root/b/inc"), Path("prj/root/c/inc")]


def test_populate_with_circular_dependency(components_configs_pool: ComponentsConfigsPool) -> None:
    resolver = IncludeDirectoriesResolver(components_configs_pool)
    comp_circular_a, comp_circular_b = get_components(components_configs_pool, "compCircularA", "compCircularB")
    resolver.populate([comp_circular_a, comp_circular_b])
    assert not comp_circular_a.include_dirs


def test_populate_with_component_not_in_pool() -> None:
    empty_pool = ComponentsConfigsPool.from_configs([], ComponentFactory(Path("prj/root")))
    resolver = IncludeDirectoriesResolver(empty_pool)
    component_x = Component(name="compX", path=Path("x"))
    resolver.populate([component_x])
    assert not component_x.include_dirs


def test_duplicate_includes_are_removed(components_configs_pool: ComponentsConfigsPool) -> None:
    comp_a_config = components_configs_pool.get_component_config("compA")
    assert comp_a_config
    # compA requires compB. compD also requires compB.
    # By adding compD to compA's requirements, we will have a diamond dependency
    # and includes from compB and compC will be collected multiple times.
    comp_a_config.required_components.append("compD")
    resolver = IncludeDirectoriesResolver(components_configs_pool)
    comp_a, comp_b, comp_c, comp_d = get_components(components_configs_pool, "compA", "compB", "compC", "compD")
    resolver.populate([comp_a, comp_b, comp_c, comp_d])
    assert comp_a.include_dirs == [
        Path("prj/root/a/src"),
        Path("prj/root/a/inc"),
        Path("prj/root/b/inc"),
        Path("prj/root/c/inc"),
        Path("prj/root/d/inc"),
    ]


def test_missing_required_component_silently_ignored() -> None:
    component_factory = ComponentFactory(Path("prj/root"))
    components_pool = ComponentsConfigsPool.from_configs(
        [
            ComponentConfig(
                name="arduino_core",
                required_components=["pins"],  # "pins" component does not exist
                include_directories=[IncludeDirectory("core", IncludeDirectoryScope.PUBLIC)],
                path=Path("core"),
            ),
            ComponentConfig(
                name="uno_pins",
                alias="pins",
                include_directories=[IncludeDirectory("uno_pins", IncludeDirectoryScope.PUBLIC)],
                path=Path("uno_pins"),
            ),
        ],
        component_factory,
    )

    resolver = IncludeDirectoriesResolver(components_pool)
    arduino_core, uno_pins = get_components(components_pool, "arduino_core", "uno_pins")

    # This should raise an exception for missing "pins" component
    with pytest.raises(UserNotificationException, match="pins"):
        resolver.populate([arduino_core])

    # This should pass without exceptions because the uno_pins resolves by the alias "pins"
    resolver.populate([arduino_core, uno_pins])
