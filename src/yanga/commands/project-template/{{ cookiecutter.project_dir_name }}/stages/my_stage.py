from pathlib import Path
from typing import List

from yanga.core.logging import logger
from yanga.ybuild.pipeline import Stage


class MyStage(Stage):
    def run(self) -> None:
        logger.info(f"Running my stage with output dir '{self.output_dir}'")

    def get_dependencies(self) -> List[Path]:
        return []

    def get_outputs(self) -> List[Path]:
        return []
