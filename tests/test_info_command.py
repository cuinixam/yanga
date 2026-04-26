import json
from pathlib import Path

from typer.testing import CliRunner

from yanga.kickstart.create import KickstartProject
from yanga.ymain import app

runner = CliRunner()


def test_info_stdout(tmp_path: Path) -> None:
    KickstartProject(project_dir=tmp_path).run()
    result = runner.invoke(app, ["info", "--project-dir", tmp_path.as_posix()])
    assert result.exit_code == 0
    info = json.loads(result.output)
    assert info["schema_version"] == 1
    assert "variants" in info
    assert "platforms" in info
    assert "components" in info


def test_info_output_file(tmp_path: Path) -> None:
    KickstartProject(project_dir=tmp_path).run()
    output_file = tmp_path / "out" / "project.json"
    result = runner.invoke(app, ["info", "--project-dir", tmp_path.as_posix(), "--output", str(output_file)])
    assert result.exit_code == 0
    assert output_file.exists()
    info = json.loads(output_file.read_text())
    assert info["schema_version"] == 1
