from yanga.core.logging import logger
from yanga.ybuild.config import YangaConfig
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.pipeline import PipelineLoader, StageRunner


class YangaBuild:
    def __init__(self, environment: BuildEnvironment) -> None:
        self.logger = logger.bind()
        self.environment = environment
        self.artifacts_locator = environment.artifacts_locator

    def run(self) -> None:
        project_dir = self.artifacts_locator.project_root_dir.absolute().as_posix()
        self.logger.info(f"Run yanga build in '{project_dir}'")
        project_config = YangaConfig.from_file(self.artifacts_locator.config_file)
        stages = PipelineLoader(
            project_config.pipeline, self.artifacts_locator.project_root_dir
        ).load_stages()
        for stage in stages:
            StageRunner(self.environment, stage).run()
