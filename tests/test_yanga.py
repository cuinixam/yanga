import sys
from pathlib import Path

import pytest

from yanga.commands.build import BuildCommand, BuildCommandConfig
from yanga.commands.init import InitCommandConfig, YangaInit


@pytest.mark.skipif(
    sys.platform != "win32", reason="Only run this test on windows platform"
)
def test_yanga_mini(tmp_path: Path) -> None:
    project_dir = tmp_path.joinpath("mini")
    YangaInit(InitCommandConfig(project_dir=project_dir, mini=True)).run()
    assert project_dir.joinpath("yanga.yaml").exists()
    assert 0 == BuildCommand().do_run(BuildCommandConfig("GermanVariant", project_dir))
