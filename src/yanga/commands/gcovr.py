"""
Command line utility to get create a component specific compile_commands.json.

It gets from the command line:
- path to compile_commands.json
- source-file which can be use multiple times
- output path
"""

import textwrap
from argparse import ArgumentParser, Namespace
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import auto
from pathlib import Path
from typing import Union

from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger

from yanga.cmake.generator import GeneratedFile
from yanga.domain.config import BaseConfigJSONMixin, StringableEnum

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
class CommandArgs(BaseConfigJSONMixin):
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


class GcovrConfigCommand(Command):
    def __init__(self) -> None:
        super().__init__("gcovr_config", "Create a component specific gcovr configuration file.")
        self.logger = logger.bind()

    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        config = create_config(CommandArgs, args)
        if config.component_objects:
            object_directory = config.component_objects[0].parent
        else:
            self.logger.error("No component object files provided.")
            return 1
        # Create a gcovr config file
        gcovr_cfg_lines = [
            f"root = {object_directory.as_posix()}",
            *[f"filter = {source_file.as_posix()}" for source_file in config.source_files],
        ]

        GeneratedFile(config.output_file, "\n".join(gcovr_cfg_lines) + "\n").to_file()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, CommandArgs)


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
