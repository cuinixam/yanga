from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path

from mashumaro import DataClassDictMixin
from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger, time_it

from yanga.gui.ygui import YangaGui


@dataclass
class GuiCommandConfig(DataClassDictMixin):
    project_dir: Path = field(
        default=Path(".").absolute(),
        metadata={"help": "Project root directory. " "Defaults to the current directory if not specified."},
    )

    @classmethod
    def from_namespace(cls, namespace: Namespace) -> "GuiCommandConfig":
        return cls.from_dict(vars(namespace))


class GuiCommand(Command):
    def __init__(self) -> None:
        super().__init__("gui", "Start the GUI to build an SPL project.")
        self.logger = logger.bind()

    @time_it()
    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        config = GuiCommandConfig.from_namespace(args)
        YangaGui(config.project_dir).run()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, GuiCommandConfig)
