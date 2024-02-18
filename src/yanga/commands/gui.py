from argparse import ArgumentParser, Namespace

from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger

from yanga.gui.ygui import YangaGui

from .base import CommandConfigBase, CommandConfigFactory


class GuiCommand(Command):
    def __init__(self) -> None:
        super().__init__("gui", "Start the GUI to build an SPL project.")
        self.logger = logger.bind()

    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        config = CommandConfigFactory.create_config(CommandConfigBase, args)
        YangaGui(config.project_dir).run()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, CommandConfigBase)
