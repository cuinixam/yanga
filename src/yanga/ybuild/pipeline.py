import importlib
import shutil
from abc import ABC
from dataclasses import dataclass
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import List, Type

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from py_app_dev.core.runnable import Executor, Runnable

from yanga.project.config import PipelineConfig, StageConfig

from .environment import BuildEnvironment


class Stage(Runnable, ABC):
    def __init__(self, environment: BuildEnvironment, group_name: str) -> None:
        self.environment = environment
        # TODO: I do not like that a Stage knows about a variant and that it has a build dir
        self.output_dir = self.environment.artifacts_locator.variant_build_dir / group_name

    @property
    def project_root_dir(self) -> Path:
        return self.environment.project_root_dir


@dataclass
class BuildStage:
    """TODO: what is the difference between this class and Stage? The name is very strange"""

    group_name: str
    _class: Type[Stage]


class PipelineLoader:
    def __init__(self, pipeline_config: PipelineConfig, project_root_dir: Path) -> None:
        self.pipeline_config = pipeline_config
        self.project_root_dir = project_root_dir

    def load_stages(self) -> List[BuildStage]:
        result = []
        for group_name, stages_config in self.pipeline_config.items():
            result.extend(self._load_stages(group_name, stages_config, self.project_root_dir))
        return result

    @staticmethod
    def _load_stages(group_name: str, stages_config: List[StageConfig], project_root_dir: Path) -> List[BuildStage]:
        result = []
        for stage_config in stages_config:
            stage_class_name = stage_config.class_name or stage_config.stage
            if stage_config.module:
                stage_class = PipelineLoader._load_module_stage(stage_config.module, stage_class_name)
            elif not stage_config.file:
                # no file means that the stage is a built-in stage
                stage_class = PipelineLoader._load_builtin_stage(stage_class_name)
            else:
                stage_class = PipelineLoader._load_user_stage(
                    project_root_dir.joinpath(stage_config.file), stage_class_name
                )
            result.append(BuildStage(group_name, stage_class))
        return result

    @staticmethod
    def _load_builtin_stage(stage_class_name: str) -> Type[Stage]:
        stage_module = import_module("yanga.ybuild.stages")
        try:
            stage_class = getattr(stage_module, stage_class_name)
        except AttributeError:
            raise UserNotificationException(
                f"Stage '{stage_class_name}' is not a Yanga built-in stage."
                " Please check your pipeline configuration."
            )
        return stage_class

    @staticmethod
    def _load_user_stage(python_file: Path, stage_class_name: str) -> Type[Stage]:
        # Create a module specification from the file path
        spec = spec_from_file_location(f"user__{stage_class_name}", python_file)
        if spec and spec.loader:
            stage_module = module_from_spec(spec)
            # Import the module
            spec.loader.exec_module(stage_module)
            try:
                stage_class = getattr(stage_module, stage_class_name)
            except AttributeError:
                raise UserNotificationException(
                    f"Could not load class '{stage_class_name}' from file '{python_file}'."
                    " Please check your pipeline configuration."
                )
            return stage_class
        raise UserNotificationException(
            f"Could not load file '{python_file}'." " Please check the file for any errors."
        )

    @staticmethod
    def _load_module_stage(module_name: str, stage_class_name: str) -> Type[Stage]:
        try:
            module = importlib.import_module(module_name)
            stage_class = getattr(module, stage_class_name)
        except ImportError:
            raise UserNotificationException(
                f"Could not load module '{module_name}'. Please check your pipeline configuration."
            )
        except AttributeError:
            raise UserNotificationException(
                f"Could not load class '{stage_class_name}' from module '{module_name}'."
                " Please check your pipeline configuration."
            )
        return stage_class


class StageRunner:
    """It checks if a stage must run in current environment.
    A stage shall run if any of the dependencies changed or one of the outputs is missing.
    All dependencies and outputs relevant information is stored in the stage output directory
    in a <stage>.deps file.
    """

    def __init__(self, environment: BuildEnvironment, stage: BuildStage) -> None:
        self.logger = logger.bind()
        self.environment = environment
        self.stage = stage

    def run(self) -> None:
        stage = self.stage._class(self.environment, self.stage.group_name)
        if self.environment.is_clean_required():
            self.logger.info(f"Cleaning stage '{stage.__class__.__name__}'")
            shutil.rmtree(stage.output_dir, ignore_errors=True)
        else:
            stage.output_dir.mkdir(parents=True, exist_ok=True)
            Executor(stage.output_dir).execute(stage)
