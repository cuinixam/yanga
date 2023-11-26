import sys
from pathlib import Path

import pytest
from py_app_dev.core.subprocess import SubprocessExecutor

from yanga.commands.build import BuildCommand, BuildCommandConfig
from yanga.commands.init import InitCommandConfig, YangaInit
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.stages import YangaScoopInstall


@pytest.mark.skipif(
    sys.platform != "win32", reason="It requires scoop to be installed on windows"
)
def test_yanga_mini(tmp_path: Path) -> None:
    project_dir = tmp_path.joinpath("mini")
    # Create a mini project
    YangaInit(InitCommandConfig(project_dir=project_dir, mini=True)).run()
    assert project_dir.joinpath("yanga.yaml").exists()
    build_script_path = project_dir / "bootstrap.ps1"
    assert build_script_path.exists()
    # Bootstrap the project
    SubprocessExecutor(["powershell", "-File", build_script_path.as_posix()]).execute()
    # Build the project
    assert 0 == BuildCommand().do_run(BuildCommandConfig("GermanVariant", project_dir))
    # Check for the build artifacts
    binary_exe = project_dir.joinpath("build/GermanVariant/build/GermanVariant.exe")
    assert binary_exe.exists()
    # Incremental build shall not rebuild the project
    write_time = binary_exe.stat().st_mtime
    assert 0 == BuildCommand().do_run(BuildCommandConfig("GermanVariant", project_dir))
    assert write_time == binary_exe.stat().st_mtime, "Binary file was rebuilt"


@pytest.mark.skipif(
    sys.platform != "win32", reason="It requires scoop to be installed on windows"
)
def test_yanga_scoop_install_stage(tmp_path: Path) -> None:
    project_dir = tmp_path.joinpath("mini")
    # Create a mini project
    YangaInit(InitCommandConfig(project_dir=project_dir, mini=True)).run()
    build_env = BuildEnvironment("some name", project_dir)
    stage = YangaScoopInstall(build_env, "test")
    stage.run()
    assert len(build_env.install_dirs) == 2
