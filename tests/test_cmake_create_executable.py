from pathlib import Path

import pytest
from yanga_core.domain.artifact import Artifact
from yanga_core.domain.components import Component
from yanga_core.domain.execution_context import ExecutionContext

from tests.utils import assert_element_of_type, assert_elements_of_type, find_elements_of_type
from yanga.cmake.cmake_backend import (
    CMakeAddExecutable,
    CMakeAddLibrary,
    CMakeCustomTarget,
    CMakeElement,
    CMakeTargetLinkLibraries,
    LinkLibrary,
    LinkScope,
)
from yanga.cmake.create_executable import CreateExecutableCMakeGenerator


@pytest.fixture
def create_executable_generator(execution_context: ExecutionContext, output_dir: Path) -> CreateExecutableCMakeGenerator:
    return CreateExecutableCMakeGenerator(execution_context, output_dir)


def test_generate(create_executable_generator: CreateExecutableCMakeGenerator) -> None:
    elements = create_executable_generator.generate()
    assert elements

    executable = assert_element_of_type(elements, CMakeAddExecutable)
    assert executable.name == "${PROJECT_NAME}"
    targets = assert_elements_of_type(elements, CMakeCustomTarget, 6)
    assert [target.name for target in targets] == [
        "build",
        "compile",
        "CompA_compile",
        "CompA_build",
        "CompBNotTestable_compile",
        "CompBNotTestable_build",
    ]


def test_create_variant_cmake_elements(
    create_executable_generator: CreateExecutableCMakeGenerator,
) -> None:
    elements = create_executable_generator.create_variant_cmake_elements()

    executable = assert_element_of_type(elements, CMakeAddExecutable)
    assert executable.name == "${PROJECT_NAME}"
    custom_targets = assert_elements_of_type(elements, CMakeCustomTarget, 2)
    assert {target.name for target in custom_targets} == {"build", "compile"}


def test_get_include_directories(
    create_executable_generator: CreateExecutableCMakeGenerator,
) -> None:
    create_executable_generator.execution_context.data_registry.insert(
        Artifact(path=Path("/another/include/dir"), provider="test", labels=["include", "public"]),
        "test",
    )
    assert len(create_executable_generator.get_include_directories().paths) == 3  # one per component source dir (compA, compB) plus one from the registry


def test_create_components_cmake_elements(
    create_executable_generator: CreateExecutableCMakeGenerator,
) -> None:
    elements = create_executable_generator.create_components_cmake_elements()

    object_libraries = find_elements_of_type(elements, CMakeAddLibrary)
    assert len(object_libraries) == 2  # One for each component
    compile_targets = find_elements_of_type(elements, CMakeCustomTarget)
    assert [target.name for target in compile_targets] == [
        "CompA_compile",
        "CompA_build",
        "CompBNotTestable_compile",
        "CompBNotTestable_build",
    ]


class ExternalExecutableGenerator(CreateExecutableCMakeGenerator):
    """A platform whose build system owns the executable adapts the generator through its hooks."""

    component_link_libraries = (LinkLibrary("flags"),)

    @property
    def executable_target_name(self) -> str:
        return "app"

    def create_executable_elements(self, component_library_targets: list[str]) -> list[CMakeElement]:
        return [CMakeTargetLinkLibraries("app", component_library_targets, scope=LinkScope.PRIVATE)]


def test_hooks_let_a_platform_link_into_its_own_executable(execution_context: ExecutionContext, output_dir: Path) -> None:
    elements = ExternalExecutableGenerator(execution_context, output_dir).generate()

    assert not find_elements_of_type(elements, CMakeAddExecutable)
    link_lines = [element.to_string() for element in find_elements_of_type(elements, CMakeTargetLinkLibraries)]
    assert link_lines[0] == "target_link_libraries(app PRIVATE CompA_lib CompBNotTestable_lib)"
    assert "target_link_libraries(CompA_lib PUBLIC flags)" in link_lines
    build_target = next(target for target in find_elements_of_type(elements, CMakeCustomTarget) if target.name == "build")
    assert build_target.depends == ["app"]


def test_component_link_libraries_skip_header_only_components(execution_context: ExecutionContext, output_dir: Path) -> None:
    header_only = Component(name="types", path=output_dir, sources=[])
    elements = ExternalExecutableGenerator(execution_context, output_dir).create_component_elements(header_only)
    assert not find_elements_of_type(elements, CMakeTargetLinkLibraries)
