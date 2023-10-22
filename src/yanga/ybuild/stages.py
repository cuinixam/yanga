from pathlib import Path
from typing import List

from py_app_dev.core.logging import logger
from py_app_dev.core.scoop_wrapper import InstalledScoopApp, ScoopWrapper

from .backends.cmake import CMakeListsBuilder, CMakeRunner
from .backends.generated_file import GeneratedFile
from .environment import BuildEnvironment
from .pipeline import Stage


class YangaScoopInstall(Stage):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind()
        self.installed_apps: List[InstalledScoopApp] = []

    def get_name(self) -> str:
        return "yanga_scoop_install"

    @property
    def scoop_file(self) -> Path:
        return self.environment.project_root_dir.joinpath("scoopfile.json")

    def run(self) -> int:
        self.logger.info(
            f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}"
        )
        self.installed_apps = ScoopWrapper().install(self.scoop_file)
        return 0

    def get_inputs(self) -> List[Path]:
        return [self.scoop_file]

    def get_outputs(self) -> List[Path]:
        return [app.path for app in self.installed_apps]


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
            .build()
        )

    def get_inputs(self) -> List[Path]:
        return self.environment.user_config_files

    def get_outputs(self) -> List[Path]:
        return [file.path for file in self.generated_files]


class YangaBuildRun(Stage):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind()

    def get_name(self) -> str:
        return "yanga_build_run"

    def run(self) -> int:
        self.logger.info(
            f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}"
        )
        CMakeRunner().run(self.output_dir)
        return 0

    def get_inputs(self) -> List[Path]:
        return [self.output_dir.joinpath("CMakeLists.txt")]

    def get_outputs(self) -> List[Path]:
        return []
