from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path

from mashumaro import DataClassDictMixin
from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger, time_it

from yanga.project.project_slurper import YangaProjectSlurper
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.pipeline import StageRunner


@dataclass
class BuildCommandConfig(DataClassDictMixin):
    variant_name: str = field(metadata={"help": "SPL variant name."})
    project_dir: Path = field(
        default=Path(".").absolute(),
        metadata={
            "help": "Project root directory. "
            "Defaults to the current directory if not specified."
        },
    )

    @classmethod
    def from_namespace(cls, namespace: Namespace) -> "BuildCommandConfig":
        return cls.from_dict(vars(namespace))


class BuildCommand(Command):
    def __init__(self) -> None:
        super().__init__("build", "Build a yanga project")
        self.logger = logger.bind()

    @time_it("Build")
    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        return self.do_run(BuildCommandConfig.from_namespace(args))

    def do_run(self, config: BuildCommandConfig) -> int:
        project = YangaProjectSlurper(config.project_dir)
        build_environment = BuildEnvironment(
            config.variant_name,
            config.project_dir,
            project.get_variant_components(config.variant_name),
            project.user_config_files,
            project.get_variant_config_file(config.variant_name),
        )
        for stage in project.stages:
            StageRunner(build_environment, stage).run()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, BuildCommandConfig)
