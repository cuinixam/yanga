import runpy
from argparse import Namespace
from pathlib import Path

import pytest

from yanga.commands.init import InitCommandConfig, YangaInit
from yanga.core.exceptions import UserNotificationException


def test_config_from_namespace():
    my_dict = {"project_dir": "my/path"}
    namespace = Namespace(**my_dict)
    config = InitCommandConfig.from_namespace(namespace)
    assert config.project_dir == Path("my/path")


def test_create_project_from_template(tmp_path):
    out_dir = tmp_path / "out"
    YangaInit.create_project_from_template(out_dir)
    assert (out_dir / "bootstrap.ps1").exists()
    assert (out_dir / "build.py").exists()


def test_create_project_fails_if_out_is_not_empty(tmp_path: Path) -> None:
    tmp_path.joinpath("some_file.txt").write_text("some content")
    with pytest.raises(UserNotificationException):
        YangaInit.create_project_from_template(tmp_path)


def test_build_py_script(tmp_path: Path) -> None:
    project_root_dir = tmp_path / "my_project"
    YangaInit.create_project_from_template(project_root_dir)
    build_script_path = project_root_dir / "build.py"

    # Execute the main function in the build.py script using runpy
    runpy.run_path(build_script_path.as_posix(), run_name="__test_main__")

    assert (project_root_dir / ".venv").exists()
    assert (project_root_dir / "poetry.lock").exists()
