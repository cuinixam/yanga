from pathlib import Path


class ProjectArtifactsLocator:
    """Provides paths to project artifacts."""

    config_file_name = "yanga.yaml"

    def __init__(self, project_root_dir: Path) -> None:
        self.project_root_dir = project_root_dir
        self.variants_dir = project_root_dir.joinpath("variants")
        self.platforms_dir = project_root_dir.joinpath("platforms")
        self.config_file = project_root_dir.joinpath(self.config_file_name)


class ProjectBuildArtifactsLocator(ProjectArtifactsLocator):
    def __init__(
        self,
        project_root_dir: Path,
        variant_name: str,
    ) -> None:
        super().__init__(project_root_dir)
        self.build_dir = project_root_dir / "build" / variant_name
        self.variant_dir = self.variants_dir / variant_name
