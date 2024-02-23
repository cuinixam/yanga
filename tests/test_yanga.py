import sys
from pathlib import Path

import pytest
from py_app_dev.core.subprocess import SubprocessExecutor

from yanga.commands.init import InitCommandConfig, YangaInit
from yanga.commands.run import RunCommand, RunCommandConfig
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest
from yanga.steps.scoop_install import ScoopInstall


@pytest.mark.skipif(sys.platform != "win32", reason="It requires scoop to be installed on windows")
def test_yanga_mini(tmp_path: Path) -> None:
    project_dir = tmp_path.joinpath("mini")
    # Create example project
    YangaInit(InitCommandConfig(project_dir=project_dir)).run()
    assert project_dir.joinpath("yanga.yaml").exists()
    build_script_path = project_dir / "bootstrap.ps1"
    assert build_script_path.exists()
    # Bootstrap the project
    SubprocessExecutor(["powershell", "-File", build_script_path.as_posix()]).execute()
    # Build the project
    assert 0 == RunCommand().do_run(RunCommandConfig(project_dir, "GermanVariant"))
    # Check for the build artifacts
    binary_exe = project_dir.joinpath("build/GermanVariant/build/GermanVariant.exe")
    assert binary_exe.exists()
    # Incremental build shall not rebuild the project
    write_time = binary_exe.stat().st_mtime
    assert 0 == RunCommand().do_run(RunCommandConfig(project_dir, "GermanVariant"))
    assert write_time == binary_exe.stat().st_mtime, "Binary file was rebuilt"


@pytest.mark.skipif(sys.platform != "win32", reason="It requires scoop to be installed on windows")
def test_yanga_scoop_install_stage(tmp_path: Path) -> None:
    project_dir = tmp_path.joinpath("mini")
    # Create example project
    YangaInit(InitCommandConfig(project_dir=project_dir)).run()
    exec_context = ExecutionContext(project_dir, "my_variant", UserVariantRequest("my_variant"))
    stage = ScoopInstall(exec_context, tmp_path / "output_scoop")
    stage.run()
    assert len(exec_context.install_dirs) == 2
