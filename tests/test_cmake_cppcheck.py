from pathlib import Path

import pytest

from tests.utils import assert_element_of_type, assert_elements_of_type, find_elements_of_type
from yanga.cmake.cmake_backend import (
    CMakeCustomCommand,
    CMakeCustomTarget,
)
from yanga.cmake.cppcheck import CppCheckCMakeGenerator
from yanga.domain.execution_context import ExecutionContext


@pytest.fixture
def create_executable_generator(execution_context: ExecutionContext, output_dir: Path) -> CppCheckCMakeGenerator:
    return CppCheckCMakeGenerator(execution_context, output_dir)


def test_generate(create_executable_generator: CppCheckCMakeGenerator) -> None:
    elements = create_executable_generator.generate()
    assert elements

    targets = assert_elements_of_type(elements, CMakeCustomTarget, 3)
    assert [target.name for target in targets] == [
        "lint",
        "CompA_lint",
        "CompBNotTestable_lint",
    ]


def test_create_variant_cmake_elements(
    create_executable_generator: CppCheckCMakeGenerator,
) -> None:
    elements = create_executable_generator.create_variant_cmake_elements()

    custom_target = assert_element_of_type(elements, CMakeCustomTarget)
    assert custom_target.name == "lint"


def test_create_components_cmake_elements(
    create_executable_generator: CppCheckCMakeGenerator,
) -> None:
    elements = create_executable_generator.create_components_cmake_elements()
    assert [target.name for target in find_elements_of_type(elements, CMakeCustomTarget)] == [
        "CompA_lint",
        "CompBNotTestable_lint",
    ]
    comp_cmd = assert_element_of_type(elements, CMakeCustomCommand, lambda cmd: "CompA" in cmd.description)
    assert [cmd.command for cmd in comp_cmd.commands] == ["yanga_cmd", "cppcheck", "yanga_cmd"]
