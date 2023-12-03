import textwrap
from pathlib import Path

import pytest
from py_app_dev.core.exceptions import UserNotificationException

from yanga.project.config import StageConfig
from yanga.ybuild.pipeline import PipelineLoader
from yanga.ybuild.stages import YangaScoopInstall


def test__load_stage():
    result = PipelineLoader._load_stages("install", [StageConfig(stage="YangaScoopInstall")], Path("."))
    assert len(result) == 1
    assert result[0].group_name == "install"
    assert result[0]._class == YangaScoopInstall


def test__load_unknown_stage():
    with pytest.raises(UserNotificationException):
        PipelineLoader._load_stages("install", [StageConfig(stage="YangaIDontExist")], Path("."))


def test__loag_stage_from_file(tmp_path: Path) -> None:
    my_python_file = tmp_path / "my_python_file.py"
    my_python_file.write_text(
        textwrap.dedent(
            """\
            from typing import List
            from pathlib import Path
            from yanga.ybuild.pipeline import Stage
            class MyStage(Stage):
                def run(self) -> None:
                    pass
                def get_dependencies(self) -> List[Path]:
                    pass
                def get_outputs(self) -> List[Path]:
                    pass
            """
        )
    )
    result = PipelineLoader._load_stages("install", [StageConfig(stage="MyStage", file="my_python_file.py")], tmp_path)
    assert len(result) == 1
    assert result[0].group_name == "install"
    assert result[0]._class.__name__ == "MyStage"
