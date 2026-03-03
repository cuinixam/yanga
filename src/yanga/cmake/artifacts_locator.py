from enum import Enum
from pathlib import Path

from yanga_core.domain.spl_paths import SPLPaths

from yanga.cmake.cmake_backend import CMakePath


class BuildArtifact(Enum):
    REPORT_CONFIG = "report_config.json"
    TARGETS_DATA = "targets_data.json"
    COMPILE_COMMANDS = "compile_commands.json"
    COVERAGE_JSON = "coverage.json"

    def __init__(self, path: str) -> None:
        self.path = path


class CMakeArtifactsLocator:
    """Defines the paths to the CMake artifacts."""

    def __init__(self, output_dir: Path, spl_paths: SPLPaths) -> None:
        # The directory where the build files will be generated
        self.spl_paths = spl_paths
        self.cmake_build_dir = CMakePath(output_dir, "CMAKE_BUILD_DIR")
        self.cmake_project_dir = CMakePath(self.spl_paths.project_root_dir)
        self.cmake_variant_reports_dir = self.cmake_build_dir.joinpath("reports")

    @property
    def project_root_dir(self) -> Path:
        return self.spl_paths.project_root_dir

    def get_component_build_dir(self, component_name: str) -> CMakePath:
        return self.cmake_build_dir.joinpath(component_name)

    def get_component_reports_dir(self, component_name: str) -> CMakePath:
        return self.get_component_build_dir(component_name).joinpath("reports")

    def get_build_artifact(self, artifact: BuildArtifact) -> CMakePath:
        return self.cmake_build_dir.joinpath(artifact.path)

    def get_component_build_artifact(self, component_name: str, artifact: BuildArtifact) -> CMakePath:
        return self.get_component_build_dir(component_name).joinpath(artifact.path)
