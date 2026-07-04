import sys
from pathlib import Path

from yanga_core.commands.run import RunCommand, RunCommandConfig

EXE_SUFFIX = ".exe" if sys.platform == "win32" else ""


def test_yanga_mini(mini_project: Path) -> None:
    project_dir = mini_project
    # Build the project. The pipeline installs everything required (venv, build tools, west deps).
    run_cmd_config = RunCommandConfig(
        project_dir,
        "host_exe",
        "GermanVariant",
        build_type="Debug",
        not_interactive=True,
    )

    assert 0 == RunCommand().do_run(run_cmd_config)
    # Check for the build artifacts
    binary_exe = project_dir.joinpath(f".yanga/build/variants/GermanVariant/host_exe/Debug/GermanVariant{EXE_SUFFIX}")
    assert binary_exe.exists()
    # Incremental build shall not rebuild the project
    write_time = binary_exe.stat().st_mtime
    assert 0 == RunCommand().do_run(run_cmd_config)
    assert write_time == binary_exe.stat().st_mtime, "Binary file shall not be rebuilt"
