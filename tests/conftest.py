from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from yanga.domain.artifacts import ProjectArtifactsLocator
from yanga.domain.components import Component
from yanga.domain.config import TestingConfiguration
from yanga.domain.execution_context import ExecutionContext


@pytest.fixture
def locate_artifact():
    """Fixture to mock the locate_artifact method."""
    with patch(
        ProjectArtifactsLocator.__module__ + "." + ProjectArtifactsLocator.__name__ + ".locate_artifact",
        side_effect=lambda file, _: Path(file),
    ) as my_locate_artifact:
        yield my_locate_artifact


@pytest.fixture
def execution_context(locate_artifact: Mock) -> ExecutionContext:
    assert locate_artifact, "Fixture locate_artifact is not explicitly used in this fixture, but is required by the fixture chain."
    env = Mock(spec=ExecutionContext)
    env.variant_name = "mock_variant"
    env.components = [
        Component(
            name="CompA",
            path=Path("compA"),
            sources=["compA_source.cpp"],
            testing=TestingConfiguration(sources=["test_compA_source.cpp"]),
        ),
        Component(
            name="CompBNotTestable",
            path=Path("compB"),
            sources=["compB_source.cpp"],
            testing=TestingConfiguration(sources=[]),
        ),
    ]
    env.include_directories = [Path("/mock/include/dir")]
    env.create_artifacts_locator.return_value = ProjectArtifactsLocator(Path("/mock/project/root"), "mock_variant", "mock_platform", "mock_build_type")
    return env


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"
