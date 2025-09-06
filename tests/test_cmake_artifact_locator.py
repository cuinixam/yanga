from pathlib import Path

from yanga.cmake.artifacts_locator import BuildArtifact, CMakeArtifactsLocator
from yanga.domain.execution_context import ExecutionContext


def test_component_build_artifacts(tmp_path: Path, execution_context: ExecutionContext) -> None:
    artifacts_locator = CMakeArtifactsLocator(tmp_path, execution_context)
    assert artifacts_locator.project_root_dir == execution_context.project_root_dir
    assert artifacts_locator.get_component_build_artifact("CompA", BuildArtifact.REPORT_CONFIG).to_path() == tmp_path / "CompA" / "report_config.json"
