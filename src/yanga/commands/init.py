from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path

from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.main import cookiecutter
from mashumaro import DataClassDictMixin

from yanga.core.cmd_line import Command
from yanga.core.exceptions import UserNotificationException
from yanga.core.logger import logger, time_it


@dataclass
class InitCommandConfig(DataClassDictMixin):
    project_dir: Path

    @classmethod
    def from_namespace(cls, namespace: Namespace) -> "InitCommandConfig":
        return cls.from_dict(vars(namespace))


class YangaInit:
    def __init__(self, config: InitCommandConfig) -> None:
        self.logger = logger.bind()
        self.config = config

    def run(self) -> None:
        self.logger.info(
            f"Run yanga init in '{self.config.project_dir.absolute().as_posix()}'"
        )
        self.create_project_from_template(self.config.project_dir)

    @staticmethod
    def create_project_from_template(output_dir: Path) -> None:
        # Create project from the cookiecutter project template
        this_dir = Path(__file__).parent
        project_dir_name = output_dir.name
        project_dir_parent = output_dir.parent
        try:
            cookiecutter(
                this_dir.joinpath("project-template").as_posix(),
                no_input=True,
                output_dir=project_dir_parent.as_posix(),
                extra_context={"project_dir_name": project_dir_name},
            )
        except OutputDirExistsException:
            raise UserNotificationException(
                f"Project directory '{output_dir}' is not empty. "
                "Remove it or use another name."
            )


class InitCommand(Command):
    def __init__(self) -> None:
        super().__init__("init", "Init a yanga project")
        self.logger = logger.bind()

    @time_it()
    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        YangaInit(InitCommandConfig.from_namespace(args)).run()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--project-dir", help="Project directory", default=Path("."), type=Path
        )
