from dataclasses import dataclass
from pathlib import Path

from yanga.domain.artifacts import ProjectArtifactsLocator
from yanga.domain.execution_context import UserRequest

from .artifacts_locator import BuildArtifact, CMakeArtifactsLocator
from .cmake_backend import CMakePath


@dataclass
class CoverageRelevantFile:
    """Used to register files relevant for the merged coverage report."""

    target: UserRequest
    json_report: CMakePath


class CoverageArtifactsLocator(CMakeArtifactsLocator):
    def __init__(self, output_dir: Path, project_artifact_locator: ProjectArtifactsLocator) -> None:
        super().__init__(output_dir, project_artifact_locator)
        self.coverage_reports_dir = self.cmake_variant_reports_dir.joinpath("coverage")

    @classmethod
    def from_cmake_artifacts_locator(cls, cmake_artifacts_locator: CMakeArtifactsLocator) -> "CoverageArtifactsLocator":
        return cls(cmake_artifacts_locator.cmake_build_dir.to_path(), cmake_artifacts_locator.artifacts_locator)

    def get_component_coverage_html_dir(self, component_name: str) -> CMakePath:
        coverage_doc_file = self.get_component_build_artifact(component_name, BuildArtifact.COVERAGE_DOC)
        # We need to generate the html report in a subdirectory to be able to link it relatively from the markdown file
        coverage_doc_file_relative_path = coverage_doc_file.to_path().relative_to(self.artifacts_locator.project_root_dir).parent.as_posix()
        return self.get_component_reports_dir(component_name).joinpath(coverage_doc_file_relative_path).joinpath("coverage")
