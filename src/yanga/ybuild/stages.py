from pathlib import Path
from typing import List

from yanga.core.logging import logger
from yanga.core.scoop_wrapper import ScoopWrapper
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.pipeline import Stage


class YangaScoopInstall(Stage):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind()

    @property
    def scoop_file(self) -> Path:
        return self.environment.project_root_dir.joinpath("scoopfile.json")

    def run(self) -> None:
        self.logger.info(
            f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}"
        )
        ScoopWrapper().install(self.scoop_file)

    def get_dependencies(self) -> List[Path]:
        return [self.scoop_file]

    def get_outputs(self) -> List[Path]:
        return []
