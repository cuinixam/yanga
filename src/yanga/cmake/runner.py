import os
from pathlib import Path
from typing import List

from py_app_dev.core.logging import logger, time_it
from py_app_dev.core.subprocess import SubprocessExecutor


class CMakeRunner:
    executable = "cmake"

    def __init__(self, install_directories: List[Path]) -> None:
        self.logger = logger.bind()
        self.install_directories = install_directories

    def run(self, build_dir: Path, target: str = "all") -> None:
        self.configure(build_dir)
        self.build(build_dir, target)

    @time_it("CMake configure")
    def configure(self, build_dir: Path) -> None:
        build_dir_str = build_dir.absolute().as_posix()
        arguments = f" -S{build_dir_str}" f" -B{build_dir_str}" f" -G Ninja "
        self.run_cmake(arguments)

    @time_it("CMake build")
    def build(self, build_dir: Path, target: str = "all") -> None:
        build_dir_str = build_dir.absolute().as_posix()
        arguments = f" --build {build_dir_str}" f" --target {target} -- "
        self.run_cmake(arguments)

    def run_cmake(self, arguments: str) -> None:
        # Add the install directories to the PATH
        env = os.environ.copy()
        env["PATH"] = ";".join([path.absolute().as_posix() for path in self.install_directories] + [env["PATH"]])
        command = self.executable + " " + arguments
        SubprocessExecutor([command], env=env).execute()
