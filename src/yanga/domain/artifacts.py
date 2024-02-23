import sys
from pathlib import Path


class ProjectArtifactsLocator:
    """Provides paths to project artifacts."""

    CONFIG_FILENAME = "yanga.yaml"

    def __init__(
        self,
        project_root_dir: Path,
        variant_name: str,
    ) -> None:
        self.project_root_dir = project_root_dir
        self.build_dir = project_root_dir / "build"
        self.variants_dir = project_root_dir / "variants"
        self.platforms_dir = project_root_dir / "platforms"
        self.config_file = project_root_dir / self.CONFIG_FILENAME
        self.variant_build_dir = self.build_dir / variant_name
        self.variant_dir = self.variants_dir / variant_name
        self.external_dependencies_dir = self.build_dir / "external"
        scripts_dir = "Scripts" if sys.platform.startswith("win32") else "bin"
        self.venv_scripts_dir = self.project_root_dir.joinpath(".venv").joinpath(scripts_dir)
