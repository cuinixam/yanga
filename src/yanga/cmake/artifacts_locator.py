from enum import Enum
from pathlib import Path

from yanga.cmake.cmake_backend import CMakePath
from yanga.domain.execution_context import ExecutionContext


class ComponentBuildArtifact(Enum):
    REPORT_CONFIG = "report_config.json"
    COMPILE_COMMANDS = "component_compile_commands.json"
    COVERAGE_JSON = "coverage.json"
    COVERAGE_DOC = "coverage.md"

    def __init__(self, path: str) -> None:
        self.path = path


class CMakeArtifactsLocator:
    """Defines the paths to the CMake artifacts."""

    def __init__(self, output_dir: Path, execution_context: ExecutionContext) -> None:
        # The directory where the build files will be generated
        self.artifacts_locator = execution_context.create_artifacts_locator()
        self.cmake_build_dir = CMakePath(output_dir, "CMAKE_BUILD_DIR")
        self.cmake_project_dir = CMakePath(self.artifacts_locator.project_root_dir)
        self.cmake_variant_reports_dir = self.cmake_build_dir.joinpath("reports")
        self.compile_commands_file = self.cmake_build_dir.joinpath("compile_commands.json")
        self.variant_report_config = self.cmake_build_dir.joinpath("report_config.json")

    @property
    def project_root_dir(self) -> Path:
        return self.artifacts_locator.project_root_dir

    def get_component_build_dir(self, component_name: str) -> CMakePath:
        return self.cmake_build_dir.joinpath(component_name)

    def get_component_reports_dir(self, component_name: str) -> CMakePath:
        return self.get_component_build_dir(component_name).joinpath("reports")

    def get_build_artifact(self, artifact: ComponentBuildArtifact) -> CMakePath:
        return self.cmake_build_dir.joinpath(artifact.path)

    def get_component_build_artifact(self, component_name: str, artifact: ComponentBuildArtifact) -> CMakePath:
        return self.get_component_build_dir(component_name).joinpath(artifact.path)
