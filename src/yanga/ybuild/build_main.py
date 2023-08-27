from typing import List

from yanga.core.logging import logger
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.pipeline import BuildStage, StageRunner


class YangaBuild:
    def __init__(self, environment: BuildEnvironment, stages: List[BuildStage]) -> None:
        self.logger = logger.bind()
        self.environment = environment
        self.stages = stages
        self.artifacts_locator = environment.artifacts_locator

    def run(self) -> None:
        project_dir = self.artifacts_locator.project_root_dir.absolute().as_posix()
        self.logger.info(f"Run yanga build in '{project_dir}'")
        for stage in self.stages:
            StageRunner(self.environment, stage).run()
