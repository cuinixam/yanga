import time
from argparse import ArgumentParser, Namespace
from pathlib import Path

from yanga.core.cmd_line import Command
from yanga.core.logger import logger, time_it


class InitCommand(Command):
    def __init__(self) -> None:
        super().__init__("init", "Init a yanga project")
        self.logger = logger.bind()

    @time_it()
    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        time.sleep(0.3)
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--project-dir", help="Project directory", default=Path("."), type=Path
        )
