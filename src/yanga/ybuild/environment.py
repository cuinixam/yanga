import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from py_app_dev.core.subprocess import SubprocessExecutor

from yanga.ybuild.generators.build_system_request import (
    BuildSystemRequest,
    CleanVariantRequest,
)
from yanga.ybuild.include_directories_provider import IncludeDirectoriesProvider

from .components import BuildComponent
from .project import ProjectBuildArtifactsLocator


@dataclass
class BuildEnvironment:
    project_root_dir: Path
    build_request: BuildSystemRequest
    components: List[BuildComponent] = field(default_factory=list)
    user_config_files: List[Path] = field(default_factory=list)
    config_file: Optional[Path] = None
    # Keep track of all install directories, updated by any stage for the subsequent stages
    install_dirs: List[Path] = field(default_factory=list)
    # Keep track of all include directory providers
    include_dirs_providers: List[IncludeDirectoriesProvider] = field(default_factory=list)

    @property
    def variant_name(self) -> str:
        # TODO: It is possible to have no variant selected, if there is only one variant in the project.
        return self.build_request.variant_name

    @property
    def include_directories(self) -> List[Path]:
        include_dirs = []
        for provider in self.include_dirs_providers:
            include_dirs.extend(provider.get_include_directories())
        return include_dirs

    @property
    def artifacts_locator(self) -> ProjectBuildArtifactsLocator:
        return ProjectBuildArtifactsLocator(self.project_root_dir, self.variant_name)

    def is_clean_required(self) -> bool:
        return isinstance(self.build_request, CleanVariantRequest)

    def add_install_dirs(self, install_dirs: List[Path]) -> None:
        self.install_dirs.extend(install_dirs)

    def add_include_dirs_provider(self, provider: IncludeDirectoriesProvider) -> None:
        self.include_dirs_providers.append(provider)

    def create_process_executor(self, command: List[str | Path], cwd: Optional[Path] = None) -> SubprocessExecutor:
        # Add the install directories to the PATH
        env = os.environ.copy()
        env["PATH"] = os.pathsep.join([path.absolute().as_posix() for path in self.install_dirs] + [env["PATH"]])
        return SubprocessExecutor(command, cwd=cwd, env=env, shell=True)  # nosec
