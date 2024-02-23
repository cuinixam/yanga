from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from typing import Optional

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

from .base import CommandConfigBase, CommandConfigFactory, prompt_user_to_select_option


@dataclass
class BuildCommandConfig(CommandConfigBase):
    variant_name: Optional[str] = field(
        default=None, metadata={"help": "SPL variant name. If none is provided, it will prompt to select one."}
    )
    target: Optional[str] = field(default=None, metadata={"help": "Target to build."})


class BuildCommand(Command):
    def __init__(self) -> None:
        super().__init__("build", "Build a yanga project")
        self.logger = logger.bind()

    @time_it("Build")
    def run(self, args: Namespace) -> int:
        self.logger.info(f"Running {self.name} with args {args}")
        return self.do_run(CommandConfigFactory.create_config(BuildCommandConfig, args))

    def do_run(self, config: BuildCommandConfig) -> int:
        project = YangaProjectSlurper(config.project_dir)
        if not config.variant_name:
            variant_name = prompt_user_to_select_option([variant.name for variant in project.variants])
        else:
            variant_name = config.variant_name
        if not variant_name:
            raise UserNotificationException("No variant selected. Stopping the execution.")
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
        for stage in project.steps:
            StageRunner(build_environment, stage).run()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, BuildCommandConfig)
