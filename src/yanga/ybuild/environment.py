from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from yanga.ybuild.components import BuildComponent
from yanga.ybuild.project import ProjectBuildArtifactsLocator


@dataclass
class BuildEnvironment:
    variant_name: str
    project_root_dir: Path
    components: List[BuildComponent] = field(default_factory=list)

    @property
    def artifacts_locator(self) -> ProjectBuildArtifactsLocator:
        return ProjectBuildArtifactsLocator(self.project_root_dir, self.variant_name)
