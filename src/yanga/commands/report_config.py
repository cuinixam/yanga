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

from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger

from yanga.cmake.generator import GeneratedFile
from yanga.domain.config import BaseConfigJSONMixin
from yanga.domain.reports import ReportData

from .base import create_config


@dataclass
class CommandArgs(BaseConfigJSONMixin):
    component_name: str = field(metadata={"help": "Component name to report on. Required if scope is 'component'."})
    variant_report_config: Path = field(metadata={"help": "Variant report configuration"})
    output_file: Path = field(metadata={"help": "Output file path to store the 'report_config.json'."})


class ReportConfigCommand(Command):
    def __init__(self) -> None:
        super().__init__("report_config", "Create a component specific report configuration.")
        self.logger = logger.bind()

    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        cli_args = create_config(CommandArgs, args)
        report_config = ReportData.from_json_file(cli_args.variant_report_config)
        # Search in the report_config components the component that has the name and replace the components with the filter one
        report_config.components = [next(component for component in report_config.components if component.name == cli_args.component_name)]
        report_config.variant_data = None
        # Update component name to signal that this report config is for a specific component
        report_config.component_name = cli_args.component_name
        GeneratedFile(cli_args.output_file, report_config.to_json_string()).to_file()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, CommandArgs)
