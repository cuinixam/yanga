from pathlib import Path

import pytest
from py_app_dev.core.subprocess import SubprocessExecutor
from typer.testing import CliRunner

from yanga.ymain import app

runner = CliRunner()


@pytest.mark.skip(reason="TODO: integration tests fail of windows")
def test_run(tmp_path: Path) -> None:
    project_dir = tmp_path.joinpath("mini")
    result = runner.invoke(
        app,
        ["init", "--project-dir", project_dir.as_posix()],
    )
    assert result.exit_code == 0
    build_script_path = project_dir / "bootstrap.ps1"
    assert build_script_path.exists()
    # Bootstrap the project
    SubprocessExecutor(["powershell", "-File", build_script_path.as_posix()]).execute()
    # Build the project
    result = runner.invoke(
        app,
        ["run", "--project-dir", project_dir.as_posix(), "--platform", "gtest", "--variant-name", "EnglishVariant"],
    )
    assert result.exit_code == 0
