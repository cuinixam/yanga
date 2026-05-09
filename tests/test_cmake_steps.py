from pathlib import Path
from unittest.mock import Mock

import pytest
from yanga_core.domain.execution_context import ExecutionContext

from yanga.cmake.steps import GenerateBuildSystemFiles


@pytest.fixture
def env(tmp_path: Path) -> ExecutionContext:
    env = Mock(spec=ExecutionContext)
    env.project_root_dir = tmp_path
    env.spl_paths = Mock()
    env.spl_paths.variant_build_dir = tmp_path / "build"
    env.user_config_files = [tmp_path / "yanga.yaml"]
    return env


def test_generate_build_system_files_always_runs(env: ExecutionContext) -> None:
    """
    Regression: pypeline cannot detect generator-code changes via file hashes.

    Returning empty inputs/outputs makes the runnable framework report NOTHING_TO_CHECK,
    so the step always runs. Without this, a yanga upgrade leaves ``variant.cmake`` stale
    on disk because user yaml is unchanged, which breaks freshly-added cmake targets like
    ``<comp>_clean``.
    """
    step = GenerateBuildSystemFiles(env)

    assert step.get_inputs() == []
    assert step.get_outputs() == []
