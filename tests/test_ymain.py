import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from yanga.ymain import app

runner = CliRunner()


@pytest.mark.skipif(sys.platform != "win32", reason="It requires scoop to be installed on windows")
def test_run(tmp_path: Path) -> None:
    project_dir = tmp_path.joinpath("mini")
    result = runner.invoke(
        app,
        ["init", "--project-dir", project_dir.as_posix()],
    )
    assert result.exit_code == 0
    result = runner.invoke(
        app,
        ["run", "--project-dir", project_dir.as_posix(), "--platform", "gtest", "--variant-name", "EnglishVariant"],
    )
    assert result.exit_code == 0
