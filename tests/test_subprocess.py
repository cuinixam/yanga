from pathlib import Path
from unittest.mock import Mock, patch

from yanga.core.subprocess import SubprocessExecutor, get_app_path


def test_get_app_path():
    assert get_app_path("python")


def test_subprocess_executor():
    def mock_run(*args, **kwargs):
        assert args[0] == "python -V"
        assert kwargs["cwd"] == "my/path"
        return Mock()

    with patch("subprocess.run", mock_run):
        SubprocessExecutor(["python", "-V"], cwd=Path("my/path")).execute()
