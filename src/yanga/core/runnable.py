# create a Runnable protocol and make Executor accept it
import hashlib
import json
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import List

from .logging import logger


class Runnable(ABC):
    @abstractmethod
    def run(self) -> int:
        """Run stage"""

    @abstractmethod
    def get_name(self) -> str:
        """Get stage name"""

    @abstractmethod
    def get_inputs(self) -> List[Path]:
        """Get stage dependencies"""

    @abstractmethod
    def get_outputs(self) -> List[Path]:
        """Get stage outputs"""


class RunInfoStatus(Enum):
    MATCH = (False, "Nothing changed. Previous execution info matches.")
    NO_INFO = (True, "No previous execution info found.")
    FILE_NOT_FOUND = (True, "File not found.")
    FILE_CHANGED = (True, "File has changed.")

    def __init__(self, should_run: bool, message: str) -> None:
        self.should_run = should_run
        self.message = message


class Executor:
    """Accepts Runnable objects and executes them.
    It create a file with the same name as the runnable's name
    and stores the inputs and outputs with their hashes.
    If the file exists, it checks the hashes of the inputs and outputs
    and if they match, it skips the execution."""

    RUN_INFO_FILE_EXTENSION = ".deps.json"

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir

    @staticmethod
    def get_file_hash(path: Path) -> str:
        with open(path, "rb") as file:
            bytes = file.read()
            readable_hash = hashlib.sha256(bytes).hexdigest()
            return readable_hash

    def store_run_info(self, runnable: Runnable) -> None:
        file_info = {
            "inputs": {
                str(path): self.get_file_hash(path) for path in runnable.get_inputs()
            },
            "outputs": {
                str(path): self.get_file_hash(path) for path in runnable.get_outputs()
            },
        }

        run_info_path = self.get_runnable_run_info_file(runnable)
        run_info_path.parent.mkdir(parents=True, exist_ok=True)
        with run_info_path.open("w") as f:
            # pretty print the json file
            json.dump(file_info, f, indent=4)

    def get_runnable_run_info_file(self, runnable: Runnable) -> Path:
        return self.cache_dir / f"{runnable.get_name()}{self.RUN_INFO_FILE_EXTENSION}"

    def previous_run_info_matches(self, runnable: Runnable) -> RunInfoStatus:
        run_info_path = self.get_runnable_run_info_file(runnable)
        if not run_info_path.exists():
            return RunInfoStatus.NO_INFO

        with run_info_path.open() as f:
            previous_info = json.load(f)

        for file_type in ["inputs", "outputs"]:
            for path_str, previous_hash in previous_info[file_type].items():
                path = Path(path_str)
                if not path.exists():
                    return RunInfoStatus.FILE_NOT_FOUND
                elif self.get_file_hash(path) != previous_hash:
                    return RunInfoStatus.FILE_CHANGED
        return RunInfoStatus.MATCH

    def execute(self, runnable: Runnable) -> int:
        run_info_status = self.previous_run_info_matches(runnable)
        if run_info_status.should_run:
            logger.info(
                f"Runnable '{runnable.get_name()}' must run. {run_info_status.message}"
            )
            exit_code = runnable.run()
            self.store_run_info(runnable)
            return exit_code
        logger.info(
            f"Runnable '{runnable.get_name()}' execution skipped. {run_info_status.message}"
        )

        return 0
