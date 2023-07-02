from yanga.ybuild.config import StageConfig
from yanga.ybuild.pipeline import PipelineLoader
from yanga.ybuild.stages import YangaInstall


def test__load_stage():
    result = PipelineLoader._load_stages("install", [StageConfig(stage="YangaInstall")])
    assert len(result) == 1
    assert result[0].group_name == "install"
    assert result[0]._class == YangaInstall
