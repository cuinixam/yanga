import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from yanga.ymain import app

runner = CliRunner()

EXE_SUFFIX = ".exe" if sys.platform == "win32" else ""


def test_run(mini_project: Path) -> None:
    # Build the project. The pipeline installs everything required (venv, build tools, west deps).
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

    variant_build_dir = mini_project.joinpath(".yanga/build/variants/EnglishVariant/gtest")
    artifacts = [
        # Variant build artifacts
        "reports/coverage/index.html",
        "reports/coverage/greeter/index.html",
        "report_config.json",
        "targets_data.json",
        # Component build artifacts
        # Greeter has tests, so coverage report + docs sources
        "greeter/reports/coverage/greeter/index.html",
        f"greeter/greeter{EXE_SUFFIX}",
        "greeter/greeter.c.md",
        "greeter/greeter_test.cc.md",
        # Main has no tests, so no coverage report but only docs sources
        "main/main.c.md",
    ]
    for artifact in artifacts:
        artifact_path = variant_build_dir.joinpath(artifact)
        assert artifact_path.exists(), f"Expected build artifact not found: {artifact_path.as_posix()}"


@pytest.mark.skipif(not Path("D:/ateliere/spledy").exists(), reason="Exploratory test. Not meant to be run in CI.")
@pytest.mark.parametrize("platform", ["arduino_uno_r3", "host_exe", "gtest"])
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
