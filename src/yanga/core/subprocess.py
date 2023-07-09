import shutil
import subprocess  # nosec
from pathlib import Path
from typing import List, Optional

from .exceptions import UserNotificationException
from .logging import logger


def which(app_name: str) -> Optional[Path]:
    """Return the path to the app if it is in the PATH, otherwise return None."""
    app_path = shutil.which(app_name)
    return Path(app_path) if app_path else None


class SubprocessExecutor:
    def __init__(
        self,
        command: List[str | Path],
        cwd: Optional[Path] = None,
        capture_output: bool = True,
    ):
        self.command = " ".join([str(cmd) for cmd in command])
        self.current_working_directory = cwd
        self.capture_output = capture_output

    def execute(self) -> None:
        result = None
        try:
            logger.info(f"Running command: {self.command}")
            result = subprocess.run(
                self.command.split(),
                cwd=(self.current_working_directory or Path.cwd()).as_posix(),
                capture_output=self.capture_output,
                text=True,  # to get stdout and stderr as strings instead of bytes
            )  # nosec
            result.check_returncode()
        except subprocess.CalledProcessError as e:
            raise UserNotificationException(
                f"Command '{self.command}' failed with:\n"
                f"{result.stdout if result else ''}\n"
                f"{result.stderr if result else e}"
            )
