import sys
from pathlib import Path
from typing import Optional

from py_app_dev.core.exceptions import UserNotificationException


class ProjectArtifactsLocator:
    """Provides paths to project artifacts."""

    def __init__(
        self,
        project_root_dir: Path,
        variant_name: Optional[str],
        platform_name: Optional[str],
        build_type: Optional[str],
        create_yanga_build_dir: bool = True,
    ) -> None:
        self.project_root_dir = project_root_dir
        yanga_out_dir = project_root_dir / ".yanga"
        self.build_dir = yanga_out_dir / "build" if create_yanga_build_dir else project_root_dir / ".yanga" / "build"
        self.variants_dir = project_root_dir / "variants"
        self.platforms_dir = project_root_dir / "platforms"
        self.variant_build_dir: Path = self.determine_variant_build_dir(variant_name, platform_name, build_type, self.build_dir)
        self.variant_dir: Optional[Path] = self.variants_dir / variant_name if variant_name else None
        # We do not need to create an extra directory if the .yanga build dir is used
        self.external_dependencies_dir = yanga_out_dir if create_yanga_build_dir else self.build_dir
        scripts_dir = "Scripts" if sys.platform.startswith("win32") else "bin"
        self.venv_scripts_dir = self.project_root_dir.joinpath(".venv").joinpath(scripts_dir)

    def locate_artifact(self, artifact: str, first_search_paths: list[Optional[Path]]) -> Path:
        search_paths: list[Optional[Path]] = []
        for path in first_search_paths:
            if path:
                search_paths.append(path.parent if path.is_file() else path)
        search_paths.extend(
            [
                self.variant_dir,
                self.project_root_dir,
                self.platforms_dir,
            ]
        )
        for dir in search_paths:
            if dir and (artifact_path := Path(dir).joinpath(artifact)).exists():
                return artifact_path
        else:
            raise UserNotificationException(f"Artifact '{artifact}' not found in the project. Searched paths: {', '.join(str(p) for p in search_paths if p is not None)}")

    @staticmethod
    def determine_variant_build_dir(variant_name: Optional[str], platform_name: Optional[str], build_type: Optional[str], build_dir: Path) -> Path:
        # build up the path in order: variant, platform, build_type
        parts = []
        if variant_name:
            parts.append(variant_name)
        if platform_name:
            parts.append(platform_name)
        if build_type:
            parts.append(build_type)
        return build_dir.joinpath(*parts) if parts else build_dir
