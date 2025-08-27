from pathlib import Path

import pytest

from tests.utils import assert_element_of_type, assert_elements_of_type, find_elements_of_type
from yanga.cmake.cmake_backend import (
    CMakeAddExecutable,
    CMakeCustomTarget,
    CMakeObjectLibrary,
)
from yanga.cmake.create_executable import CreateExecutableCMakeGenerator
from yanga.domain.execution_context import ExecutionContext


@pytest.fixture
def create_executable_generator(execution_context: ExecutionContext, output_dir: Path) -> CreateExecutableCMakeGenerator:
    return CreateExecutableCMakeGenerator(execution_context, output_dir)


def test_generate(create_executable_generator: CreateExecutableCMakeGenerator) -> None:
    elements = create_executable_generator.generate()
    assert elements

    executable = assert_element_of_type(elements, CMakeAddExecutable)
    assert executable.name == "${PROJECT_NAME}"
    targets = assert_elements_of_type(elements, CMakeCustomTarget, 5)
    assert [target.name for target in targets] == [
        "build",
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
    custom_target = assert_element_of_type(elements, CMakeCustomTarget)
    assert custom_target.name == "build"


def test_get_include_directories(
    create_executable_generator: CreateExecutableCMakeGenerator,
) -> None:
    # Add an additional global include directory
    create_executable_generator.execution_context.include_directories.append(Path("/another/include/dir"))
    assert len(create_executable_generator.get_include_directories().paths) == 3  # Two from components, one global


def test_create_components_cmake_elements(
    create_executable_generator: CreateExecutableCMakeGenerator,
) -> None:
    elements = create_executable_generator.create_components_cmake_elements()

    object_libraries = find_elements_of_type(elements, CMakeObjectLibrary)
    assert len(object_libraries) == 2  # One for each component
    compile_targets = find_elements_of_type(elements, CMakeCustomTarget)
    assert [target.name for target in compile_targets] == [
        "CompA_compile",
        "CompA_build",
        "CompBNotTestable_compile",
        "CompBNotTestable_build",
    ]
