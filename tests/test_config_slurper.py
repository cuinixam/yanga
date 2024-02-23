from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yanga.domain.config import YangaUserConfig
from yanga.domain.config_slurper import YangaConfigSlurper


@pytest.fixture
def mock_project_dir(tmp_path: Path) -> Path:
    """Creates a mock project directory with some sample 'yanga.yaml' files."""
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2/dir3").mkdir()

    (tmp_path / "yanga.yaml").write_text("root config")
    (tmp_path / "dir1/yanga.yaml").write_text("dir1 config")
    (tmp_path / "dir2/yanga.yaml").write_text("dir2 config")
    (tmp_path / "dir2/dir3/yanga.yaml").write_text("dir3 config")

    return tmp_path


def test_parse_config_files(mock_project_dir):
    slurper = YangaConfigSlurper(mock_project_dir)

    # Mock the YangaUserConfig.from_file to return mock configs
    mock_config = MagicMock(spec=YangaUserConfig)
    with patch.object(YangaUserConfig, "from_file", return_value=mock_config):
        configs = slurper.slurp()

        assert len(configs) == 4
        for config in configs:
            assert config == mock_config


def test_no_config_files(tmp_path):
    slurper = YangaConfigSlurper(tmp_path)

    configs = slurper.slurp()

    assert len(configs) == 0
