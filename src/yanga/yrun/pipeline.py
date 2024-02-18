from pathlib import Path
from typing import List

from py_app_dev.core.logging import logger
from py_app_dev.core.pipeline import PipelineConfig
from py_app_dev.core.pipeline import PipelineLoader as GenericPipelineLoader
from py_app_dev.core.runnable import Executor

from yanga.domain.pipeline import PipelineStep, PipelineStepReference


class PipelineLoader:
    """Loads pipeline steps from a pipeline configuration.
    The steps are not instantiated, only the references are returned (lazy load)."""

    def __init__(self, pipeline_config: PipelineConfig, project_root_dir: Path) -> None:
        self.pipeline_config = pipeline_config
        self.project_root_dir = project_root_dir
        self._loader = GenericPipelineLoader[PipelineStep](self.pipeline_config, self.project_root_dir)

    def load_steps(self) -> List[PipelineStepReference]:
        return [
            PipelineStepReference(step_reference.group_name, step_reference._class)
            for step_reference in self._loader.load_steps()
        ]


class PipelineStepsExecutor:
    """Executes a list of pipeline steps sequentially."""

    def __init__(
        self,
        steps: List[PipelineStep],
        force_run: bool = False,
    ) -> None:
        self.logger = logger.bind()
        self.steps = steps
        self.force_run = force_run

    def run(self) -> int:
        for step in self.steps:
            Executor(step.output_dir, self.force_run).execute(step)
        return 0


class PipelineScheduler:
    """
    Schedules which steps must be executed based on the provided configuration:
    * If a step name is provided and the single flag is set, only that step will be executed.
    * If a step name is provided and the single flag is not set, all steps up to the provided step will be executed.
    * In case a command is provided, only the steps up to that command will be executed.
    * If no step name is provided, all steps will be executed.
    """

    def __init__(self, pipeline_config: PipelineConfig, project_root_dir: Path) -> None:
        self.pipeline_config = pipeline_config
        self.project_root_dir = project_root_dir
        self._loader = PipelineLoader(self.pipeline_config, self.project_root_dir)
