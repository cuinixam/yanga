from pathlib import Path

import pytest
from py_app_dev.core.exceptions import UserNotificationException

from yanga.kickstart.create import KickstartProject


def test_create_project_from_template(tmp_path):
    out_dir = tmp_path / "out"
    KickstartProject(project_dir=out_dir).run()
    files = ["bootstrap.ps1", "yanga.yaml", "main.c", "greeter.c"]
    for file in files:
        assert (out_dir / file).exists()


def test_create_project_fails_if_out_is_not_empty(tmp_path: Path) -> None:
    tmp_path.joinpath("some_file.txt").write_text("some content")
    with pytest.raises(UserNotificationException):
        KickstartProject(tmp_path).run()
    KickstartProject(tmp_path, force=True).run()
    assert tmp_path.joinpath("bootstrap.ps1").exists()
