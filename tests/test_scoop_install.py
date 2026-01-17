import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from py_app_dev.core.scoop_wrapper import ScoopFileElement

from yanga.domain.config import PlatformConfig, ScoopManifest, VariantConfig
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest
from yanga.steps.scoop_install import ScoopInstall


def test_scoop_data() -> None:
    scoop_content = {
        "buckets": [{"Name": "my_bucket", "Source": "https://github.com/my/bucket"}],
        "apps": [
            {
                "Name": "app1",
                "Source": "my_bucket",
                "Version": "1.0.0",
            },
            {
                "name": "app2",
                "source": "my_bucket",
                "version": "2.0.0",
            },
        ],
    }
    content = ScoopManifest.from_dict(scoop_content)
    assert content.buckets[0].name == "my_bucket"
    assert {app.name for app in content.apps} == {"app1", "app2"}
    # Check serialization back to dict
    assert json.loads(content.to_json_string()) == scoop_content


def test_scoop_install_with_global_scoopfile_and_platform_scoop_manifest(tmp_path: Path) -> None:
    project_dir = tmp_path

    # Create a global scoopfile.json file
    global_scoop_content = {
        "buckets": [{"Name": "global_bucket", "Source": "https://github.com/global/bucket"}],
        "apps": [{"Name": "global_app", "Source": "global_bucket", "Version": "1.0.0"}],
    }
    global_scoop_file = project_dir / "scoopfile.json"
    with open(global_scoop_file, "w") as f:
        json.dump(global_scoop_content, f)

    platform_specific_content = {
        "buckets": [{"name": "global_bucket", "source": "https://github.com/global/bucket"}],
        "apps": [{"name": "platform_app", "source": "global_bucket", "version": "0.0.1"}],
    }

    exec_context = ExecutionContext(
        project_root_dir=project_dir,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
        platform=PlatformConfig(name="test_platform", scoop_manifest=ScoopManifest.from_dict(platform_specific_content)),
    )

    scoop_install = ScoopInstall(exec_context, "install")

    # Run
    collected_dependencies = scoop_install._collect_dependencies()

    # Verify
    assert {bucket.name for bucket in collected_dependencies.buckets} == {"global_bucket"}
    assert {app.name for app in collected_dependencies.apps} == {"global_app", "platform_app"}


def test_scoop_install_with_platform_dependencies(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="test_platform",
        scoop_manifest=ScoopManifest(
            buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/ScoopInstaller/Main"})],
            apps=[ScoopFileElement.from_dict({"name": "git", "source": "main", "version": "2.42.0"})],
        ),
    )

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform)

    scoop_install = ScoopInstall(exec_context, "install")
    collected_dependencies = scoop_install._collect_dependencies()

    assert len(collected_dependencies.buckets) == 1
    assert collected_dependencies.buckets[0].name == "main"
    assert collected_dependencies.buckets[0].source == "https://github.com/ScoopInstaller/Main"

    assert len(collected_dependencies.apps) == 1
    assert collected_dependencies.apps[0].name == "git"
    assert collected_dependencies.apps[0].source == "main"
    assert collected_dependencies.apps[0].version == "2.42.0"


def test_scoop_install_with_variant_dependencies(tmp_path: Path) -> None:
    project_dir = tmp_path

    variant = VariantConfig(
        name="test_variant",
        scoop_manifest=ScoopManifest(
            buckets=[ScoopFileElement.from_dict({"name": "extras", "source": "https://github.com/ScoopInstaller/Extras"})],
            apps=[ScoopFileElement.from_dict({"name": "vscode", "source": "extras"})],
        ),
    )

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), variant=variant)

    scoop_install = ScoopInstall(exec_context, "install")
    collected_dependencies = scoop_install._collect_dependencies()

    assert len(collected_dependencies.buckets) == 1
    assert collected_dependencies.buckets[0].name == "extras"
    assert collected_dependencies.buckets[0].source == "https://github.com/ScoopInstaller/Extras"

    assert len(collected_dependencies.apps) == 1
    assert collected_dependencies.apps[0].name == "vscode"
    assert collected_dependencies.apps[0].source == "extras"
    assert collected_dependencies.apps[0].version is None


def test_scoop_install_merges_platform_and_variant_dependencies(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="test_platform",
        scoop_manifest=ScoopManifest(
            buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/ScoopInstaller/Main"})],
            apps=[ScoopFileElement.from_dict({"name": "git", "source": "main", "version": "2.42.0"})],
        ),
    )

    variant = VariantConfig(
        name="test_variant",
        scoop_manifest=ScoopManifest(
            buckets=[ScoopFileElement.from_dict({"name": "extras", "source": "https://github.com/ScoopInstaller/Extras"})],
            apps=[ScoopFileElement.from_dict({"name": "vscode", "source": "extras"})],
        ),
    )

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform, variant=variant)

    scoop_install = ScoopInstall(exec_context, "install")
    collected_dependencies = scoop_install._collect_dependencies()

    assert len(collected_dependencies.buckets) == 2
    bucket_names = {bucket.name for bucket in collected_dependencies.buckets}
    assert bucket_names == {"main", "extras"}

    assert len(collected_dependencies.apps) == 2
    app_names = {app.name for app in collected_dependencies.apps}
    assert app_names == {"git", "vscode"}


def test_scoop_install_with_no_dependencies(tmp_path: Path) -> None:
    project_dir = tmp_path

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"))

    scoop_install = ScoopInstall(exec_context, "install")
    collected_dependencies = scoop_install._collect_dependencies()

    assert len(collected_dependencies.buckets) == 0
    assert len(collected_dependencies.apps) == 0


def test_scoop_install_generates_scoop_manifest(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="test_platform",
        scoop_manifest=ScoopManifest(
            buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/ScoopInstaller/Main"})],
            apps=[ScoopFileElement.from_dict({"name": "git", "source": "main", "version": "2.42.0"})],
        ),
    )

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform)

    scoop_install = ScoopInstall(exec_context, "install")
    manifest = scoop_install._collect_dependencies()
    scoop_install._generate_scoop_manifest(manifest)

    assert scoop_install.scoop_manifest_file.exists()

    with scoop_install.scoop_manifest_file.open() as manifest_file:
        content = json.load(manifest_file)

    assert "buckets" in content
    assert "apps" in content

    buckets = content["buckets"]
    assert len(buckets) == 1
    assert buckets[0]["name"] == "main"
    assert buckets[0]["source"] == "https://github.com/ScoopInstaller/Main"

    apps = content["apps"]
    assert len(apps) == 1
    assert apps[0]["name"] == "git"
    assert apps[0]["source"] == "main"
    assert apps[0]["version"] == "2.42.0"


def test_scoop_install_merges_buckets_with_conflicts(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="test_platform",
        scoop_manifest=ScoopManifest(
            buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/ScoopInstaller/Main"})],
            apps=[],
        ),
    )

    variant = VariantConfig(
        name="test_variant",
        scoop_manifest=ScoopManifest(
            buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/different/main"})],
            apps=[],
        ),
    )

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform, variant=variant)

    scoop_install = ScoopInstall(exec_context, "install")
    collected_dependencies = scoop_install._collect_dependencies()

    assert len(collected_dependencies.buckets) == 1
    assert collected_dependencies.buckets[0].name == "main"
    assert collected_dependencies.buckets[0].source == "https://github.com/ScoopInstaller/Main"


def test_scoop_install_variant_specific_directories(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="windows_platform",
        scoop_manifest=ScoopManifest(
            buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/ScoopInstaller/Main"})],
            apps=[ScoopFileElement.from_dict({"name": "git", "source": "main"})],
        ),
    )

    for variant_name in ["variant_a", "variant_b"]:
        exec_context = ExecutionContext(
            project_root_dir=project_dir,
            variant_name=variant_name,
            user_request=UserVariantRequest(variant_name),
            platform=platform,
        )

        scoop_install = ScoopInstall(exec_context, "install")
        collected_dependencies = scoop_install._collect_dependencies()
        scoop_install._generate_scoop_manifest(collected_dependencies)

        expected_scoop_file = project_dir / ".yanga" / "build" / variant_name / "windows_platform" / "scoopfile.json"
        assert expected_scoop_file.exists()
        assert scoop_install.scoop_manifest_file == expected_scoop_file


def test_scoop_manifest_file_from_file(tmp_path: Path) -> None:
    project_dir = tmp_path

    scoop_content = {
        "buckets": [{"Name": "main", "Source": "https://github.com/ScoopInstaller/Main"}, {"Name": "extras", "Source": "https://github.com/ScoopInstaller/Extras"}],
        "apps": [{"Name": "git", "Source": "main", "Version": "2.42.0"}, {"Name": "vscode", "Source": "extras"}],
    }

    scoop_file = project_dir / "scoopfile.json"
    scoop_file.write_text(json.dumps(scoop_content, indent=2))

    manifest_file = ScoopManifest.from_file(scoop_file)
    assert manifest_file.file == scoop_file

    assert len(manifest_file.buckets) == 2
    main_bucket = next((bucket for bucket in manifest_file.buckets if bucket.name == "main"), None)
    assert main_bucket is not None
    assert main_bucket.source == "https://github.com/ScoopInstaller/Main"

    extras_bucket = next((bucket for bucket in manifest_file.buckets if bucket.name == "extras"), None)
    assert extras_bucket is not None
    assert extras_bucket.source == "https://github.com/ScoopInstaller/Extras"

    assert len(manifest_file.apps) == 2
    git_app = next((app for app in manifest_file.apps if app.name == "git"), None)
    assert git_app is not None
    assert git_app.source == "main"
    assert git_app.version == "2.42.0"

    vscode_app = next((app for app in manifest_file.apps if app.name == "vscode"), None)
    assert vscode_app is not None
    assert vscode_app.source == "extras"
    assert vscode_app.version is None


def test_scoop_install_with_global_scoopfile_using_manifest_file(tmp_path: Path) -> None:
    project_dir = tmp_path

    global_scoop_content = {
        "buckets": [{"Name": "global_bucket", "Source": "https://github.com/global/bucket"}],
        "apps": [{"Name": "global_app", "Source": "global_bucket", "Version": "1.0.0"}],
    }

    global_scoop_file = project_dir / "scoopfile.json"
    global_scoop_file.write_text(json.dumps(global_scoop_content, indent=2))

    exec_context = ExecutionContext(
        project_root_dir=project_dir,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
    )

    scoop_install = ScoopInstall(exec_context, "install")
    collected_dependencies = scoop_install._collect_dependencies()

    assert len(collected_dependencies.buckets) == 1
    assert collected_dependencies.buckets[0].name == "global_bucket"
    assert collected_dependencies.buckets[0].source == "https://github.com/global/bucket"

    assert len(collected_dependencies.apps) == 1
    assert collected_dependencies.apps[0].name == "global_app"
    assert collected_dependencies.apps[0].source == "global_bucket"
    assert collected_dependencies.apps[0].version == "1.0.0"


def test_scoop_install_execution_info_serialization(tmp_path: Path) -> None:
    from yanga.steps.scoop_install import ScoopInstallExecutionInfo

    execution_info = ScoopInstallExecutionInfo(install_dirs=[tmp_path / "app1", tmp_path / "app2"], env_vars={"PATH": "/usr/bin", "EDITOR": "vim"})

    info_file = tmp_path / "execution_info.json"
    execution_info.to_json_file(info_file)
    assert info_file.exists()

    loaded_info = ScoopInstallExecutionInfo.from_json_file(info_file)
    assert len(loaded_info.install_dirs) == 2
    assert tmp_path / "app1" in loaded_info.install_dirs
    assert tmp_path / "app2" in loaded_info.install_dirs
    assert loaded_info.env_vars["PATH"] == "/usr/bin"
    assert loaded_info.env_vars["EDITOR"] == "vim"


def test_scoop_install_run_skips_on_non_windows(tmp_path: Path) -> None:
    project_dir = tmp_path
    exec_context = ExecutionContext(
        project_root_dir=project_dir,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
    )
    scoop_install = ScoopInstall(exec_context, "install")

    with patch("platform.system", return_value="Linux"):
        assert scoop_install.run() == 0

    with patch("platform.system", return_value="Darwin"):
        assert scoop_install.run() == 0


def test_scoop_install_run_executes_on_windows(tmp_path: Path) -> None:
    project_dir = tmp_path
    exec_context = ExecutionContext(
        project_root_dir=project_dir,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
    )
    scoop_install = ScoopInstall(exec_context, "install")

    # Mock internal methods to avoid side effects and just check if logic proceeds
    scoop_install._collect_dependencies = MagicMock(return_value=ScoopManifest())  # type: ignore

    with patch("platform.system", return_value="Windows"):
        assert scoop_install.run() == 0
        scoop_install._collect_dependencies.assert_called_once()
