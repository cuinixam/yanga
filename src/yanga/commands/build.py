from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path

from mashumaro import DataClassDictMixin

from yanga.core.cmd_line import Command, register_arguments_for_config_dataclass
from yanga.core.logging import logger, time_it
from yanga.ybuild.build_main import YangaBuild
from yanga.ybuild.environment import BuildEnvironment


@dataclass
class BuildCommandConfig(DataClassDictMixin):
    variant_name: str = field(metadata={"help": "SPL variant name."})
    build_config: str = field(metadata={"help": "Build configuration name."})
    build_target: str = field(metadata={"help": "Build target name."})
    project_dir: Path = field(
        default=Path("."),
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
        config = BuildCommandConfig.from_namespace(args)
        # search variant
        # create project build artifacts locator
        environment = BuildEnvironment(
            config.variant_name,
            config.build_config,
            config.build_target,
            config.project_dir,
        )
        YangaBuild(environment).run()
        return 0

    def _register_arguments(self, parser: ArgumentParser) -> None:
        register_arguments_for_config_dataclass(parser, BuildCommandConfig)
