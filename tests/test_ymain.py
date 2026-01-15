import os
import sys
from pathlib import Path

import pytest
from py_app_dev.core.subprocess import SubprocessExecutor
from typer.testing import CliRunner

from yanga.ymain import app

runner = CliRunner()


@pytest.mark.skipif(sys.platform != "win32", reason="It requires scoop to be installed on windows")
def test_run(mini_project: Path) -> None:
    build_script_path = mini_project / "build.ps1"
    assert build_script_path.exists()
    # Bootstrap the project
    SubprocessExecutor(["powershell", "-File", build_script_path.as_posix(), "-install"]).execute()
    # "Refresh" the PATH to make sure the Scoop shims are available
    os.environ["PATH"] += os.pathsep + str(Path.home() / "scoop" / "shims")
    # Build the project
    result = runner.invoke(
        app,
        [
            "run",
            "--project-dir",
            mini_project.as_posix(),
            "--platform",
            "gtest",
            "--variant",
            "EnglishVariant",
            "--target",
            "report",
            "--not-interactive",
        ],
    )
    assert result.exit_code == 0

    variant_build_dir = mini_project.joinpath(".yanga/build/EnglishVariant/gtest")
    artifacts = [
        # Variant build artifacts
        "reports/coverage/index.html",
        "reports/coverage/greeter/index.html",
        "report_config.json",
        "targets_data.json",
        # Component build artifacts
        # Greeter has tests, so coverage report + cppcheck + docs sources
        "greeter/reports/coverage/greeter/index.html",
        "greeter/greeter.exe",
        "greeter/cppcheck_report.md",
        "greeter/greeter.c.md",
        "greeter/greeter_test.cc.md",
        # Main has no tests, so no coverage report but only cppcheck and docs sources
        "main/main.c.md",
        "main/cppcheck_report.md",
    ]
    for artifact in artifacts:
        artifact_path = variant_build_dir.joinpath(artifact)
        assert artifact_path.exists(), f"Expected build artifact not found: {artifact_path.as_posix()}"


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
