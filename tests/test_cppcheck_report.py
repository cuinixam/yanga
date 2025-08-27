"""Tests for the CppCheck HTML report command."""

from pathlib import Path
from typing import Callable

from clanguru.doc_generator import CodeContent, Section, TextContent

from tests.utils import assert_element_of_any_type, assert_elements_of_any_type
from yanga.commands.cppcheck_report import (
    CppCheckError,
    CppCheckReportCommand,
    CppCheckResults,
    Location,
    _extract_code_context,
    create_doc_structure,
)


def test_load_xml_data_detailed_checks(get_test_data_path: Callable[[str], Path]) -> None:
    source_file = Path("tests/data/sample_cppcheck_input.c")
    xml_file = get_test_data_path("sample_cppcheck_output.xml")
    results = CppCheckReportCommand().load_xml_data(xml_file)

    # Find the null pointer error using utility function
    null_pointer_error = assert_element_of_any_type(results.errors, CppCheckError, lambda error: error.id == "nullPointer")
    assert null_pointer_error.severity == "error"
    assert null_pointer_error.cwe == "476"
    assert null_pointer_error.file0 == source_file
    assert len(null_pointer_error.locations) == 2
    assert len(null_pointer_error.symbols) == 1
    assert null_pointer_error.symbols[0] == "ptr"

    # Check locations
    locations = null_pointer_error.locations
    assert locations[0].file == source_file
    assert locations[0].line == 16
    assert locations[0].column == 6
    assert "dereference" in locations[0].info.lower()

    assert locations[1].file == source_file
    assert locations[1].line == 15
    assert locations[1].column == 16
    assert "assignment" in locations[1].info.lower()


def test_create_doc_structure_empty_results() -> None:
    results = CppCheckResults()
    doc = create_doc_structure(results, "TestComponent")

    assert doc.title == "TestComponent"
    assert len(doc.sections) == 1
    assert doc.sections[0].title == "Statistics"
    assert len(doc.sections[0].content) == 1
    assert isinstance(doc.sections[0].content[0], TextContent)
    assert "Total issues found: 0" in doc.sections[0].content[0].text
    assert "No issues found." in doc.sections[0].content[0].text


def test_create_doc_structure_with_errors() -> None:
    errors = [
        CppCheckError(
            id="nullPointer",
            severity="error",
            msg="Null pointer dereference",
            verbose="Dereferencing a null pointer leads to undefined behavior",
            cwe="476",
            file0=Path("test.c"),
            locations=[Location(file=Path("test.c"), line=10, column=5)],
        ),
        CppCheckError(
            id="uninitVar",
            severity="warning",
            msg="Uninitialized variable",
            verbose="Variable 'x' is not initialized",
            locations=[Location(file=Path("test.c"), line=15, column=8)],
        ),
        CppCheckError(
            id="bufferOverflow",
            severity="error",
            msg="Buffer overflow",
            verbose="Writing outside buffer boundaries",
            locations=[Location(file=Path("other.c"), line=5, column=2)],
        ),
    ]

    results = CppCheckResults(errors=errors)
    doc = create_doc_structure(results, "MyProject")

    assert doc.title == "MyProject"

    # Check statistics section using utility function
    stats_section = assert_element_of_any_type(doc.sections, Section, lambda section: section.title == "Statistics")
    assert isinstance(stats_section.content[0], TextContent)
    stats_text = stats_section.content[0].text
    assert "Total issues found: 3" in stats_text
    assert "error: 2" in stats_text
    assert "warning: 1" in stats_text

    # Check file sections using utility functions
    file_sections = assert_elements_of_any_type(doc.sections, Section, 2, lambda section: section.title.startswith("File:"))

    # Check first file section (other.c should come first alphabetically)
    other_file_section = assert_element_of_any_type(file_sections, Section, lambda section: section.title == "File: other.c")
    assert len(other_file_section.subsections) == 1

    buffer_issue = other_file_section.subsections[0]
    assert buffer_issue.title == "Error: bufferOverflow"
    assert len(buffer_issue.content) == 2  # Description + code context (file not found message)
    assert isinstance(buffer_issue.content[0], TextContent)
    assert "Writing outside buffer boundaries" in buffer_issue.content[0].text
    assert isinstance(buffer_issue.content[1], CodeContent)
    assert "Could not read file: other.c at line 5" in buffer_issue.content[1].code

    # Check second file section (test.c)
    test_file_section = assert_element_of_any_type(file_sections, Section, lambda section: section.title == "File: test.c")
    assert len(test_file_section.subsections) == 2

    # Check first issue in test.c (nullPointer)
    null_issue = assert_element_of_any_type(test_file_section.subsections, Section, lambda subsection: subsection.title == "Error: nullPointer")
    assert len(null_issue.content) == 2  # Description + code context (file not found message)
    assert isinstance(null_issue.content[0], TextContent)
    assert "Dereferencing a null pointer leads to undefined behavior" in null_issue.content[0].text
    assert "CWE: 476" in null_issue.content[0].text
    assert isinstance(null_issue.content[1], CodeContent)
    assert "Could not read file: test.c at line 10" in null_issue.content[1].code

    # Check second issue in test.c (uninitVar)
    uninit_issue = assert_element_of_any_type(test_file_section.subsections, Section, lambda subsection: subsection.title == "Warning: uninitVar")
    assert len(uninit_issue.content) == 2  # Description + code context (file not found message)
    assert isinstance(uninit_issue.content[0], TextContent)
    assert "Variable 'x' is not initialized" in uninit_issue.content[0].text
    assert isinstance(uninit_issue.content[1], CodeContent)
    assert "Could not read file: test.c at line 15" in uninit_issue.content[1].code


def test_extract_code_context_file_not_found() -> None:
    context = _extract_code_context(Location(file=Path("nonexistent.c"), line=10, column=5), 3)
    assert "Could not read file: nonexistent.c at line 10" in context


def test_extract_code_context_with_file(get_test_data_path: Callable[[str], Path]) -> None:
    test_file = get_test_data_path("sample_cppcheck_input.c")
    location = Location(file=test_file, line=16, column=5)  # The null pointer dereference line

    context = _extract_code_context(location, 2)

    # Check that we get the expected format with line numbers
    assert ">>> " in context  # Marker for the target line
    assert "16:" in context  # Line number
    assert "*ptr = 42;" in context  # The actual problematic line
    assert "int *ptr = NULL;" in context  # Line before (line 15)
    assert "return 0;" in context  # Line after (line 17)


def test_create_doc_structure_with_code_context(get_test_data_path: Callable[[str], Path]) -> None:
    test_file = get_test_data_path("sample_cppcheck_input.c")

    errors = [
        CppCheckError(
            id="nullPointer",
            severity="error",
            msg="Null pointer dereference",
            verbose="Dereferencing a null pointer",
            locations=[Location(file=test_file, line=16, column=5)],
        ),
    ]

    results = CppCheckResults(errors=errors)
    doc = create_doc_structure(results, "TestProject", context_lines=1)

    # Find the file section using utility function
    file_section = assert_element_of_any_type(doc.sections, Section, lambda section: section.title.startswith("File:"))
    assert len(file_section.subsections) == 1

    issue_section = file_section.subsections[0]
    assert len(issue_section.content) == 2  # Description + Code context

    # Check code content
    code_content = issue_section.content[1]
    assert isinstance(code_content, CodeContent)
    assert code_content.language == "c"
    assert "*ptr = 42;" in code_content.code
    assert ">>> " in code_content.code  # Target line marker
