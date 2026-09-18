import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner
from yanga_core.commands.features import FeaturesCommand, FeaturesCommandConfig

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


@pytest.mark.parametrize(
    ("args", "variant_name", "platform", "gui"),
    [
        ([], None, None, True),
        (["--variant", "GermanVariant", "--no-gui"], "GermanVariant", None, False),
        (["--variant", "GermanVariant", "--platform", "gtest"], "GermanVariant", "gtest", True),
    ],
    ids=["all-variants", "variant-terminal", "variant-and-platform"],
)
def test_features_runs_the_features_command(tmp_path: Path, args: list[str], variant_name: str | None, platform: str | None, gui: bool) -> None:
    with patch("yanga.ymain._check_tkinter_available"), patch.object(FeaturesCommand, "do_run", return_value=0) as do_run:
        result = runner.invoke(app, ["features", "--project-dir", tmp_path.as_posix(), *args])

    assert result.exit_code == 0
    do_run.assert_called_once_with(FeaturesCommandConfig(tmp_path, variant_name=variant_name, platform=platform, gui=gui))
