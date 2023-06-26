import runpy
from argparse import Namespace
from pathlib import Path
import sys

import pytest

from yanga.commands.init import YangaInit, YangaInitConfig


def test_config_from_namespace():
    my_dict = {"project_dir": "my/path"}
    namespace = Namespace(**my_dict)
    config = YangaInitConfig.from_namespace(namespace)
    assert config.project_dir == Path("my/path")


def test_create_project_from_template(tmp_path):
    out_dir = tmp_path / "out"
    YangaInit.create_project_from_template(out_dir)
    assert (out_dir / "build.ps1").exists()
    assert (out_dir / "build.py").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Only for Windows")
def test_build_py_script(tmp_path: Path) -> None:
    project_root_dir = tmp_path / "my_project"
    YangaInit.create_project_from_template(project_root_dir)
    build_script_path = project_root_dir / "build.py"

    # Execute the main function in the build.py script using runpy
    runpy.run_path(build_script_path.as_posix(), run_name="__test_main__")

    assert (project_root_dir / ".venv").exists()
    assert (project_root_dir / "poetry.lock").exists()
