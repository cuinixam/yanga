from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from typing import List, Optional

from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.logging import logger, time_it

from yanga.commands.project_templates.template.bootstrap_j2 import (
    UserNotificationException,
)
from yanga.project.project_slurper import YangaProjectSlurper
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.generators.build_system_request import BuildSystemRequest
from yanga.ybuild.pipeline import BuildStage, StageRunner

from .base import CommandConfigBase, CommandConfigFactory, prompt_user_to_select_option

# TODO: Refactor this and the build command to avoid code duplication


@dataclass
class RunCommandConfig(CommandConfigBase):
    variant_name: Optional[str] = field(
        default=None, metadata={"help": "SPL variant name. If none is provided, it will prompt to select one."}
    )
    step: Optional[str] = field(default=None, metadata={"help": "Name of the step to run."})
    single: Optional[bool] = field(
        default=False,
        metadata={
            "help": "If provided, only the provided step will run,"
            " without running all previous steps in the pipeline.",
            "action": "store_true",
        },
    )
    print: Optional[bool] = field(
        default=False,
        metadata={
            "help": "Print the pipeline steps.",
            "action": "store_true",
        },
    )
    # TODO: Add a flag to force the execution of a step even if it is not dirty


class RunCommand(Command):
    def __init__(self) -> None:
        super().__init__("run", "Run a yanga pipeline step (and all previous steps if necessary).")
        self.logger = logger.bind()

    @time_it("Run")
    def run(self, args: Namespace) -> int:
        self.logger.debug(f"Running {self.name} with args {args}")
        self.do_run(CommandConfigFactory.create_config(RunCommandConfig, args))
        return 0

    def do_run(self, config: RunCommandConfig) -> int:
        project = YangaProjectSlurper(config.project_dir)
        variant_name = prompt_user_to_select_option([variant.name for variant in project.variants], config.variant_name)
        if not variant_name:
            raise UserNotificationException("No variant selected. Stopping the execution.")
        if config.print:
            self.print_steps_info(project.steps)
            return 0
        if not project.steps:
            raise UserNotificationException("No steps found. Check you pipeline configuration.")
        # Check if the step exists in the pipeline
        provided_steps_names = [step.config.stage for step in project.steps]
        if config.step and config.step not in provided_steps_names:
            raise UserNotificationException(
                f"Step '{config.step}' not found in the pipeline. Check your pipeline configuration."
            )
        if not config.step and config.single:
            raise UserNotificationException(
                "The 'single' flag can only be used in combination with the 'step' argument."
            )
        build_environment = BuildEnvironment(
            config.project_dir,
            BuildSystemRequest(variant_name),
            project.get_variant_components(variant_name),
            project.user_config_files,
            project.get_variant_config_file(variant_name),
        )
        # Check if the user only wants to run the step without running all previous steps
        if config.single:
            selected_step = next(step for step in project.steps if step.config.stage == config.step)
            StageRunner(build_environment, selected_step).run()
        else:
            for step in project.steps:
                StageRunner(build_environment, step).run()
                if step.config.stage == config.step:
                    break

        return 0

    def print_steps_info(self, steps: List[BuildStage]) -> None:
        if not steps:
            self.logger.info("No steps found. Check you pipeline configuration.")
        self.logger.info("Pipeline steps:")
        for step in steps:
            self.logger.info(f"- {step.config.stage}")

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, RunCommandConfig)
