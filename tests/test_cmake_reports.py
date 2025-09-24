from pathlib import Path

import pytest

from tests.utils import assert_element_of_type, assert_elements_of_type, find_elements_of_type
from yanga.cmake.cmake_backend import (
    CMakeCustomTarget,
)
from yanga.cmake.reports import ReportCMakeGenerator
from yanga.domain.components import Component
from yanga.domain.config import DocsConfiguration
from yanga.domain.execution_context import ExecutionContext
from yanga.domain.reports import ReportRelevantFiles, ReportRelevantFileType


@pytest.fixture
def create_executable_generator(execution_context: ExecutionContext, output_dir: Path) -> ReportCMakeGenerator:
    return ReportCMakeGenerator(execution_context, output_dir)


def test_generate(create_executable_generator: ReportCMakeGenerator) -> None:
    elements = create_executable_generator.generate()
    assert elements

    targets = assert_elements_of_type(elements, CMakeCustomTarget, 8)
    assert {target.name for target in targets} == {
        "CompA_docs",
        "CompA_results",
        "CompA_report",
        "CompBNotTestable_docs",
        "CompBNotTestable_results",
        "CompBNotTestable_report",
        "results",
        "report",
    }


def test_create_variant_cmake_elements(
    create_executable_generator: ReportCMakeGenerator,
) -> None:
    elements = create_executable_generator.create_variant_cmake_elements()

    custom_targets = assert_elements_of_type(elements, CMakeCustomTarget, 2)
    assert {target.name for target in custom_targets} == {"report", "results"}


def test_create_components_cmake_elements(
    create_executable_generator: ReportCMakeGenerator,
) -> None:
    elements = create_executable_generator.create_components_cmake_elements()
    assert {target.name for target in find_elements_of_type(elements, CMakeCustomTarget)} == {
        "CompA_docs",
        "CompA_report",
        "CompA_results",
        "CompBNotTestable_docs",
        "CompBNotTestable_report",
        "CompBNotTestable_results",
    }
    comp_cmd = assert_element_of_type(elements, CMakeCustomTarget, lambda target: target.name == "CompA_docs")
    assert [cmd.command for cmd in comp_cmd.commands] == ["clanguru"]
    comp_cmd = assert_element_of_type(elements, CMakeCustomTarget, lambda target: target.name == "CompA_report")
    assert [cmd.command for cmd in comp_cmd.commands] == ["${CMAKE_COMMAND}", "yanga_cmd", "${CMAKE_COMMAND}"]


def test_exclude_productive_code(execution_context: ExecutionContext, output_dir: Path) -> None:
    execution_context.components = [
        Component(
            name="CompA",
            path=Path("compA"),
            sources=["compA_source.cpp"],
            docs=DocsConfiguration(sources=["index.md"], exclude_productive_code=True),
        ),
        Component(
            name="CompB",
            path=Path("compB"),
            sources=["compB_source.cpp"],
            docs=DocsConfiguration(sources=["index.md"], exclude_productive_code=False),
        ),
    ]

    gen = ReportCMakeGenerator(execution_context, output_dir)
    elements = gen.create_components_cmake_elements()

    assert {t.name for t in find_elements_of_type(elements, CMakeCustomTarget)} == {"CompA_results", "CompA_report", "CompB_results", "CompB_report", "CompB_docs"}
    # Only component B SOURCES shall be reported as relevant for the report
    report_relevant_files = execution_context.data_registry.find_data(ReportRelevantFiles)
    assert_elements_of_type(
        report_relevant_files, ReportRelevantFiles, 1, lambda elem: elem.file_type == ReportRelevantFileType.SOURCES and elem.target.target_name == "CompB_docs"
    )
