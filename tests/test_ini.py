# test_yanga_ini.py

from pathlib import Path

import pytest

from yanga.ini import YangaIni


@pytest.fixture
def ini_file(tmp_path: Path) -> Path:
    """Create a temporary INI file for testing."""
    ini_content = """
    [default]
    configuration_file_name = yanga_from_ini.yaml
    exclude_dirs = .git, .github, .vscode, build, .venv
    """
    ini_file_path = tmp_path / "yanga.ini"
    ini_file_path.write_text(ini_content)
    return ini_file_path


@pytest.fixture
def toml_file(tmp_path: Path) -> Path:
    """Create a temporary pyproject.toml file for testing."""
    toml_content = """
    [tool.yanga]
    configuration_file_name = "yanga_from_toml.yaml"
    exclude_dirs = [".git", ".github", ".vscode", "build", ".venv"]
    """
    toml_file_path = tmp_path / "pyproject.toml"
    toml_file_path.write_text(toml_content)
    return toml_file_path


def test_load_ini_config(ini_file: Path) -> None:
    """Test loading configuration from an INI file."""
    config = YangaIni.load_ini_config(ini_file)
    expected_config = {"configuration_file_name": "yanga_from_ini.yaml", "exclude_dirs": [".git", ".github", ".vscode", "build", ".venv"]}
    assert config == expected_config


def test_load_toml_config(toml_file: Path) -> None:
    """Test loading configuration from a TOML file."""
    config = YangaIni.load_toml_config(toml_file)
    expected_config = {"configuration_file_name": "yanga_from_toml.yaml", "exclude_dirs": [".git", ".github", ".vscode", "build", ".venv"]}
    assert config == expected_config


def test_from_toml_or_ini_only_ini(ini_file: Path, toml_file: Path) -> None:
    """Test instantiating YangaIni from only an INI file."""
    config = YangaIni.from_toml_or_ini(ini_file=ini_file, pyproject_toml=toml_file)
    assert config.configuration_file_name == "yanga_from_toml.yaml"


def test_from_toml_without_yanga_info(tmp_path: Path) -> None:
    toml_content = """
    [tool.pytest]
    configuration_file_name = "yanga_from_toml.yaml"
    """
    toml_file_path = tmp_path / "pyproject.toml"
    toml_file_path.write_text(toml_content)
    config = YangaIni.from_toml_or_ini(ini_file=None, pyproject_toml=toml_file_path)
    assert config.configuration_file_name is None
