from pathlib import Path
from typing import List

from kspl.generate import HeaderWriter
from kspl.kconfig import KConfig
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from py_app_dev.core.scoop_wrapper import ScoopWrapper

from yanga.ybuild.generators.build_system import (
    BuildSystemBackend,
    BuildSystemGenerator,
)
from yanga.ybuild.include_directories_provider import IncludeDirectoriesProvider

from .backends.cmake import CMakeRunner
from .backends.generated_file import GeneratedFile
from .environment import BuildEnvironment
from .pipeline import Stage


class YangaVEnvInstall(Stage):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind()

    @property
    def install_dirs(self) -> List[Path]:
        return [
            self.project_root_dir / dir
            for dir in [".venv/Scripts", ".venv/bin"]
            if (self.project_root_dir / dir).exists()
        ]

    def get_name(self) -> str:
        return "yanga_venv_install"

    def run(self) -> int:
        build_script_path = self.project_root_dir / "bootstrap.py"
        if not build_script_path.exists():
            raise UserNotificationException(
                "Failed to find bootstrap script. Make sure that the project is initialized correctly."
            )
        self.environment.create_process_executor(
            ["python", build_script_path.as_posix()],
            cwd=self.project_root_dir,
        ).execute()
        self.environment.add_install_dirs(self.install_dirs)
        return 0

    def get_inputs(self) -> List[Path]:
        return []

    def get_outputs(self) -> List[Path]:
        return []


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
        self.logger.info(f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}")
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


class YangaWestInstall(Stage):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind()
        self.artifacts_locator = self.environment.artifacts_locator

    def get_name(self) -> str:
        return "yanga_west_install"

    @property
    def west_manifest_file(self) -> Path:
        return self.project_root_dir.joinpath("west.yaml")

    def run(self) -> int:
        self.logger.info(f"Running {self.__class__.__name__} stage. Output dir: {self.output_dir}")
        try:
            self.environment.create_process_executor(
                [
                    "west",
                    "init",
                    "-l",
                    "--mf",
                    self.west_manifest_file.as_posix(),
                    self.project_root_dir.joinpath("build/west").as_posix(),
                ],
                cwd=self.project_root_dir,
            ).execute()
            self.environment.create_process_executor(
                ["west", "update"],
                cwd=self.project_root_dir.joinpath("build"),
            ).execute()
        except Exception as e:
            raise UserNotificationException(f"Failed to initialize and update with west: {e}")

        return 0

    def get_inputs(self) -> List[Path]:
        return [self.west_manifest_file]

    def get_outputs(self) -> List[Path]:
        return []


class YangaBuildConfigure(Stage):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind()
        self.generated_files: List[GeneratedFile] = []

    def get_name(self) -> str:
        return "yanga_build_configure"

    def run(self) -> int:
        self.logger.info(f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}")
        self.generated_files = BuildSystemGenerator(
            BuildSystemBackend.CMAKE, self.environment, self.output_dir
        ).generate()
        for file in self.generated_files:
            file.to_file()
        return 0

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
        self.logger.info(f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}")
        CMakeRunner(self.environment.install_dirs).run(self.output_dir, self.environment.build_request.target_name)
        return 0

    def get_inputs(self) -> List[Path]:
        return []

    def get_outputs(self) -> List[Path]:
        return []


class KConfigIncludeDirectoriesProvider(IncludeDirectoriesProvider):
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def get_include_directories(self) -> List[Path]:
        return [self.output_dir]


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
        self.logger.info(f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}")
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
        # Update the include directories for the subsequent stages
        self.environment.add_include_dirs_provider(KConfigIncludeDirectoriesProvider(self.output_dir))
        return 0

    def get_inputs(self) -> List[Path]:
        # TODO: Use as input only the user config file where variant configuration is defined.
        # Now all the user config files are used as inputs, which will trigger the generation
        # if any of the file has changed.
        return self.environment.user_config_files + self.input_files

    def get_outputs(self) -> List[Path]:
        return [self.header_file]
