import json
import logging
import os
import subprocess  # nosec
import sys
import venv
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("build")


this_dir = Path(__file__).parent
# TODO: the python package manager should be configurable, e.g.: "poetry=>1.5.1"
package_manager = "poetry>=1.5.1"


class UserNotificationException(Exception):
    pass


class SubprocessExecutor:
    def __init__(self, command: List[str | Path], cwd: Optional[Path] = None):
        self.command = " ".join([str(cmd) for cmd in command])
        self.current_working_directory = cwd

    def execute(self) -> None:
        result = None
        try:
            logger.info(f"Running command: {self.command}")
            result = subprocess.run(
                self.command,
                cwd=str(self.current_working_directory or Path.cwd()),
                capture_output=True,
                text=True,  # to get stdout and stderr as strings instead of bytes
            )  # nosec
            result.check_returncode()
        except subprocess.CalledProcessError as e:
            raise UserNotificationException(
                f"Command '{self.command}' failed with error:\n"
                f"{result.stderr if result else e}"
            )


class Build:
    """TODO: use a VirtualEnvironment class to handle venv
    for different operating systems"""

    @property
    def venv_dir(self) -> Path:
        return this_dir / ".venv"

    def run(self) -> None:
        logger.info("Running project build script")
        self.create_virtual_environment()
        self.install_package_manager()
        self.install_project_dependencies()

    def create_virtual_environment(self) -> None:
        """Create a virtual environment and install
        the python package manager with pip"""
        venv.create(self.venv_dir, with_pip=True)

    def install_package_manager(self) -> None:
        """Install the python package manager with pip"""
        pip_path = self.venv_dir.joinpath("Scripts/pip").as_posix()
        SubprocessExecutor([pip_path, "install", package_manager]).execute()

    def install_project_dependencies(self) -> None:
        """Install the project dependencies using the python package manager"""
        poetry_path = self.venv_dir.joinpath("Scripts/poetry").as_posix()
        SubprocessExecutor([poetry_path, "install"], this_dir).execute()


def print_environment_info() -> None:
    str_bar = "".join(["-" for _ in range(80)])
    logger.debug(str_bar)
    logger.debug("Environment: \n" + json.dumps(dict(os.environ), indent=4))
    logger.info(str_bar)
    logger.info(f"Arguments: {sys.argv[1:]}")
    logger.info(str_bar)


def main() -> int:
    try:
        # print_environment_info()
        Build().run()
    except UserNotificationException as e:
        logger.error(e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

if __name__ == "__test_main__":
    """This is used to execute the build script from a test and
    it shall not call sys.exit()"""
    main()
