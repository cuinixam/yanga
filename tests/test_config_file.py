from pathlib import Path

import pytest

from yanga.domain.config import ConfigFile


def test_config_file_with_file_path() -> None:
    config = ConfigFile(id="west", file=Path("west.yaml"))
    assert config.id == "west"
    assert config.file == Path("west.yaml")
    assert config.content is None


def test_config_file_with_content() -> None:
    content: dict[str, list[str]] = {"remotes": [], "projects": []}
    config = ConfigFile(id="west", content=content)
    assert config.id == "west"
    assert config.file is None
    assert config.content == content


def test_config_file_with_both_file_and_content() -> None:
    content: dict[str, list[str]] = {"remotes": [], "projects": []}
    config = ConfigFile(id="west", file=Path("west.yaml"), content=content)
    assert config.id == "west"
    assert config.file == Path("west.yaml")
    assert config.content == content


def test_config_file_missing_both_raises() -> None:
    with pytest.raises(ValueError, match="must have either 'file' or 'content'"):
        ConfigFile(id="west")
