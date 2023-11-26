from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .components import BuildComponent
from .project import ProjectBuildArtifactsLocator


@dataclass
class BuildEnvironment:
    variant_name: str
    project_root_dir: Path
    components: List[BuildComponent] = field(default_factory=list)
    user_config_files: List[Path] = field(default_factory=list)
    config_file: Optional[Path] = None
    # Keep track of all install directories, updated by any stage for the subsequent stages
    install_dirs: List[Path] = field(default_factory=list)

    @property
    def artifacts_locator(self) -> ProjectBuildArtifactsLocator:
        return ProjectBuildArtifactsLocator(self.project_root_dir, self.variant_name)

    def add_install_dirs(self, install_dirs: List[Path]) -> None:
        self.install_dirs.extend(install_dirs)
