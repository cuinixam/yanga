import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from yanga.core.exceptions import UserNotificationException
from yanga.core.scoop_wrapper import ScoopInstallConfigFile, ScoopWrapper


def test_scoop_installed():
    """Patch the get_app_path function to return a valid path to scoop.exe.
    Then test that ScoopWrapper.get_scoop_path returns the same path.
    """
    with patch(
        "yanga.core.scoop_wrapper.get_app_path", return_value=Path("c:/scoop/scoop.exe")
    ):
        scoop_wrapper = ScoopWrapper()
        assert scoop_wrapper.get_scoop_path() == Path("c:/scoop/scoop.exe")


def test_scoop_is_not_installed():
    """Patch the get_app_path function to return None.
    Then test that ScoopWrapper.get_scoop_path raises a UserNotificationException.
    """
    with patch("yanga.core.scoop_wrapper.get_app_path", return_value=None):
        with pytest.raises(UserNotificationException):
            ScoopWrapper()


@pytest.fixture
def scoop_dir(tmp_path: Path) -> Path:
    # Create a temporary directory structure for testing
    apps_dir = tmp_path / "apps"
    # Create fake apps and manifest files
    manifest = apps_dir / "app1" / "1.0" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"version": "1.0", "bin": ["bin/program1.exe", "program2.exe"]})
    )
    manifest = apps_dir / "app1" / "2.0" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {"version": "2.0", "bin": [["app/program3.exe", "alias"], "program4.exe"]}
        )
    )

    manifest = apps_dir / "app2" / "3.1.1" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"version": "3.1.1", "bin": "program5.exe"}))

    return tmp_path


def test_get_installed_tools(scoop_dir: Path) -> None:
    # Patch get_app_path to return the scoop directory
    with patch("yanga.core.scoop_wrapper.get_app_path", return_value=scoop_dir):
        scoop_wrapper = ScoopWrapper()

    # Get the installed tools
    installed_tools = scoop_wrapper.get_installed_apps()

    # Additional assertions based on your requirements or expectations
    assert len(installed_tools) == 3
    apps_dir = scoop_dir.joinpath("apps")

    # Check the details of individual tools
    tool1 = installed_tools[0]
    assert tool1.name == "app1"
    assert tool1.version == "1.0"
    assert tool1.path == apps_dir.joinpath("app1/1.0")
    assert tool1.manifest_file == tool1.path / "manifest.json"
    assert tool1.bin_dirs == [Path("bin")]

    tool2 = installed_tools[1]
    assert tool2.name == "app1"
    assert tool2.version == "2.0"
    assert tool2.path == apps_dir.joinpath("app1/2.0")
    assert tool2.manifest_file == tool2.path / "manifest.json"
    assert tool2.bin_dirs == [Path("app")]

    tool3 = installed_tools[2]
    assert tool3.name == "app2"
    assert tool3.version == "3.1.1"
    assert tool3.path == apps_dir.joinpath("app2/3.1.1")
    assert tool3.manifest_file == tool3.path / "manifest.json"
    assert tool3.bin_dirs == []


def test_install(scoop_dir: Path, tmp_path: Path) -> None:
    # Patch get_app_path to return the scoop directory
    with patch("yanga.core.scoop_wrapper.get_app_path", return_value=scoop_dir):
        scoop_wrapper = ScoopWrapper()

    scoop_file = tmp_path / "scoopfile.json"
    scoop_file.write_text(
        """{
        "buckets": [],
        "apps": [
            {
                "Source": "versions",
                "Name": "app1"
            },
            {
                "Source": "main",
                "Name": "app3"
            }
        ]
    }"""
    )
    with patch("subprocess.run", Mock()):
        assert len(scoop_wrapper.install(scoop_file)) == 1


def test_nothing_to_install(scoop_dir: Path, tmp_path: Path) -> None:
    # Patch get_app_path to return the scoop directory
    with patch("yanga.core.scoop_wrapper.get_app_path", return_value=scoop_dir):
        scoop_wrapper = ScoopWrapper()

    scoop_file = tmp_path / "scoopfile.json"
    scoop_file.write_text(
        """{
        "buckets": [],
        "apps": [
            {
                "Source": "versions",
                "Name": "app1"
            },
            {
                "Source": "main",
                "Name": "app2"
            }
        ]
    }"""
    )
    assert scoop_wrapper.install(scoop_file) == []


def test_scoop_file(tmp_path: Path) -> None:
    scoop_file = tmp_path / "scoopfile.json"
    scoop_file.write_text(
        """
    {
        "buckets": [
            {
                "Name": "main",
                "Source": "https://github.com/ScoopInstaller/main"
            },
            {
                "Name": "versions",
                "Source": "https://github.com/ScoopInstaller/Versions"
            }
        ],
        "apps": [
            {
                "Source": "versions",
                "Name": "python311"
            },
            {
                "Source": "main",
                "Name": "python"
            }
        ]
    }
    """
    )
    scoop_deps = ScoopInstallConfigFile.from_file(scoop_file)
    assert scoop_deps.bucket_names == ["main", "versions"]
    assert scoop_deps.app_names == ["python311", "python"]
