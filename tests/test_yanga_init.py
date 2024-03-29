import runpy
from pathlib import Path

import pytest
from py_app_dev.core.exceptions import UserNotificationException

from yanga.commands.init import ProjectBuilder, YangaInit


def test_create_project_from_template(tmp_path):
    out_dir = tmp_path / "out"
    YangaInit(project_dir=out_dir).run()
    files = ["bootstrap.ps1", "bootstrap.py", "bootstrap.json", "main.c", "yanga.yaml"]
    for file in files:
        assert (out_dir / file).exists()


def test_create_project_fails_if_out_is_not_empty(tmp_path: Path) -> None:
    tmp_path.joinpath("some_file.txt").write_text("some content")
    with pytest.raises(UserNotificationException):
        ProjectBuilder(tmp_path).build()


def test_build_py_script(tmp_path: Path) -> None:
    project_dir = tmp_path / "my_project"
    YangaInit(project_dir=project_dir).run()
    build_script_path = project_dir / "bootstrap.py"

    # Execute the main function in the bootstrap.py script using runpy
    runpy.run_path(build_script_path.as_posix(), run_name="__test_main__")

    assert (project_dir / ".venv").exists()
    assert (project_dir / "poetry.lock").exists()
