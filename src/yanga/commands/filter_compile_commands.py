"""
Command line utility to get create a component specific compile_commands.json.

It gets from the command line:
- path to compile_commands.json
- source-file which can be use multiple times
- output path
"""

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path

from clanguru.compilation_options_manager import CompilationDatabase, filter_compilation_database
from mashumaro import DataClassDictMixin
from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger

from .base import create_config


@dataclass
class FilterCompileCommandsCommandConfig(DataClassDictMixin):
    compilation_database: Path = field(
        metadata={"help": "Path to compile_commands.json."},
    )
    source_files: list[Path] = field(
        metadata={"help": "Relevant source files."},
    )
    output_file: Path = field(
        metadata={"help": "Output file path to store the filtered compile_commands.json."},
    )


class FilterCompileCommandsCommand(Command):
    def __init__(self) -> None:
        super().__init__("filter_compile_commands", "Create a component specific compile commands file.")
        self.logger = logger.bind()

    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        config = create_config(FilterCompileCommandsCommandConfig, args)
        result = filter_compilation_database(
            CompilationDatabase.from_json_file(config.compilation_database),
            config.source_files,
        )
        result.to_json_file(config.output_file)
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, FilterCompileCommandsCommandConfig)
