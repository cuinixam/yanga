from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path

from mashumaro import DataClassDictMixin

from yanga.core.cmd_line import Command
from yanga.core.logger import logger, time_it


@dataclass
class YangaBuildConfig(DataClassDictMixin):
    project_dir: Path

    @classmethod
    def from_namespace(cls, namespace: Namespace) -> "YangaBuildConfig":
        return cls.from_dict(vars(namespace))


class YangaBuild:
    def __init__(self, config: YangaBuildConfig) -> None:
        self.logger = logger.bind()
        self.config = config

    def run(self) -> None:
        self.logger.info(
            f"Run yanga build in '{self.config.project_dir.absolute().as_posix()}'"
        )


class BuildCommand(Command):
    def __init__(self) -> None:
        super().__init__("build", "Build a yanga project")
        self.logger = logger.bind()

    @time_it()
    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        YangaBuild(YangaBuildConfig.from_namespace(args)).run()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--project-dir", help="Project directory", default=Path("."), type=Path
        )
