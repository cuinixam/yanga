from dataclasses import dataclass
from pathlib import Path
from typing import List

from py_app_dev.core.logging import logger
from py_app_dev.core.scoop_wrapper import ScoopWrapper

from yanga.domain.config import BaseConfigJSONMixin
from yanga.domain.execution_context import ExecutionContext
from yanga.domain.pipeline import PipelineStep


@dataclass
class ScoopInstallExecutionInfo(BaseConfigJSONMixin):
    install_dirs: List[Path]


class ScoopInstall(PipelineStep):
    def __init__(self, execution_context: ExecutionContext, output_dir: Path) -> None:
        super().__init__(execution_context, output_dir)
        self.logger = logger.bind()
        self.execution_info = ScoopInstallExecutionInfo([])
        # One needs to keep track of the installed apps to get the required paths
        # even if the step does not need to run.
        self.execution_info_file = self.output_dir.joinpath("scoop_install_exec_info.json")

    def get_name(self) -> str:
        return self.__class__.__name__

    @property
    def install_dirs(self) -> List[Path]:
        return self.execution_info.install_dirs

    @property
    def scoop_file(self) -> Path:
        return self.project_root_dir.joinpath("scoopfile.json")

    def run(self) -> int:
        self.logger.debug(f"Run {self.get_name()} stage. Output dir: {self.output_dir}")
        installed_apps = ScoopWrapper().install(self.scoop_file)
        for app in installed_apps:
            self.install_dirs.extend(app.get_all_required_paths())
        self.execution_info.to_json_file(self.execution_info_file)
        return 0

    def get_inputs(self) -> List[Path]:
        return [self.scoop_file]

    def get_outputs(self) -> List[Path]:
        return self.install_dirs

    def update_execution_context(self) -> None:
        install_dirs = ScoopInstallExecutionInfo.from_json_file(self.execution_info_file).install_dirs
        # Update the install directories for the subsequent stages
        self.execution_context.add_install_dirs(list(set(install_dirs)))
