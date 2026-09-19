from pathlib import Path
from unittest.mock import Mock

import pytest
from py_app_dev.core.data_registry import DataRegistry
from py_app_dev.core.exceptions import UserNotificationException
from pypeline.domain.external_project import ExternalProject
from yanga_core.domain.execution_context import ExecutionContext

from yanga.zephyr.steps import KCONFIG_FRONTEND, ZephyrBuild


@pytest.fixture
def env(tmp_path: Path) -> ExecutionContext:
    env = Mock(spec=ExecutionContext)
    env.project_root_dir = tmp_path
    env.variant_name = "Disco"
    env.platform = Mock()
    env.platform.name = "zephyr_sim"
    env.spl_paths = Mock()
    env.spl_paths.variant_build_dir = tmp_path / "build"
    env.user_request = Mock()
    env.user_request.target = None
    env.variant_platform_feature_selection_file = None
    env.install_dirs = []
    env.data_registry = DataRegistry()
    env.data_registry.insert(ExternalProject(name="zephyr", path=tmp_path / "zephyr", revision="v4.4.0"), "test")
    return env


CONFIG = {"board": "native_sim/native/64", "toolchain": "host", "kconfig_root": "platforms/zephyr/KConfig"}


def test_cmake_args_use_configured_paths(env: ExecutionContext) -> None:
    step = ZephyrBuild(env, "build", {**CONFIG, "app_config_dir": "platforms/zephyr/app", "source_dir": "platforms/zephyr"})
    command = step.west_build_command("all")
    args = step.get_cmake_args()

    assert command[:6] == ["west", "build", "-b", "native_sim/native/64", "-d", (env.project_root_dir / "build").as_posix()]
    assert command[6] == (env.project_root_dir / "platforms/zephyr").as_posix()
    assert f"-DKCONFIG_ROOT={(env.project_root_dir / 'platforms/zephyr/KConfig').as_posix()}" in args
    assert f"-DAPPLICATION_CONFIG_DIR={(env.project_root_dir / 'platforms/zephyr/app').as_posix()}" in args
    assert f"-DEXTRA_KCONFIG_TARGET_COMMAND_FOR_platform_features={KCONFIG_FRONTEND.as_posix()}" in args
    assert "-DEXTRA_CONF_FILE" not in " ".join(args)


def test_paths_default_to_project_root(env: ExecutionContext) -> None:
    step = ZephyrBuild(env, "build", CONFIG)

    assert step.west_build_command("all")[6] == env.project_root_dir.as_posix()
    assert f"-DAPPLICATION_CONFIG_DIR={env.project_root_dir.as_posix()}" in step.get_cmake_args()


def test_missing_kconfig_root_is_a_user_error(env: ExecutionContext) -> None:
    with pytest.raises(UserNotificationException, match="kconfig_root"):
        ZephyrBuild(env, "build", {"board": "native_sim/native/64", "toolchain": "host"})


@pytest.mark.parametrize(
    ("target", "expected_tail"),
    [("all", []), ("report", ["-t", "report"])],
)
def test_build_target_is_passed_to_west(env: ExecutionContext, target: str, expected_tail: list[str]) -> None:
    command = ZephyrBuild(env, "build", CONFIG).west_build_command(target)

    assert command[7 : 7 + len(expected_tail)] == expected_tail
    assert "--" in command


def test_cross_compile_needs_installed_toolchain(env: ExecutionContext) -> None:
    config = {**CONFIG, "toolchain": "cross-compile", "toolchain_app": "riscv64-zephyr-elf", "sysroot": "picolibc/riscv64-zephyr-elf"}
    step = ZephyrBuild(env, "build", config)
    with pytest.raises(UserNotificationException, match="riscv64-zephyr-elf"):
        step.get_cmake_args()

    root = env.project_root_dir / "poks" / "riscv64-zephyr-elf" / "1.0"
    env.install_dirs = [root / "bin"]
    args = step.get_cmake_args()

    assert f"-DCROSS_COMPILE={(root / 'bin' / 'riscv64-zephyr-elf').as_posix()}-" in args
    assert f"-DCROSS_COMPILE_TOOLCHAIN_PATH={root.as_posix()}" in args
    assert f"-DSYSROOT_DIR={(root / 'picolibc/riscv64-zephyr-elf').as_posix()}" in args
