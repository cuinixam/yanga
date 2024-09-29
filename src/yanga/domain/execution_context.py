import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import List, Optional, Union

from py_app_dev.core.subprocess import SubprocessExecutor
from pypeline.domain.execution_context import ExecutionContext as _ExecutionContext

from .artifacts import ProjectArtifactsLocator
from .components import Component
from .config import PlatformConfig


class UserRequestTarget(Enum):
    NONE = auto()
    ALL = auto()
    BUILD = auto()
    COMPILE = auto()
    CLEAN = auto()
    TEST = auto()
    MOCKUP = auto()

    def __str__(self) -> str:
        return self.name.lower()


class UserRequestScope(Enum):
    VARIANT = auto()
    COMPONENT = auto()


@dataclass
class UserRequest:
    scope: UserRequestScope
    variant_name: Optional[str] = None
    component_name: Optional[str] = None
    target: Optional[Union[str, UserRequestTarget]] = None

    @property
    def target_name(self) -> str:
        target = str(self.target if self.target else UserRequestTarget.ALL)
        if self.component_name:
            return f"{self.component_name}_{target}"
        return target


class UserVariantRequest(UserRequest):
    def __init__(
        self,
        variant_name: Optional[str],
        target: Optional[Union[str, UserRequestTarget]] = None,
    ) -> None:
        super().__init__(UserRequestScope.VARIANT, variant_name, None, target=target)


class IncludeDirectoriesProvider(ABC):
    @abstractmethod
    def get_include_directories(self) -> List[Path]: ...


@dataclass
class ExecutionContext(_ExecutionContext):
    def __init__(
        self,
        project_root_dir: Path,
        user_request: UserRequest,
        variant_name: Optional[str] = None,
        components: Optional[List[Component]] = None,
        user_config_files: Optional[List[Path]] = None,
        config_file: Optional[Path] = None,
        platform: Optional[PlatformConfig] = None,
    ) -> None:
        super().__init__(project_root_dir)
        self.user_request = user_request
        self.variant_name = variant_name
        self.components = components if components else []
        self.user_config_files = user_config_files if user_config_files else []
        self.config_file = config_file
        self.platform = platform
        self.include_dirs_providers: List[IncludeDirectoriesProvider] = []

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
        return SubprocessExecutor(command, cwd=cwd, env=env, shell=True)  # noqa: S604

    def create_artifacts_locator(self) -> ProjectArtifactsLocator:
        return ProjectArtifactsLocator(
            self.project_root_dir,
            self.variant_name,
            self.platform.name if self.platform else None,
        )
