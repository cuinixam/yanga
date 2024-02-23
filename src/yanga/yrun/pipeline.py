from pathlib import Path
from typing import List, Optional

from py_app_dev.core.logging import logger
from py_app_dev.core.pipeline import PipelineConfig
from py_app_dev.core.pipeline import PipelineLoader as GenericPipelineLoader
from py_app_dev.core.runnable import Executor

from yanga.domain.artifacts import ProjectArtifactsLocator
from yanga.domain.execution_context import ExecutionContext, UserRequest
from yanga.domain.pipeline import PipelineStep, PipelineStepReference
from yanga.domain.project_slurper import YangaProjectSlurper


class PipelineLoader:
    """Loads pipeline steps from a pipeline configuration.
    The steps are not instantiated, only the references are returned (lazy load).

    The pipeline loader needs to know the project root directory to be able to find the
    user custom local steps."""

    def __init__(self, pipeline_config: PipelineConfig, project_root_dir: Path) -> None:
        self.pipeline_config = pipeline_config
        self.project_root_dir = project_root_dir
        self._loader = GenericPipelineLoader[PipelineStep](self.pipeline_config, self.project_root_dir)

    def load_steps_references(self) -> List[PipelineStepReference]:
        return [
            PipelineStepReference(step_reference.group_name, step_reference._class)
            for step_reference in self._loader.load_steps()
        ]


class PipelineStepsExecutor:
    """Executes a list of pipeline steps sequentially."""

    def __init__(
        self,
        project_slurper: YangaProjectSlurper,
        variant_name: str,
        user_request: UserRequest,
        steps_references: List[PipelineStepReference],
        force_run: bool = False,
    ) -> None:
        self.logger = logger.bind()
        self.project_slurper = project_slurper
        self.variant_name = variant_name
        self.user_request = user_request
        self.steps_references = steps_references
        self.force_run = force_run

    def run(self) -> int:
        execution_context = ExecutionContext(
            self.project_slurper.project_dir,
            self.variant_name,
            self.user_request,
            self.project_slurper.get_variant_components(self.variant_name),
            self.project_slurper.user_config_files,
            self.project_slurper.get_variant_config_file(self.variant_name),
        )
        for step_reference in self.steps_references:
            artifacts_locator = ProjectArtifactsLocator(self.project_slurper.project_dir, self.variant_name)
            step_output_dir = artifacts_locator.variant_build_dir / step_reference.group_name
            step = step_reference._class(execution_context, step_output_dir)
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

    def __init__(self, pipeline: PipelineConfig, project_dir: Path) -> None:
        self.pipeline = pipeline
        self.project_dir = project_dir
        self.logger = logger.bind()

    def get_steps_to_run(self, step_name: Optional[str] = None, single: bool = False) -> List[PipelineStepReference]:
        pipeline_loader = PipelineLoader(self.pipeline, self.project_dir)
        return self.filter_steps_references(pipeline_loader.load_steps_references(), step_name, single)

    @staticmethod
    def filter_steps_references(
        steps_references: List[PipelineStepReference], step_name: Optional[str], single: Optional[bool]
    ) -> List[PipelineStepReference]:
        if step_name:
            step_reference = next((step for step in steps_references if step.name == step_name), None)
            if not step_reference:
                return []
            if single:
                return [step_reference]
            return [
                step
                for step in steps_references
                if steps_references.index(step) <= steps_references.index(step_reference)
            ]
        return steps_references
