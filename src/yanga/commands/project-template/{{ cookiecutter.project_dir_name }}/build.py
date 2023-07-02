import json
import logging
import os
import re
import subprocess  # nosec
import sys
import venv
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build")


this_dir = Path(__file__).parent
package_manager = "{{ cookiecutter.python_package_manager }}"


class UserNotificationException(Exception):
    pass


class SubprocessExecutor:
    def __init__(self, command: List[str | Path], cwd: Optional[Path] = None):
        self.command = " ".join([str(cmd) for cmd in command])
        self.current_working_directory = cwd

    def execute(self) -> None:
        result = None
        try:
            current_dir = (self.current_working_directory or Path.cwd()).as_posix()
            logger.info(f"Running command: {self.command} in {current_dir}")
            # print all virtual environment variables
            logger.debug(json.dumps(dict(os.environ), indent=4))
            result = subprocess.run(
                self.command,
                cwd=current_dir,
                capture_output=True,
                text=True,  # to get stdout and stderr as strings instead of bytes
            )  # nosec
            result.check_returncode()
        except subprocess.CalledProcessError as e:
            raise UserNotificationException(
                f"Command '{self.command}' failed with error:\n"
                f"{result.stderr if result else e}"
            )


class WindowsVirtualEnvironment:
    def __init__(self, venv_dir: Path) -> None:
        self.venv_dir = venv_dir
        self.activate_script = self.venv_dir.joinpath("Scripts/activate.bat")

    def create(self) -> None:
        """Create a virtual environment and install
        the python package manager with pip"""
        venv.create(self.venv_dir, with_pip=True)

    def pip(self, *args: str) -> None:
        """Run pip commands in the virtual environment"""
        pip_path = self.venv_dir.joinpath("Scripts/pip").as_posix()
        SubprocessExecutor([pip_path, *args], this_dir).execute()

    def run(self, *args: str) -> None:
        """Run commands in the virtual environment"""
        SubprocessExecutor(
            [f"cmd /c {self.activate_script.as_posix()} && ", *args], this_dir
        ).execute()


class Build:
    """TODO: use a VirtualEnvironment class to handle venv
    for different operating systems"""

    @property
    def venv_dir(self) -> Path:
        return this_dir / ".venv"

    @property
    def package_manager_name(self) -> str:
        match = re.match(r"^([a-zA-Z0-9_-]+)", package_manager)

        if match:
            return match.group(1)
        else:
            raise UserNotificationException(
                f"Could not extract the package manager name from {package_manager}"
            )

    def run(self) -> None:
        logger.info("Running project build script")
        virtual_env = WindowsVirtualEnvironment(self.venv_dir)
        virtual_env.create()
        virtual_env.pip("install", package_manager)
        virtual_env.run(self.package_manager_name, "install")
        # TODO: call yanga build
        # virtual_env.run("python -m yanga.ymain", "build")


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
