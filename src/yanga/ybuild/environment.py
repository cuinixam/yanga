from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .components import BuildComponent
from .project import ProjectBuildArtifactsLocator


@dataclass
class BuildEnvironment:
    variant_name: str
    project_root_dir: Path
    components: List[BuildComponent] = field(default_factory=list)
    user_config_files: List[Path] = field(default_factory=list)

    @property
    def artifacts_locator(self) -> ProjectBuildArtifactsLocator:
        return ProjectBuildArtifactsLocator(self.project_root_dir, self.variant_name)
