import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from py_app_dev.core.data_registry import DataRegistry

from tests.utils import this_repository_root_dir
from yanga.domain.artifacts import ProjectArtifactsLocator
from yanga.domain.components import Component
from yanga.domain.config import TestingConfiguration
from yanga.domain.execution_context import ExecutionContext
from yanga.kickstart.create import KickstartProject


@pytest.fixture
def locate_artifact():
    """Fixture to mock the locate_artifact method."""
    with patch(
        ProjectArtifactsLocator.__module__ + "." + ProjectArtifactsLocator.__name__ + ".locate_artifact",
        side_effect=lambda file, _: Path(file),
    ) as my_locate_artifact:
        yield my_locate_artifact


@pytest.fixture
def execution_context(locate_artifact: Mock, tmp_path: Path) -> ExecutionContext:
    assert locate_artifact, "Fixture locate_artifact is not explicitly used in this fixture, but is required by the fixture chain."
    env = Mock(spec=ExecutionContext)
    env.project_root_dir = tmp_path
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
    env.create_artifacts_locator.return_value = ProjectArtifactsLocator(tmp_path, "mock_variant", "mock_platform", "mock_build_type")
    env.data_registry = DataRegistry()
    return env


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"


@pytest.fixture
def get_test_data_path():
    """Fixture that returns a function to get test data file paths by name."""

    def _get_test_data_path(filename: str) -> Path:
        """Get path to a test data file by filename."""
        return Path(__file__).parent / "data" / filename

    return _get_test_data_path


@pytest.fixture
def mini_project(request: pytest.FixtureRequest) -> Generator[Path, None, None]:
    # Create temp directory in the repository to ensure same drive as yanga source
    # This avoids cross-drive path issues on Windows with Poetry
    test_name = request.node.name
    tests_dir = this_repository_root_dir() / "build" / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    project_dir = Path(tempfile.mkdtemp(prefix=f"{test_name}_", dir=tests_dir))

    try:
        # Create example project
        KickstartProject(project_dir).run()
        assert project_dir.joinpath("yanga.yaml").exists()

        # Replace the YANGA dependency in the pyproject.toml
        pyproject_toml = project_dir.joinpath("pyproject.toml")
        new_dependency = f"yanga @ file:///{this_repository_root_dir().as_posix()}"
        pyproject_toml.write_text(pyproject_toml.read_text().replace("yanga>=2,<3", new_dependency))

        assert '"yanga @ file:///' in pyproject_toml.read_text(), "Failed to set the local yanga dependency in the mini project."

        yield project_dir
    finally:
        # Cleanup: remove the test project directory
        if project_dir.exists():
            pass  # shutil.rmtree(project_dir, ignore_errors=True)
