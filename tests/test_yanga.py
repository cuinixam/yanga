from pathlib import Path

import pytest
from py_app_dev.core.subprocess import SubprocessExecutor
from pypeline.steps.scoop_install import ScoopInstall

from yanga.commands.run import RunCommand, RunCommandConfig
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest
from yanga.kickstart.create import KickstartProject


@pytest.fixture
def mini_project(tmp_path: Path) -> Path:
    project_dir = tmp_path.joinpath("mini")
    # Create example project
    KickstartProject(project_dir).run()
    assert project_dir.joinpath("yanga.yaml").exists()
    return project_dir


@pytest.mark.skip(reason="TODO: integration tests fail of windows")
def test_yanga_mini(mini_project: Path) -> None:
    project_dir = mini_project
    build_script_path = project_dir / "bootstrap.ps1"
    assert build_script_path.exists()
    # Bootstrap the project
    SubprocessExecutor(["powershell", "-File", build_script_path.as_posix()]).execute()
    # Build the project
    assert 0 == RunCommand().do_run(RunCommandConfig(project_dir, "win_exe", "GermanVariant"))
    # Check for the build artifacts
    binary_exe = project_dir.joinpath("build/GermanVariant/win_exe/GermanVariant.exe")
    assert binary_exe.exists()
    # Incremental build shall not rebuild the project
    write_time = binary_exe.stat().st_mtime
    assert 0 == RunCommand().do_run(RunCommandConfig(project_dir, "win_exe", "GermanVariant"))
    assert write_time == binary_exe.stat().st_mtime, "Binary file was rebuilt"


@pytest.mark.skip(reason="TODO: integration tests fail of windows")
def test_yanga_scoop_install_stage(mini_project: Path) -> None:
    project_dir = mini_project
    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="my_variant", user_request=UserVariantRequest("my_variant"))
    # Create directory to store the step dependency file
    project_dir.joinpath("build/install").mkdir(parents=True, exist_ok=True)
    step = ScoopInstall(exec_context, "install")
    # Run the scoop install step
    step.run()
    step.update_execution_context()
    assert len(exec_context.install_dirs) == 1
