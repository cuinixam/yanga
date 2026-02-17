import os
import sys
from pathlib import Path

import pytest
from py_app_dev.core.subprocess import SubprocessExecutor

from yanga.commands.run import RunCommand, RunCommandConfig


@pytest.mark.skipif(sys.platform != "win32", reason="It requires scoop to be installed on windows")
def test_yanga_mini(mini_project: Path) -> None:
    project_dir = mini_project
    build_script_path = project_dir / "build.ps1"
    assert build_script_path.exists()
    # Bootstrap the project
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    completed_process = SubprocessExecutor(["powershell", "-File", build_script_path.as_posix(), "-install"], env=env).execute(handle_errors=False)

    assert completed_process is not None
    assert completed_process.returncode == 0, "Bootstrapping the project failed."
    # "Refresh" the PATH to make sure the Scoop shims are available
    os.environ["PATH"] += os.pathsep + str(Path.home() / "scoop" / "shims")
    # Build the project
    run_cmd_config = RunCommandConfig(
        project_dir,
        "host_exe",
        "GermanVariant",
        build_type="Debug",
        not_interactive=True,
    )

    assert 0 == RunCommand().do_run(run_cmd_config)
    # Check for the build artifacts
    binary_exe = project_dir.joinpath(".yanga/build/GermanVariant/host_exe/Debug/GermanVariant.exe")
    assert binary_exe.exists()
    # Incremental build shall not rebuild the project
    write_time = binary_exe.stat().st_mtime
    assert 0 == RunCommand().do_run(run_cmd_config)
    assert write_time == binary_exe.stat().st_mtime, "Binary file shall not be rebuilt"
