import textwrap
from pathlib import Path
from unittest.mock import Mock, patch

from yanga.ybuild.build_main import YangaBuild
from yanga.ybuild.stages import YangaInstall


def test_build(tmp_path: Path) -> None:
    # Create the config file
    config_file = tmp_path / "yanga.yaml"
    config_file.write_text(
        textwrap.dedent(
            """\
    pipeline:
        install:
            - stage: YangaInstall
    """
        )
    )
    # Mock the BuildEnvironment
    environment = Mock()
    environment.artifacts_locator = artifacts_locator = Mock()
    artifacts_locator.config_file = config_file
    artifacts_locator.project_root_dir = tmp_path
    # Run the build
    with patch(
        YangaInstall.__module__ + "." + YangaInstall.__name__, autospec=True
    ) as mock_yanga_install:
        mock_instance = mock_yanga_install.return_value
        # Run the build
        YangaBuild(environment).run()
        # Check that the YangaInstall run method was called
        mock_instance.run.assert_called_once()
