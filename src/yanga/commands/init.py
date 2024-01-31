import json
import shutil
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Union

from cookiecutter.main import cookiecutter
from jinja2 import Environment, FileSystemLoader
from mashumaro import DataClassDictMixin
from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger, time_it


@dataclass
class TemplateFileConfig:
    # Relative path to input directory
    src: str
    # Relative path to the output directory. None means root directory.
    dest: Optional[str] = None


class ProjectBuilder:
    def __init__(self, project_dir: Path, input_dir: Optional[Path] = None) -> None:
        self.project_dir = project_dir
        self.input_dir = input_dir if input_dir else Path(__file__).parent.joinpath("project_templates")

        self.dirs: List[Path] = []
        self.cookiecutter_dir: Optional[Path] = None
        # Store tuples of (template_path, destination_path)
        # where the destination path is relative to the output directory
        self.template_files: List[TemplateFileConfig] = []
        self.template_config: Dict[str, Any] = {}
        self.check_target_directory_flag = True

    def with_disable_target_directory_check(self) -> "ProjectBuilder":
        self.check_target_directory_flag = False
        return self

    def with_dir(self, dir: Union[Path, str]) -> "ProjectBuilder":
        self.dirs.append(self.resolve_file_path(dir))
        return self

    def with_cookiecutter_dir(self, cookiecutter_dir: Union[Path, str]) -> "ProjectBuilder":
        self.cookiecutter_dir = self.resolve_file_path(cookiecutter_dir)
        return self

    def with_jinja_template(self, template_path: str, dest_path: Optional[str] = None) -> "ProjectBuilder":
        self.template_files.append(TemplateFileConfig(template_path, dest_path))
        return self

    def with_template_config(self, config: Dict[str, Any]) -> "ProjectBuilder":
        self.template_config.update(config)
        return self

    def with_template_config_file(self, json_file: Union[Path, str]) -> "ProjectBuilder":
        json_file_path = self.resolve_file_path(json_file)
        with json_file_path.open() as f:
            self.template_config.update(json.load(f))
        return self

    def resolve_file_paths(self, files: List[Path | str]) -> List[Path]:
        return [self.resolve_file_path(file) for file in files]

    def resolve_file_path(self, file: Union[Path, str]) -> Path:
        return self.input_dir.joinpath(file) if isinstance(file, str) else file

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
            shutil.copytree(tmp_dir_path / project_dir_name, output_dir, dirs_exist_ok=True)

    @staticmethod
    def _check_target_directory(project_dir: Path) -> None:
        if project_dir.is_dir() and any(project_dir.iterdir()):
            raise UserNotificationException(
                f"Project directory '{project_dir}' is not empty."
                " The target directory shall either be empty or not exist."
            )

    def _render_templates(self) -> None:
        env = Environment(loader=FileSystemLoader(self.input_dir), keep_trailing_newline=True)  # nosec
        for template_file in self.template_files:
            template = env.get_template(template_file.src)
            rendered_content = template.render(self.template_config)
            dest_file_path = template_file.dest if template_file.dest else Path(template_file.src).name
            dest_path = self.project_dir / dest_file_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(rendered_content)

    def build(self) -> None:
        if self.check_target_directory_flag:
            self._check_target_directory(self.project_dir)
        if self.cookiecutter_dir:
            self._create_project_from_template(self.cookiecutter_dir, self.project_dir)
        for dir in self.dirs:
            shutil.copytree(dir, self.project_dir, dirs_exist_ok=True)
        self._render_templates()  # Render and write Jinja2 templates


@dataclass
class InitCommandConfig(DataClassDictMixin):
    project_dir: Path = field(
        default=Path(".").absolute(),
        metadata={"help": "Project root directory. " "Defaults to the current directory if not specified."},
    )

    bootstrap: Optional[bool] = field(
        default=False,
        metadata={
            "help": "Initialize only the bootstrap files.",
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
        self.logger.info(f"Run yanga init in '{self.config.project_dir.absolute().as_posix()}'")
        project_builder = ProjectBuilder(self.config.project_dir)
        project_builder.with_jinja_template("template/bootstrap_j2.ps1", "bootstrap.ps1").with_jinja_template(
            "template/bootstrap_j2.py", "bootstrap.py"
        ).with_jinja_template("template/bootstrap_j2.json", "bootstrap.json").with_template_config_file(
            "template/cookiecutter.json"
        )
        if self.config.bootstrap:
            project_builder.with_disable_target_directory_check()
        else:
            project_builder.with_dir("common").with_cookiecutter_dir("template")
            project_builder.with_dir("mini")
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
