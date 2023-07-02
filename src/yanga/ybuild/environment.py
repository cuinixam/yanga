from dataclasses import dataclass
from pathlib import Path

from yanga.ybuild.project import ProjectBuildArtifactsLocator


@dataclass
class BuildEnvironment:
    variant_name: str
    build_config: str
    build_target: str
    project_root_dir: Path

    @property
    def artifacts_locator(self) -> ProjectBuildArtifactsLocator:
        return ProjectBuildArtifactsLocator(
            self.project_root_dir, self.variant_name, self.build_config
        )
