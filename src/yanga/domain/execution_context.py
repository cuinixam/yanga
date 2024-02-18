import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from py_app_dev.core.subprocess import SubprocessExecutor

from .components import Component


class IncludeDirectoriesProvider(ABC):
    @abstractmethod
    def get_include_directories(self) -> List[Path]:
        ...


@dataclass
class ExecutionContext:
    project_root_dir: Path
    variant_name: str
    components: List[Component] = field(default_factory=list)
    user_config_files: List[Path] = field(default_factory=list)
    config_file: Optional[Path] = None
    # Keep track of all install directories, updated by any stage for the subsequent stages
    install_dirs: List[Path] = field(default_factory=list)
    # Keep track of all include directory providers
    include_dirs_providers: List[IncludeDirectoriesProvider] = field(default_factory=list)

    @property
    def include_directories(self) -> List[Path]:
        include_dirs = []
        for provider in self.include_dirs_providers:
            include_dirs.extend(provider.get_include_directories())
        return include_dirs

    def add_install_dirs(self, install_dirs: List[Path]) -> None:
        self.install_dirs.extend(install_dirs)

    def add_include_dirs_provider(self, provider: IncludeDirectoriesProvider) -> None:
        self.include_dirs_providers.append(provider)

    def create_process_executor(self, command: List[str | Path], cwd: Optional[Path] = None) -> SubprocessExecutor:
        # Add the install directories to the PATH
        env = os.environ.copy()
        env["PATH"] = os.pathsep.join([path.absolute().as_posix() for path in self.install_dirs] + [env["PATH"]])
        return SubprocessExecutor(command, cwd=cwd, env=env, shell=True)  # nosec
