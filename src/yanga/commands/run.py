from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from typing import List, Optional

from py_app_dev.core.cmd_line import Command, register_arguments_for_config_dataclass
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger, time_it

from yanga.domain.config import PlatformConfig, VariantConfig
from yanga.domain.execution_context import UserRequest, UserRequestScope
from yanga.domain.project_slurper import YangaProjectSlurper
from yanga.yrun import PipelineScheduler, PipelineStepsExecutor

from .base import CommandConfigBase, CommandConfigFactory, prompt_user_to_select_option


@dataclass
class RunCommandConfig(CommandConfigBase):
    platform: Optional[str] = field(
        default=None,
        metadata={"help": "Platform for which to build (see the available platforms in the configuration)."},
    )
    variant_name: Optional[str] = field(
        default=None,
        metadata={"help": "SPL variant name. If none is provided, it will prompt to select one."},
    )
    component_name: Optional[str] = field(
        default=None, metadata={"help": "Restrict the scope to one specific component."}
    )
    target: Optional[str] = field(default=None, metadata={"help": "Define a specific target to execute."})
    step: Optional[str] = field(
        default=None,
        metadata={"help": "Name of the step to run (as written in the pipeline config)."},
    )
    single: bool = field(
        default=False,
        metadata={
            "help": "If provided, only the provided step will run,"
            " without running all previous steps in the pipeline.",
            "action": "store_true",
        },
    )
    print: bool = field(
        default=False,
        metadata={
            "help": "Print the pipeline steps.",
            "action": "store_true",
        },
    )
    force_run: bool = field(
        default=False,
        metadata={
            "help": "Force the execution of a step even if it is not dirty.",
            "action": "store_true",
        },
    )


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
        project_slurper = YangaProjectSlurper(config.project_dir)
        if config.print:
            project_slurper.print_project_info()
            return 0
        variant_name = self.determine_variant_name(config.variant_name, project_slurper.variants)
        platform_name = self.determine_platform_name(config.platform, project_slurper.platforms)
        if not project_slurper.pipeline:
            raise UserNotificationException("No pipeline found in the configuration.")
        # Schedule the steps to run
        steps_references = PipelineScheduler(project_slurper.pipeline, config.project_dir).get_steps_to_run(
            config.step, config.single
        )
        if not steps_references:
            if config.step:
                raise UserNotificationException(f"Step '{config.step}' not found in the pipeline.")
            self.logger.info("No steps to run.")
            return 0
        user_request = UserRequest(
            (UserRequestScope.COMPONENT if config.component_name else UserRequestScope.VARIANT),
            variant_name,
            config.component_name,
            config.target,
        )
        PipelineStepsExecutor(
            project_slurper,
            variant_name,
            platform_name,
            user_request,
            steps_references,
            config.force_run,
        ).run()
        return 0

    def determine_variant_name(
        self, variant_name: Optional[str], variant_configs: List[VariantConfig]
    ) -> Optional[str]:
        selected_variant_name: Optional[str]
        if not variant_name:
            if len(variant_configs) == 1:
                selected_variant_name = variant_configs[0].name
                self.logger.info(f"Only one variant found. Using '{selected_variant_name}'.")
            else:
                selected_variant_name = prompt_user_to_select_option(
                    [variant.name for variant in variant_configs], "Select variant: "
                )
        else:
            selected_variant_name = variant_name
        if not selected_variant_name:
            self.logger.warning("No variant selected. This might cause some steps to fail.")
        return selected_variant_name

    def determine_platform_name(
        self, platform_name: Optional[str], platform_configs: List[PlatformConfig]
    ) -> Optional[str]:
        selected_platform_name: Optional[str]
        if not platform_name:
            if len(platform_configs) == 1:
                selected_platform_name = platform_configs[0].name
                self.logger.info(f"Only one platform found. Using '{selected_platform_name}'.")
            else:
                selected_platform_name = prompt_user_to_select_option(
                    [platform.name for platform in platform_configs],
                    "Select platform: ",
                )
        else:
            selected_platform_name = platform_name
        if not selected_platform_name:
            self.logger.warning("No platform selected. This might cause some steps to fail.")
        return selected_platform_name

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, RunCommandConfig)
