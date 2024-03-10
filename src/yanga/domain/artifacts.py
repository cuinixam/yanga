import sys
from pathlib import Path
from typing import List, Optional

from py_app_dev.core.exceptions import UserNotificationException


class ProjectArtifactsLocator:
    """Provides paths to project artifacts."""

    CONFIG_FILENAME = "yanga.yaml"

    def __init__(
        self,
        project_root_dir: Path,
        variant_name: Optional[str],
        platform_name: Optional[str],
    ) -> None:
        self.project_root_dir = project_root_dir
        self.build_dir = project_root_dir / "build"
        self.variants_dir = project_root_dir / "variants"
        self.platforms_dir = project_root_dir / "platforms"
        self.config_file = project_root_dir / self.CONFIG_FILENAME
        self.variant_build_dir: Path = self.determine_variant_build_dir(variant_name, platform_name, self.build_dir)
        self.variant_dir: Optional[Path] = self.variants_dir / variant_name if variant_name else None
        self.external_dependencies_dir = self.build_dir / "external"
        scripts_dir = "Scripts" if sys.platform.startswith("win32") else "bin"
        self.venv_scripts_dir = self.project_root_dir.joinpath(".venv").joinpath(scripts_dir)

    def locate_artifact(self, artifact: str, first_search_paths: List[Optional[Path]]) -> Path:
        search_paths = []
        for path in first_search_paths:
            if path:
                search_paths.append(path.parent if path.is_file() else path)
        for dir in [
            *search_paths,
            self.variant_dir,
            self.project_root_dir,
            self.platforms_dir,
        ]:
            if dir and (artifact_path := Path(dir).joinpath(artifact)).exists():
                return artifact_path
        else:
            raise UserNotificationException(f"Artifact '{artifact}' not found in the project.")

    @staticmethod
    def determine_variant_build_dir(variant_name: Optional[str], platform_name: Optional[str], build_dir: Path) -> Path:
        if variant_name and platform_name:
            return build_dir / variant_name / platform_name
        if variant_name:
            return build_dir / variant_name
        return build_dir
