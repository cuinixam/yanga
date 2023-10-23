import shutil
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from cookiecutter.main import cookiecutter
from mashumaro import DataClassDictMixin
from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger, time_it


@dataclass
class InitCommandConfig(DataClassDictMixin):
    project_dir: Path = field(
        default=Path(".").absolute(),
        metadata={
            "help": "Project root directory. "
            "Defaults to the current directory if not specified."
        },
    )
    mini: Optional[bool] = field(
        default=False,
        metadata={
            "help": "Create a minimal 'hello world' project with one component and one variant.",
            "action": "store_true",
        },
    )

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
        if self.config.mini:
            self.create_mini_project(self.config.project_dir)
        else:
            self.create_project_from_template(self.config.project_dir)

    @staticmethod
    def create_project_from_template(output_dir: Path) -> None:
        YangaInit._check_target_directory(output_dir)
        with TemporaryDirectory() as tmp_dir:
            this_dir = Path(__file__).parent
            tmp_dir_path = Path(tmp_dir)
            project_dir_name = output_dir.name
            cookiecutter(
                this_dir.joinpath("project-template").as_posix(),
                no_input=True,
                output_dir=tmp_dir_path.as_posix(),
                extra_context={"project_dir_name": project_dir_name},
            )
            # Copy the temporary directory to the output directory
            shutil.copytree(
                tmp_dir_path / project_dir_name, output_dir, dirs_exist_ok=True
            )

    @staticmethod
    def create_mini_project(output_dir: Path) -> None:
        YangaInit._check_target_directory(output_dir)
        # Copy the mini-project directory to the output directory
        mini_project_dir = Path(__file__).parent.joinpath("project-mini")
        shutil.copytree(mini_project_dir, output_dir, dirs_exist_ok=True)

    @staticmethod
    def _check_target_directory(output_dir) -> None:
        if output_dir.is_dir() and any(output_dir.iterdir()):
            raise UserNotificationException(
                f"Project directory '{output_dir}' is not empty."
                " The target directory shall either be empty or not exist."
            )


class InitCommand(Command):
    def __init__(self) -> None:
        super().__init__("init", "Init a yanga project")
        self.logger = logger.bind()

    @time_it("Init")
    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        YangaInit(InitCommandConfig.from_namespace(args)).run()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, InitCommandConfig)
