from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mashumaro import DataClassDictMixin
from pick import pick
from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger, time_it

from yanga.project.project_slurper import YangaProjectSlurper
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.generators.build_system_request import (
    BuildSystemRequest,
    CustomBuildSystemRequest,
)
from yanga.ybuild.pipeline import StageRunner


@dataclass
class BuildCommandConfig(DataClassDictMixin):
    # If the user does not specify the variant name, it shall be prompted for it.
    variant_name: Optional[str] = field(default=None, metadata={"help": "SPL variant name."})
    project_dir: Path = field(
        default=Path(".").absolute(),
        metadata={"help": "Project root directory. " "Defaults to the current directory if not specified."},
    )
    target: Optional[str] = field(default=None, metadata={"help": "Target to build."})

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
        variant_name = self.select_variant(project, config.variant_name)
        if not variant_name:
            raise UserNotificationException("No variant selected.")
        if config.target:
            build_request = CustomBuildSystemRequest(variant_name, config.target)
        else:
            # TODO: I have no idea why mypy complains here.
            # BuildSystemRequest is a base class for CustomBuildSystemRequest.
            build_request = BuildSystemRequest(variant_name)  # type: ignore
        build_environment = BuildEnvironment(
            config.project_dir,
            build_request,
            project.get_variant_components(variant_name),
            project.user_config_files,
            project.get_variant_config_file(variant_name),
        )
        for stage in project.stages:
            StageRunner(build_environment, stage).run()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, BuildCommandConfig)

    def select_variant(self, project: YangaProjectSlurper, variant_name: Optional[str]) -> Optional[str]:
        if variant_name:
            return variant_name
        if not project.variants:
            return None
        variants = [variant.name for variant in project.variants]
        try:
            # TODO: this message is only necessary in case the user will press Ctrl+C to quit.
            # In this case, after pick method returns, the execution is paused until the user presses any key.
            # I have no idea why that happens.
            self.logger.info("Press any key to continue...")
            selected_variant, _ = pick(variants, "Select a variant: ", indicator="=>")
        except KeyboardInterrupt:
            selected_variant = None
        return str(selected_variant) if selected_variant else None
