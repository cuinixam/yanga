from pathlib import Path
from typing import List

from yanga.core.logger import logger
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.pipeline import Stage


class YangaInstall(Stage):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind()

    def run(self) -> None:
        self.logger.info(
            f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}"
        )

    def get_dependencies(self) -> List[Path]:
        return []

    def get_outputs(self) -> List[Path]:
        return []
