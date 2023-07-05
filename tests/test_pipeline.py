import pytest

from yanga.core.exceptions import UserNotificationException
from yanga.ybuild.config import StageConfig
from yanga.ybuild.pipeline import PipelineLoader
from yanga.ybuild.stages import YangaScoopInstall


def test__load_stage():
    result = PipelineLoader._load_stages(
        "install", [StageConfig(stage="YangaScoopInstall")]
    )
    assert len(result) == 1
    assert result[0].group_name == "install"
    assert result[0]._class == YangaScoopInstall


def test__load_unknown_stage():
    with pytest.raises(UserNotificationException):
        PipelineLoader._load_stages("install", [StageConfig(stage="YangaIDontExist")])
