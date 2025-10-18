from pathlib import Path

import pytest
from py_app_dev.core.subprocess import SubprocessExecutor
from typer.testing import CliRunner

from yanga.ymain import app

runner = CliRunner()


@pytest.mark.skip(reason="TODO: integration tests fail on windows")
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
        ["run", "--project-dir", project_dir.as_posix(), "--platform", "gtest", "--variant", "EnglishVariant"],
    )
    assert result.exit_code == 0


@pytest.mark.skipif(not Path("D:/ateliere/spledy").exists(), reason="Exploratory test. Not meant to be run in CI.")
@pytest.mark.parametrize("platform", ["arduino_uno_r3", "win_exe", "gtest"])
def test_spled(platform: str) -> None:
    project_dir = Path("D:/ateliere/spledy")
    result = runner.invoke(
        app,
        [
            "run",
            "--project-dir",
            project_dir.as_posix(),
            "--variant",
            "Disco",
            "--platform",
            platform,
            "--target",
            "all",
            "--force-run",
            "--not-interactive",
        ],
    )
    assert result.exit_code == 0
