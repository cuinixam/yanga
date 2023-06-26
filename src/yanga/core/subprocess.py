import shutil
import subprocess  # nosec
from pathlib import Path
from typing import List, Optional

from .exceptions import UserNotificationException
from .logger import logger


def get_app_path(app_name: str) -> Optional[Path]:
    """Return the path to the app if it is in the PATH, otherwise return None."""
    app_path = shutil.which(app_name)
    return Path(app_path) if app_path else None


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
                cwd=(self.current_working_directory or Path.cwd()).as_posix(),
                capture_output=True,
                text=True,  # to get stdout and stderr as strings instead of bytes
            )  # nosec
            result.check_returncode()
        except subprocess.CalledProcessError as e:
            err_message = result.stderr if result else e
            raise UserNotificationException(
                f"Command '{self.command}' failed with error:\n{err_message}"
            )
