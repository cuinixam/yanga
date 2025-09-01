from pathlib import Path

import pytest

from tests.utils import assert_element_of_type, assert_elements_of_type, find_elements_of_type
from yanga.cmake.cmake_backend import (
    CMakeCustomTarget,
)
from yanga.cmake.reports import ReportCMakeGenerator
from yanga.domain.execution_context import ExecutionContext


@pytest.fixture
def create_executable_generator(execution_context: ExecutionContext, output_dir: Path) -> ReportCMakeGenerator:
    return ReportCMakeGenerator(execution_context, output_dir)


def test_generate(create_executable_generator: ReportCMakeGenerator) -> None:
    elements = create_executable_generator.generate()
    assert elements

    targets = assert_elements_of_type(elements, CMakeCustomTarget, 5)
    assert [target.name for target in targets] == [
        "report",
        "CompA_docs",
        "CompA_report",
        "CompBNotTestable_docs",
        "CompBNotTestable_report",
    ]


def test_create_variant_cmake_elements(
    create_executable_generator: ReportCMakeGenerator,
) -> None:
    elements = create_executable_generator.create_variant_cmake_elements()

    custom_target = assert_element_of_type(elements, CMakeCustomTarget)
    assert custom_target.name == "report"


def test_create_components_cmake_elements(
    create_executable_generator: ReportCMakeGenerator,
) -> None:
    elements = create_executable_generator.create_components_cmake_elements()
    assert [target.name for target in find_elements_of_type(elements, CMakeCustomTarget)] == [
        "CompA_docs",
        "CompA_report",
        "CompBNotTestable_docs",
        "CompBNotTestable_report",
    ]
    comp_cmd = assert_element_of_type(elements, CMakeCustomTarget, lambda target: target.name == "CompA_docs")
    assert [cmd.command for cmd in comp_cmd.commands] == ["clanguru", "clanguru"]
    comp_cmd = assert_element_of_type(elements, CMakeCustomTarget, lambda target: target.name == "CompA_report")
    assert [cmd.command for cmd in comp_cmd.commands] == ["${CMAKE_COMMAND}", "yanga_cmd", "${CMAKE_COMMAND}"]
