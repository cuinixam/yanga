"""
Command line utility to get create a component specific compile_commands.json.

It gets from the command line:
- path to compile_commands.json
- source-file which can be use multiple times
- output path
"""

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from enum import auto
from pathlib import Path

from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger

from yanga.cmake.generator import GeneratedFile
from yanga.domain.config import BaseConfigJSONMixin, StringableEnum, stringable_enum_field_metadata

from .base import create_config


class ReportScope(StringableEnum):
    COMPONENT = auto()
    VARIANT = auto()


@dataclass
class ReportCommandConfig(BaseConfigJSONMixin):
    scope: ReportScope = field(metadata=stringable_enum_field_metadata(ReportScope))
    variant_name: str = field(metadata={"help": "Variant name to report on. Required if scope is 'variant'."})
    source_files: list[Path] = field(metadata={"help": "Report generation relevant source files."})
    output_file: Path = field(metadata={"help": "Output file path to store the 'report_config.json'."})
    component_name: str | None = field(default=None, metadata={"help": "Component name to report on. Required if scope is 'component'."})


class ReportConfigFile(GeneratedFile):
    def __init__(self, config: ReportCommandConfig) -> None:
        super().__init__(config.output_file)
        self.config = config

    def to_string(self) -> str:
        return self.config.to_json_string()


class ReportCommand(Command):
    def __init__(self) -> None:
        super().__init__("report_config", "Create a component specific report configuration.")
        self.logger = logger.bind()

    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        config = create_config(ReportCommandConfig, args)
        ReportConfigFile(config).to_file()
        self.logger.info(f"Report configuration written to {config.output_file}")
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, ReportCommandConfig)
