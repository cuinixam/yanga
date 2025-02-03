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
        self.run_cmake(["-S", build_dir_str, "-B", build_dir_str, "-G", "Ninja"])

    @time_it("CMake build")
    def build(self, build_dir: Path, target: str = "all") -> None:
        build_dir_str = build_dir.absolute().as_posix()
        self.run_cmake(["--build", build_dir_str, "--target", target, "--"])

    def run_cmake(self, arguments: List[str]) -> None:
        # Add the install directories to the PATH
        env = os.environ.copy()
        env["PATH"] = ";".join([path.absolute().as_posix() for path in self.install_directories] + [env["PATH"]])
        SubprocessExecutor([self.executable, *arguments], env=env).execute()
