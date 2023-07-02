from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import List, Type

from yanga.ybuild.config import PipelineConfig, StageConfig
from yanga.ybuild.environment import BuildEnvironment


class Stage(ABC):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        self.environment = environment
        self.output_dir = self.environment.artifacts_locator.build_dir / group_name

    @abstractmethod
    def run(self) -> None:
        """Run stage"""

    @abstractmethod
    def get_dependencies(self) -> List[Path]:
        """Get stage dependencies"""

    @abstractmethod
    def get_outputs(self) -> List[Path]:
        """Get stage outputs"""


@dataclass
class BuildStage:
    group_name: str
    _class: Type[Stage]


class PipelineLoader:
    def __init__(self, pipeline_config: PipelineConfig) -> None:
        self.pipeline_config = pipeline_config

    def load_stages(self) -> List[BuildStage]:
        result = []
        for group_name, stages_config in self.pipeline_config.items():
            result.extend(self._load_stages(group_name, stages_config))
        return result

    @staticmethod
    def _load_stages(
        group_name: str, stages_config: List[StageConfig]
    ) -> List[BuildStage]:
        result = []
        for stage_config in stages_config:
            stage_class_name = stage_config.class_name or stage_config.stage
            if not stage_config.file:
                # no file means that the stage is a built-in stage
                stage_class = PipelineLoader._load_builtin_stage(stage_class_name)
                result.append(BuildStage(group_name, stage_class))
            else:
                # TODO: load stage from file
                raise NotImplementedError("User defined stages are not supported yet")
        return result

    @staticmethod
    def _load_builtin_stage(stage_class_name: str) -> Type[Stage]:
        stage_module = import_module("yanga.ybuild.stages")
        stage_class = getattr(stage_module, stage_class_name)
        return stage_class


class StageRunner:
    """It checks if a stage must run in current environment.
    A stage shall run if any of the dependencies changed or one of the outputs is missing.
    All dependencies and outputs relevant information is stored in the stage output directory
    in a <stage>.deps file.
    """

    def __init__(self, environment: BuildEnvironment, stage: BuildStage) -> None:
        self.environment = environment
        self.stage = stage

    def run(self) -> None:
        stage = self.stage._class(self.environment, self.stage.group_name)
        if self._must_run(stage):
            stage.run()

    def _must_run(self, stage: Stage) -> bool:
        """A stage shall run if any of the dependencies changed or one of the outputs is missing.
        All dependencies and outputs relevant information is stored in the stage output directory
        in a <stage>.deps file."""
        return True
