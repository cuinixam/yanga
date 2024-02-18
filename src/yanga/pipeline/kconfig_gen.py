from pathlib import Path
from typing import List

from kspl.generate import HeaderWriter
from kspl.kconfig import KConfig
from py_app_dev.core.logging import logger

from yanga.domain.execution_context import ExecutionContext, IncludeDirectoriesProvider
from yanga.domain.pipeline import PipelineStep


class KConfigIncludeDirectoriesProvider(IncludeDirectoriesProvider):
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def get_include_directories(self) -> List[Path]:
        return [self.output_dir]


class KConfigGen(PipelineStep):
    def __init__(self, execution_context: ExecutionContext, output_dir: Path) -> None:
        super().__init__(execution_context, output_dir)
        self.logger = logger.bind()
        self.input_files: List[Path] = []

    def get_name(self) -> str:
        return self.__class__.__name__

    @property
    def header_file(self) -> Path:
        return self.output_dir.joinpath("autoconf.h")

    def run(self) -> int:
        self.logger.debug(f"Run {self.get_name()} stage. Output dir: {self.output_dir}")
        kconfig_model_file = self.project_root_dir.joinpath("KConfig")
        if not kconfig_model_file.is_file():
            self.logger.info("No KConfig file found. Skip this stage.")
            return 0
        kconfig = KConfig(
            kconfig_model_file,
            self.execution_context.config_file,
        )
        self.input_files = kconfig.get_parsed_files()
        config = kconfig.collect_config_data()
        HeaderWriter(self.header_file).write(config)
        # Update the include directories for the subsequent steps
        self.execution_context.add_include_dirs_provider(KConfigIncludeDirectoriesProvider(self.output_dir))
        return 0

    def get_inputs(self) -> List[Path]:
        # TODO: Use as input only the user config file where variant configuration is defined.
        # Now all the user config files are used as inputs, which will trigger the generation
        # if any of the file has changed.
        return self.execution_context.user_config_files + self.input_files

    def get_outputs(self) -> List[Path]:
        return [self.header_file]
