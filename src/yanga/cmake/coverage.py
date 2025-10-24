from dataclasses import dataclass
from pathlib import Path

from yanga.domain.artifacts import ProjectArtifactsLocator
from yanga.domain.execution_context import UserRequest

from .artifacts_locator import CMakeArtifactsLocator
from .cmake_backend import CMakePath


@dataclass
class CoverageRelevantFile:
    """Used to register files relevant for the merged coverage report."""

    target: UserRequest
    json_report: CMakePath


class CoverageArtifactsLocator(CMakeArtifactsLocator):
    def __init__(self, output_dir: Path, project_artifact_locator: ProjectArtifactsLocator) -> None:
        super().__init__(output_dir, project_artifact_locator)

    @classmethod
    def from_cmake_artifacts_locator(cls, cmake_artifacts_locator: CMakeArtifactsLocator) -> "CoverageArtifactsLocator":
        return cls(cmake_artifacts_locator.cmake_build_dir.to_path(), cmake_artifacts_locator.artifacts_locator)

    def _get_component_coverage_reports_relative_dir(self, component_name: str) -> str:
        # (!) We need to keep the component coverage reports relative path to the `reports` dir identical for both the component and variant reports
        # E.g., reports/coverage/<component_name>
        # This is because we copy the component report into the variant report dir maintaining the relative structure.
        return f"coverage/{component_name}"

    def get_component_coverage_reports_dir(self, component_name: str) -> CMakePath:
        """Path inside the component reports dir where the coverage report is located."""
        return self.get_component_reports_dir(component_name).joinpath(self._get_component_coverage_reports_relative_dir(component_name))

    def get_component_variant_coverage_reports_dir(self, component_name: str) -> CMakePath:
        """Path inside the variant reports dir where the component coverage report shall be located."""
        return self.cmake_variant_reports_dir.joinpath(self._get_component_coverage_reports_relative_dir(component_name))

    def get_component_coverage_html_file(self, component_name: str) -> CMakePath:
        return self.get_component_coverage_reports_dir(component_name).joinpath("index.html")

    def get_variant_coverage_reports_dir(self) -> CMakePath:
        return self.cmake_variant_reports_dir.joinpath("coverage")

    def get_variant_coverage_html_file(self) -> CMakePath:
        return self.get_variant_coverage_reports_dir().joinpath("index.html")
