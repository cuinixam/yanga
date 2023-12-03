from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .components import BuildComponent
from .project import ProjectBuildArtifactsLocator


@dataclass
class BuildRequest:
    variant_name: str
    component_name: Optional[str] = None
    # TODO: str is too generic and error prone, we should have a type for this
    command: Optional[str] = None


@dataclass
class BuildEnvironment:
    project_root_dir: Path
    build_request: BuildRequest
    components: List[BuildComponent] = field(default_factory=list)
    user_config_files: List[Path] = field(default_factory=list)
    config_file: Optional[Path] = None
    # Keep track of all install directories, updated by any stage for the subsequent stages
    install_dirs: List[Path] = field(default_factory=list)

    @property
    def variant_name(self) -> str:
        return self.build_request.variant_name

    @property
    def artifacts_locator(self) -> ProjectBuildArtifactsLocator:
        return ProjectBuildArtifactsLocator(self.project_root_dir, self.variant_name)

    def is_clean_required(self) -> bool:
        return self.build_request.command == "clean"

    def add_install_dirs(self, install_dirs: List[Path]) -> None:
        self.install_dirs.extend(install_dirs)
