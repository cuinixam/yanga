"""
Command line utility to get create a component specific compile_commands.json.

It gets from the command line:
- path to compile_commands.json
- source-file which can be use multiple times
- output path
"""

import os
import textwrap
from argparse import ArgumentParser, Namespace
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import auto
from pathlib import Path
from typing import Union

from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger

from yanga.cmake.artifacts_locator import BuildArtifact
from yanga.cmake.generator import GeneratedFile
from yanga.domain.config import BaseConfigJSONMixin, StringableEnum
from yanga.domain.reports import ReportData

from .base import create_config


class GcovReportScope(StringableEnum):
    COMPONENT = auto()
    VARIANT = auto()


def _deserialize_component_objects(raw: object) -> list[Path]:
    """
    Normalize various incoming representations (CMake / argparse / mashumaro) into list[Path].

    Accepted forms:
      - "a.obj;b.obj;c.obj"
      - "a.obj"
      - Path("a.obj")
      - [ "a.obj", "b.obj" ]
      - [ Path("a.obj"), Path("b.obj") ]
      - Nested lists produced by earlier parsing: [[Path("a.obj"), ...], ...]
    """

    def iter_items(value: object) -> Iterator[Union[str, Path]]:
        if isinstance(value, str):
            # CMake style list or single path
            yield from (p for p in value.split(";") if p)
        elif isinstance(value, Path):
            yield value
        elif isinstance(value, list):
            for entry in value:
                yield from iter_items(entry)
        else:
            raise TypeError(f"Unsupported component_objects entry type: {type(value).__name__}")

    return [Path(item) for item in iter_items(raw)]


@dataclass
class ComponentCommandArgs(BaseConfigJSONMixin):
    component_objects: list[Path] = field(
        metadata={
            "help": "List of object files for the component",
            "deserialize": _deserialize_component_objects,
        }
    )
    source_files: list[Path] = field(
        metadata={"help": "Relevant source files."},
    )
    output_file: Path = field(
        metadata={"help": "Output Gcovr configuration file."},
    )


class CreateComponentGcovrConfigCommand(Command):
    def __init__(self) -> None:
        super().__init__("gcovr_config_component", "Create a component specific gcovr configuration file.")
        self.logger = logger.bind()

    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        config = create_config(ComponentCommandArgs, args)
        # Determine the object directory as the common parent of the object files
        if config.component_objects:
            object_directory = os.path.commonpath([obj.parent for obj in config.component_objects])
        else:
            self.logger.error("No component object files provided.")
            return 1
        # Create a gcovr config file
        gcovr_cfg_lines = [
            f"root = {Path(object_directory).as_posix()}",
            *[f"filter = {source_file.as_posix()}" for source_file in config.source_files],
        ]

        GeneratedFile(config.output_file, "\n".join(gcovr_cfg_lines) + "\n").to_file()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, ComponentCommandArgs)


@dataclass
class VariantCommandArgs(BaseConfigJSONMixin):
    variant_report_config: Path = field(metadata={"help": "Variant report configuration"})
    output_file: Path = field(metadata={"help": "Output Gcovr configuration file."})


class CreateVariantGcovrConfigCommand(Command):
    def __init__(self) -> None:
        super().__init__("gcovr_config_variant", "Create a variant gcovr configuration file to collect all components json reports.")
        self.logger = logger.bind()

    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        config = create_config(VariantCommandArgs, args)

        report_config = ReportData.from_json_file(config.variant_report_config)

        # Only include components which have coverage results
        coverage_json_files = [component.build_dir.joinpath(BuildArtifact.COVERAGE_JSON.path) for component in report_config.components if component.coverage_results]

        # Create a gcovr config file
        gcovr_cfg_lines = [
            f"root = {report_config.project_dir.as_posix()}",
            *[f"add-tracefile = {coverage_json.as_posix()}" for coverage_json in coverage_json_files],
        ]

        GeneratedFile(config.output_file, "\n".join(gcovr_cfg_lines) + "\n").to_file()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, VariantCommandArgs)


@dataclass
class DocCommandArgs(BaseConfigJSONMixin):
    output_file: Path = field(
        metadata={"help": "Output doc file."},
    )


class GcovrDocCommand(Command):
    def __init__(self) -> None:
        super().__init__("gcovr_doc", "Create a component documentation file to include the gcovr generated report.")
        self.logger = logger.bind()

    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        config = create_config(DocCommandArgs, args)
        GeneratedFile(
            config.output_file,
            textwrap.dedent("""\
                        # Code Coverage

                        <a href="./coverage/index.html">Report</a>
                        """),
        ).to_file()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, DocCommandArgs)
