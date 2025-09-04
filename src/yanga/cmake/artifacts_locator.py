from pathlib import Path

from yanga.cmake.cmake_backend import CMakePath
from yanga.domain.execution_context import ExecutionContext


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

    def get_component_compile_commands(self, component_name: str) -> CMakePath:
        return self.get_component_build_dir(component_name).joinpath("component_compile_commands.json")

    def get_component_report_config(self, component_name: str) -> CMakePath:
        return self.get_component_build_dir(component_name).joinpath("report_config.json")
