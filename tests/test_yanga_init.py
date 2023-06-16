from argparse import Namespace
from pathlib import Path

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
