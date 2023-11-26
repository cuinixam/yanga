from pathlib import Path
from typing import List

from kspl.generate import HeaderWriter
from kspl.kconfig import KConfig
from py_app_dev.core.logging import logger
from py_app_dev.core.scoop_wrapper import ScoopWrapper

from .backends.cmake import CMakeListsBuilder, CMakeRunner
from .backends.generated_file import GeneratedFile
from .environment import BuildEnvironment
from .pipeline import Stage


class YangaScoopInstall(Stage):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind()
        self.install_dirs: List[Path] = []

    def get_name(self) -> str:
        return "yanga_scoop_install"

    @property
    def scoop_file(self) -> Path:
        return self.project_root_dir.joinpath("scoopfile.json")

    def run(self) -> int:
        self.logger.info(
            f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}"
        )
        installed_apps = ScoopWrapper().install(self.scoop_file)
        for app in installed_apps:
            self.install_dirs.extend(app.get_all_required_paths())
        # Update the install directories for the subsequent stages
        self.environment.add_install_dirs(list(set(self.install_dirs)))
        return 0

    def get_inputs(self) -> List[Path]:
        return [self.scoop_file]

    def get_outputs(self) -> List[Path]:
        return self.install_dirs


class YangaBuildConfigure(Stage):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind()
        self.generated_files: List[GeneratedFile] = []

    def get_name(self) -> str:
        return "yanga_build_configure"

    def run(self) -> int:
        self.logger.info(
            f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}"
        )
        self.generated_files.append(self.create_cmake_lists())
        for file in self.generated_files:
            file.to_file()
        return 0

    def create_cmake_lists(self) -> GeneratedFile:
        return (
            CMakeListsBuilder(self.output_dir)
            .with_project_name(self.environment.variant_name)
            .with_components(self.environment.components)
            # TODO: include directories should not be hardcoded here
            .with_include_directories([self.output_dir.joinpath("../gen")])
            .build()
        )

    def get_inputs(self) -> List[Path]:
        return self.environment.user_config_files

    def get_outputs(self) -> List[Path]:
        return [file.path for file in self.generated_files]


class YangaBuildRun(Stage):
    """Run CMake and build the project.
    This stage is always executed. The dependencies are handled by CMake."""

    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind()

    def get_name(self) -> str:
        return "yanga_build_run"

    def run(self) -> int:
        self.logger.info(
            f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}"
        )
        CMakeRunner(self.environment.install_dirs).run(self.output_dir)
        return 0

    def get_inputs(self) -> List[Path]:
        return []

    def get_outputs(self) -> List[Path]:
        return []


class YangaKConfigGen(Stage):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind()
        self.input_files: List[Path] = []

    def get_name(self) -> str:
        return "yanga_kconfig_gen"

    @property
    def header_file(self) -> Path:
        return self.output_dir.joinpath("autoconf.h")

    def run(self) -> int:
        self.logger.info(
            f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}"
        )
        kconfig_model_file = self.project_root_dir.joinpath("KConfig")
        if not kconfig_model_file.is_file():
            self.logger.info("No KConfig file found. Skip this stage.")
            return 0
        kconfig = KConfig(
            kconfig_model_file,
            self.environment.config_file,
        )
        self.input_files = kconfig.get_parsed_files()
        config = kconfig.collect_config_data()
        HeaderWriter(self.header_file).write(config)
        return 0

    def get_inputs(self) -> List[Path]:
        # TODO: Use as input only the user config file where variant configuration is defined.
        # Now all the user config files are used as inputs, which will trigger the generation
        # if any of the file has changed.
        return self.environment.user_config_files + self.input_files

    def get_outputs(self) -> List[Path]:
        return [self.header_file]
