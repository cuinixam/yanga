"""Command line utility to generate an HTML report from a CppCheck XML report."""

import xml.etree.ElementTree as ET
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from clanguru.doc_generator import CodeContent, DocStructure, MarkdownFormatter, Section, TextContent
from mashumaro import DataClassDictMixin
from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger

from .base import create_config


@dataclass
class Location(DataClassDictMixin):
    """Represents a location in source code."""

    file: Path
    line: int
    column: int = 0
    info: str = ""


@dataclass
class CppCheckError(DataClassDictMixin):
    """Represents a single CppCheck error/issue."""

    id: str
    severity: str
    msg: str
    verbose: str = ""
    cwe: Optional[str] = None
    file0: Optional[Path] = None
    locations: list[Location] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)


@dataclass
class CppCheckResults(DataClassDictMixin):
    """Representation of the CppCheck XML data."""

    version: str = "2"
    cppcheck_version: str = ""
    errors: list[CppCheckError] = field(default_factory=list)

    def get_errors_by_severity(self) -> dict[str, list[CppCheckError]]:
        """Group errors by severity level."""
        result: dict[str, list[CppCheckError]] = {}
        for error in self.errors:
            if error.severity not in result:
                result[error.severity] = []
            result[error.severity].append(error)
        return result

    def get_errors_by_file(self) -> dict[Path, list[CppCheckError]]:
        """Group errors by source file."""
        result: dict[Path, list[CppCheckError]] = {}
        for error in self.errors:
            # Use file0 if available, otherwise use first location's file
            file_name = error.file0
            if not file_name and error.locations:
                file_name = error.locations[0].file

            if file_name:
                if file_name not in result:
                    result[file_name] = []
                result[file_name].append(error)
        return result

    def get_severity_counts(self) -> dict[str, int]:
        """Get count of errors per severity level."""
        counts: dict[str, int] = {}
        for error in self.errors:
            counts[error.severity] = counts.get(error.severity, 0) + 1
        return counts


def create_doc_structure(cppcheck_data: CppCheckResults, component_name: str, context_lines: int = 3) -> DocStructure:
    """Create a DocStructure from CppCheck results for documentation generation."""
    doc = DocStructure(component_name)

    # Add statistics section
    statistics_section = Section("Statistics")
    total_issues = len(cppcheck_data.errors)
    severity_counts = cppcheck_data.get_severity_counts()

    stats_text = f"Total issues found: {total_issues}\n\n"
    if severity_counts:
        stats_text += "Issues by severity:\n"
        for severity, count in sorted(severity_counts.items()):
            stats_text += f"- {severity}: {count}\n"
    else:
        stats_text += "No issues found."

    statistics_section.add_content(TextContent(stats_text.strip()))
    doc.add_section(statistics_section)

    # Group errors by file and create sections
    errors_by_file = cppcheck_data.get_errors_by_file()

    for file_path, file_errors in sorted(errors_by_file.items()):
        file_section = _create_file_section(file_path, file_errors, context_lines)
        doc.add_section(file_section)

    return doc


def _create_file_section(file_path: Path, file_errors: list[CppCheckError], context_lines: int) -> Section:
    """Create a documentation section for a single file with its errors."""
    file_section = Section(f"File: {file_path}")

    for error in file_errors:
        # Create section for each issue
        issue_title = f"{error.severity.title()}: {error.id}"
        issue_section = Section(issue_title)

        # Add issue description
        description = error.verbose or error.msg
        if error.cwe:
            description += f"\n\nCWE: {error.cwe}"

        issue_section.add_content(TextContent(description))

        # Add code context if we have location information
        primary_location = None
        if error.locations:
            primary_location = error.locations[0]
        elif error.file0:
            # If we only have file0, create a basic location
            primary_location = Location(file=error.file0, line=1)

        if primary_location:
            code_context = _extract_code_context(primary_location, context_lines)
            if code_context:
                # If extraction failed (returns error comment) keep previous formatting via CodeContent
                if code_context.startswith("// Could not read file"):
                    issue_section.add_content(CodeContent(code_context, "c"))
                else:
                    # Provide full MyST directive block directly so use TextContent
                    issue_section.add_content(TextContent(code_context))

        file_section.add_subsection(issue_section)

    return file_section


def _extract_code_context(location: Location, context_lines: int) -> str:
    """
    Extract code context around the specified location and format it as a MyST code-block directive.

    Returns a full MyST fenced directive block, e.g.::

        ```{code-block}
        :linenos:
        :lineno-start: 42
        :emphasize-lines: 3
        <code>
        ```

    If the file can't be read, returns an error comment string starting with
    ``// Could not read file`` so callers may decide on fallback formatting.
    """
    try:
        with open(location.file, encoding="utf-8") as file:
            lines = file.readlines()

        target_line_index = location.line - 1  # 0-based
        if target_line_index < 0 or target_line_index >= len(lines):
            return ""

        # Determine slice
        start_index = max(0, target_line_index - context_lines)
        end_index = min(len(lines), target_line_index + context_lines + 1)

        snippet = [lines[i].rstrip("\n") for i in range(start_index, end_index)]

        # Relative line to emphasize inside snippet (1-based within snippet)
        emphasize_relative = (target_line_index - start_index) + 1
        lineno_start = start_index + 1  # original file line number for first snippet line

        # Build MyST code-block directive
        directive_header = [
            "```{code-block}",
            ":linenos:",
            f":lineno-start: {lineno_start}",
            f":emphasize-lines: {emphasize_relative}",
        ]
        directive_body = "\n".join(snippet)
        myst_block = "\n".join(directive_header) + "\n" + directive_body + "\n```"
        return myst_block
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return f"// Could not read file: {location.file} at line {location.line}"


@dataclass
class CommandArgs(DataClassDictMixin):
    input_file: Path = field(
        metadata={"help": "CppCheck XML report."},
    )
    output_file: Path = field(
        metadata={"help": "Html report."},
    )


class CppCheckReportCommand(Command):
    def __init__(self) -> None:
        super().__init__("cppcheck_report", "Create cppcheck report from the xml results.")
        self.logger = logger.bind()

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, CommandArgs)

    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        config = create_config(CommandArgs, args)
        self.logger.debug(f"Generating HTML report {config.output_file} from {config.input_file}")

        # Load and parse the XML data
        cppcheck_data = self.load_xml_data(config.input_file)

        # Generate the document structure from the cppcheck results
        doc_structure = create_doc_structure(cppcheck_data, "CppCheck Report")

        # Generate the Markdown report
        config.output_file.write_text(MarkdownFormatter().format(doc_structure))

        return 0

    def load_xml_data(self, xml_file: Path) -> CppCheckResults:
        """Parse CppCheck XML output into structured data."""
        self.logger.debug(f"Parsing XML file: {xml_file}")

        try:
            tree = ET.parse(xml_file)  # noqa: S314
            root = tree.getroot()
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse XML file {xml_file}: {e}")
            raise
        except FileNotFoundError:
            self.logger.error(f"XML file not found: {xml_file}")
            raise

        # Extract version information
        results_version = root.attrib.get("version", "2")
        cppcheck_version = ""

        cppcheck_elem = root.find("cppcheck")
        if cppcheck_elem is not None:
            cppcheck_version = cppcheck_elem.attrib.get("version", "")

        # Parse all errors
        errors: list[CppCheckError] = []
        errors_elem = root.find("errors")
        if errors_elem is not None:
            for error_elem in errors_elem.findall("error"):
                error = self._parse_error_element(error_elem)
                errors.append(error)

        return CppCheckResults(version=results_version, cppcheck_version=cppcheck_version, errors=errors)

    def _parse_error_element(self, error_elem: ET.Element) -> CppCheckError:
        """Parse a single error element into a CppCheckError object."""
        # Extract attributes
        error_id = error_elem.attrib.get("id", "")
        severity = error_elem.attrib.get("severity", "")
        msg = error_elem.attrib.get("msg", "")
        verbose = error_elem.attrib.get("verbose", msg)  # fallback to msg if verbose not present
        cwe = error_elem.attrib.get("cwe")
        file0_elem = error_elem.attrib.get("file0")
        file0 = Path(file0_elem) if file0_elem else None

        # Parse locations
        locations: list[Location] = []
        for loc_elem in error_elem.findall("location"):
            location = Location(
                file=Path(loc_elem.attrib.get("file", "")),
                line=int(loc_elem.attrib.get("line", 0)),
                column=int(loc_elem.attrib.get("column", 0)),
                info=loc_elem.attrib.get("info", ""),
            )
            locations.append(location)

        # Parse symbols
        symbols: list[str] = []
        for symbol_elem in error_elem.findall("symbol"):
            if symbol_elem.text:
                symbols.append(symbol_elem.text)

        return CppCheckError(id=error_id, severity=severity, msg=msg, verbose=verbose, cwe=cwe, file0=file0, locations=locations, symbols=symbols)
