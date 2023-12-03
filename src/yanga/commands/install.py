from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path

from mashumaro import DataClassDictMixin
from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger, time_it
from py_app_dev.core.scoop_wrapper import ScoopWrapper


@dataclass
class InstallCommandConfig(DataClassDictMixin):
    scoop_file: Path = field(metadata={"help": "Scoop install configuration file."})

    @classmethod
    def from_namespace(cls, namespace: Namespace) -> "InstallCommandConfig":
        return cls.from_dict(vars(namespace))


class InstallCommand(Command):
    def __init__(self) -> None:
        super().__init__("install", "Run a yanga installer based on the provided arguments")
        self.logger = logger.bind()

    @time_it("Install")
    def run(self, args: Namespace) -> int:
        self.logger.debug(f"Running {self.name} with args {args}")
        self.do_run(InstallCommandConfig.from_namespace(args))
        return 0

    def do_run(self, config: InstallCommandConfig) -> int:
        ScoopWrapper().install(config.scoop_file)
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, InstallCommandConfig)
