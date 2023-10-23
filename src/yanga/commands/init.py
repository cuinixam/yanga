import shutil
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Union

from cookiecutter.main import cookiecutter
from mashumaro import DataClassDictMixin
from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger, time_it


class ProjectBuilder:
    def __init__(self, project_dir: Path, input_dir: Optional[Path] = None) -> None:
        self.project_dir = project_dir
        self.this_dir = (
            input_dir
            if input_dir
            else Path(__file__).parent.joinpath("project-templates")
        )

        self.dirs: List[Path] = []
        self.cookiecutter_dir: Optional[Path] = None

    def with_dir(self, dir: Union[Path, str]) -> "ProjectBuilder":
        self.dirs.append(self.resolve_file_path(dir))
        return self

    def with_cookiecutter_dir(
        self, cookiecutter_dir: Union[Path, str]
    ) -> "ProjectBuilder":
        self.cookiecutter_dir = self.resolve_file_path(cookiecutter_dir)
        return self

    def resolve_file_paths(self, files: List[Path | str]) -> List[Path]:
        return [self.resolve_file_path(file) for file in files]

    def resolve_file_path(self, file: Union[Path, str]) -> Path:
        return self.this_dir.joinpath(file) if isinstance(file, str) else file

    @staticmethod
    def _create_project_from_template(input_dir: Path, output_dir: Path) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            project_dir_name = output_dir.name
            cookiecutter(
                input_dir.as_posix(),
                no_input=True,
                output_dir=tmp_dir_path.as_posix(),
                extra_context={"project_dir_name": project_dir_name},
            )
            # Copy the temporary directory to the output directory
            shutil.copytree(
                tmp_dir_path / project_dir_name, output_dir, dirs_exist_ok=True
            )

    @staticmethod
    def _check_target_directory(project_dir: Path) -> None:
        if project_dir.is_dir() and any(project_dir.iterdir()):
            raise UserNotificationException(
                f"Project directory '{project_dir}' is not empty."
                " The target directory shall either be empty or not exist."
            )

    def build(self) -> None:
        self._check_target_directory(self.project_dir)
        if self.cookiecutter_dir:
            self._create_project_from_template(self.cookiecutter_dir, self.project_dir)
        for dir in self.dirs:
            shutil.copytree(dir, self.project_dir, dirs_exist_ok=True)


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
        project_builder = ProjectBuilder(self.config.project_dir)
        project_builder.with_dir("common").with_cookiecutter_dir("template")

        if self.config.mini:
            project_builder.with_dir("mini")
        else:
            project_builder.with_dir("max")
        project_builder.build()


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
