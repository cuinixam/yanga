import json
from pathlib import Path
from unittest.mock import MagicMock

from poks.domain import PoksApp, PoksBucket

from yanga.domain.config import ConfigFile, PlatformConfig, VariantConfig
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest
from yanga.steps.poks_install import PoksConfig, PoksInstall, PoksInstallExecutionInfo


def test_poks_config_data() -> None:
    poks_content = {
        "buckets": [{"name": "tools", "url": "https://github.com/example/bucket"}],
        "apps": [
            {"name": "cmake", "version": "3.28.1", "bucket": "tools"},
            {"name": "ninja", "version": "1.11.1", "bucket": "tools"},
        ],
    }
    config = PoksConfig.from_dict(poks_content)
    assert config.buckets[0].name == "tools"
    assert {app.name for app in config.apps} == {"cmake", "ninja"}
    # Check serialization back to dict
    assert json.loads(config.to_json_string()) == poks_content


def test_poks_install_with_platform_dependencies(tmp_path: Path) -> None:
    platform = PlatformConfig(
        name="test_platform",
        configs=[
            ConfigFile(
                id="poks",
                content=PoksConfig(
                    buckets=[PoksBucket(name="main", url="https://github.com/example/main")],
                    apps=[PoksApp(name="cmake", version="3.28.1", bucket="main")],
                ).to_dict(),
            )
        ],
    )

    exec_context = ExecutionContext(
        project_root_dir=tmp_path,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
        platform=platform,
    )

    poks_install = PoksInstall(exec_context, "install")
    collected = poks_install._collect_dependencies()

    assert len(collected.buckets) == 1
    assert collected.buckets[0].name == "main"
    assert collected.buckets[0].url == "https://github.com/example/main"

    assert len(collected.apps) == 1
    assert collected.apps[0].name == "cmake"
    assert collected.apps[0].version == "3.28.1"
    assert collected.apps[0].bucket == "main"


def test_poks_install_with_variant_dependencies(tmp_path: Path) -> None:
    variant = VariantConfig(
        name="test_variant",
        configs=[
            ConfigFile(
                id="poks",
                content=PoksConfig(
                    buckets=[PoksBucket(name="extras", url="https://github.com/example/extras")],
                    apps=[PoksApp(name="ninja", version="1.11.1", bucket="extras")],
                ).to_dict(),
            )
        ],
    )

    exec_context = ExecutionContext(
        project_root_dir=tmp_path,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
        variant=variant,
    )

    poks_install = PoksInstall(exec_context, "install")
    collected = poks_install._collect_dependencies()

    assert len(collected.buckets) == 1
    assert collected.buckets[0].name == "extras"

    assert len(collected.apps) == 1
    assert collected.apps[0].name == "ninja"
    assert collected.apps[0].version == "1.11.1"


def test_poks_install_merges_platform_and_variant_dependencies(tmp_path: Path) -> None:
    platform = PlatformConfig(
        name="test_platform",
        configs=[
            ConfigFile(
                id="poks",
                content=PoksConfig(
                    buckets=[PoksBucket(name="main", url="https://github.com/example/main")],
                    apps=[PoksApp(name="cmake", version="3.28.1", bucket="main")],
                ).to_dict(),
            )
        ],
    )

    variant = VariantConfig(
        name="test_variant",
        configs=[
            ConfigFile(
                id="poks",
                content=PoksConfig(
                    buckets=[PoksBucket(name="extras", url="https://github.com/example/extras")],
                    apps=[PoksApp(name="ninja", version="1.11.1", bucket="extras")],
                ).to_dict(),
            )
        ],
    )

    exec_context = ExecutionContext(
        project_root_dir=tmp_path,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
        platform=platform,
        variant=variant,
    )

    poks_install = PoksInstall(exec_context, "install")
    collected = poks_install._collect_dependencies()

    assert len(collected.buckets) == 2
    assert {b.name for b in collected.buckets} == {"main", "extras"}

    assert len(collected.apps) == 2
    assert {a.name for a in collected.apps} == {"cmake", "ninja"}


def test_poks_install_with_no_dependencies(tmp_path: Path) -> None:
    exec_context = ExecutionContext(
        project_root_dir=tmp_path,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
    )

    poks_install = PoksInstall(exec_context, "install")
    collected = poks_install._collect_dependencies()

    assert len(collected.buckets) == 0
    assert len(collected.apps) == 0


def test_poks_install_with_global_poks_json(tmp_path: Path) -> None:
    global_content = {
        "buckets": [{"name": "global_bucket", "url": "https://github.com/global/bucket"}],
        "apps": [{"name": "global_app", "version": "1.0.0", "bucket": "global_bucket"}],
    }
    global_file = tmp_path / "poks.json"
    global_file.write_text(json.dumps(global_content))

    exec_context = ExecutionContext(
        project_root_dir=tmp_path,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
    )

    poks_install = PoksInstall(exec_context, "install")
    collected = poks_install._collect_dependencies()

    assert len(collected.buckets) == 1
    assert collected.buckets[0].name == "global_bucket"

    assert len(collected.apps) == 1
    assert collected.apps[0].name == "global_app"
    assert collected.apps[0].version == "1.0.0"


def test_poks_install_with_global_and_platform_configs(tmp_path: Path) -> None:
    global_content = {
        "buckets": [{"name": "global_bucket", "url": "https://github.com/global/bucket"}],
        "apps": [{"name": "global_app", "version": "1.0.0", "bucket": "global_bucket"}],
    }
    global_file = tmp_path / "poks.json"
    global_file.write_text(json.dumps(global_content))

    platform_content = {
        "buckets": [{"name": "global_bucket", "url": "https://github.com/global/bucket"}],
        "apps": [{"name": "platform_app", "version": "0.0.1", "bucket": "global_bucket"}],
    }

    exec_context = ExecutionContext(
        project_root_dir=tmp_path,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
        platform=PlatformConfig(
            name="test_platform",
            configs=[ConfigFile(id="poks", content=platform_content)],
        ),
    )

    poks_install = PoksInstall(exec_context, "install")
    collected = poks_install._collect_dependencies()

    assert {b.name for b in collected.buckets} == {"global_bucket"}
    assert {a.name for a in collected.apps} == {"global_app", "platform_app"}


def test_poks_install_merges_buckets_with_conflicts(tmp_path: Path) -> None:
    platform = PlatformConfig(
        name="test_platform",
        configs=[
            ConfigFile(
                id="poks",
                content=PoksConfig(
                    buckets=[PoksBucket(name="main", url="https://github.com/example/main")],
                    apps=[],
                ).to_dict(),
            )
        ],
    )

    variant = VariantConfig(
        name="test_variant",
        configs=[
            ConfigFile(
                id="poks",
                content=PoksConfig(
                    buckets=[PoksBucket(name="main", url="https://github.com/different/main")],
                    apps=[],
                ).to_dict(),
            )
        ],
    )

    exec_context = ExecutionContext(
        project_root_dir=tmp_path,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
        platform=platform,
        variant=variant,
    )

    poks_install = PoksInstall(exec_context, "install")
    collected = poks_install._collect_dependencies()

    # First definition wins (variant is collected before platform)
    assert len(collected.buckets) == 1
    assert collected.buckets[0].name == "main"
    assert collected.buckets[0].url == "https://github.com/different/main"


def test_poks_install_generates_config(tmp_path: Path) -> None:
    platform = PlatformConfig(
        name="test_platform",
        configs=[
            ConfigFile(
                id="poks",
                content=PoksConfig(
                    buckets=[PoksBucket(name="main", url="https://github.com/example/main")],
                    apps=[PoksApp(name="cmake", version="3.28.1", bucket="main")],
                ).to_dict(),
            )
        ],
    )

    exec_context = ExecutionContext(
        project_root_dir=tmp_path,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
        platform=platform,
    )

    poks_install = PoksInstall(exec_context, "install")
    config = poks_install._collect_dependencies()
    poks_install._generate_poks_config(config)

    assert poks_install.poks_config_file.exists()

    content = json.loads(poks_install.poks_config_file.read_text())

    assert "buckets" in content
    assert "apps" in content
    assert len(content["buckets"]) == 1
    assert content["buckets"][0]["name"] == "main"
    assert len(content["apps"]) == 1
    assert content["apps"][0]["name"] == "cmake"
    assert content["apps"][0]["version"] == "3.28.1"


def test_poks_install_variant_specific_directories(tmp_path: Path) -> None:
    platform = PlatformConfig(
        name="test_platform",
        configs=[
            ConfigFile(
                id="poks",
                content=PoksConfig(
                    buckets=[PoksBucket(name="main", url="https://github.com/example/main")],
                    apps=[PoksApp(name="cmake", version="3.28.1", bucket="main")],
                ).to_dict(),
            )
        ],
    )

    for variant_name in ["variant_a", "variant_b"]:
        exec_context = ExecutionContext(
            project_root_dir=tmp_path,
            variant_name=variant_name,
            user_request=UserVariantRequest(variant_name),
            platform=platform,
        )

        poks_install = PoksInstall(exec_context, "install")
        config = poks_install._collect_dependencies()
        poks_install._generate_poks_config(config)

        expected_file = tmp_path / ".yanga" / "build" / variant_name / "test_platform" / "poks.json"
        assert expected_file.exists()
        assert poks_install.poks_config_file == expected_file


def test_poks_install_execution_info_serialization(tmp_path: Path) -> None:
    execution_info = PoksInstallExecutionInfo(
        install_dirs=[tmp_path / "app1" / "bin", tmp_path / "app2" / "bin"],
        env_vars={"TOOLCHAIN_PATH": "/some/path", "SDK_ROOT": "/sdk"},
    )

    info_file = tmp_path / "execution_info.json"
    execution_info.to_json_file(info_file)
    assert info_file.exists()

    loaded_info = PoksInstallExecutionInfo.from_json_file(info_file)
    assert len(loaded_info.install_dirs) == 2
    assert tmp_path / "app1" / "bin" in loaded_info.install_dirs
    assert tmp_path / "app2" / "bin" in loaded_info.install_dirs
    assert loaded_info.env_vars["TOOLCHAIN_PATH"] == "/some/path"
    assert loaded_info.env_vars["SDK_ROOT"] == "/sdk"


def test_poks_install_run_with_no_dependencies(tmp_path: Path) -> None:
    exec_context = ExecutionContext(
        project_root_dir=tmp_path,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
    )
    poks_install = PoksInstall(exec_context, "install")

    # Mock _collect_dependencies to return empty config
    poks_install._collect_dependencies = MagicMock(return_value=PoksConfig())  # type: ignore

    assert poks_install.run() == 0
    poks_install._collect_dependencies.assert_called_once()


def test_poks_config_from_file(tmp_path: Path) -> None:
    poks_content = {
        "buckets": [
            {"name": "main", "url": "https://github.com/example/main"},
            {"name": "extras", "url": "https://github.com/example/extras"},
        ],
        "apps": [
            {"name": "cmake", "version": "3.28.1", "bucket": "main"},
            {"name": "ninja", "version": "1.11.1", "bucket": "extras"},
        ],
    }

    config_file = tmp_path / "poks.json"
    config_file.write_text(json.dumps(poks_content, indent=2))

    config = PoksConfig.from_file(config_file)

    assert len(config.buckets) == 2
    assert next(b for b in config.buckets if b.name == "main").url == "https://github.com/example/main"
    assert next(b for b in config.buckets if b.name == "extras").url == "https://github.com/example/extras"

    assert len(config.apps) == 2
    assert next(a for a in config.apps if a.name == "cmake").version == "3.28.1"
    assert next(a for a in config.apps if a.name == "ninja").version == "1.11.1"
