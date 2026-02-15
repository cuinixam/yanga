import json
from pathlib import Path

from py_app_dev.core.scoop_wrapper import ScoopFileElement

from yanga.domain.config import ConfigFile, PlatformConfig, VariantConfig
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest
from yanga.steps.scoop_install import ScoopInstall
from yanga.steps.scoop_install_base import ScoopManifest


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
        platform=PlatformConfig(
            name="test_platform",
            configs=[
                ConfigFile(
                    id="scoop",
                    content=platform_specific_content,
                )
            ],
        ),
    )

    scoop_install = ScoopInstall(exec_context, "install")
    collected_dependencies = scoop_install._collect_dependencies()

    assert {bucket.name for bucket in collected_dependencies.buckets} == {"global_bucket"}
    assert {app.name for app in collected_dependencies.apps} == {"global_app", "platform_app"}


def test_scoop_install_with_platform_dependencies(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="test_platform",
        configs=[
            ConfigFile(
                id="scoop",
                content=ScoopManifest(
                    buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/ScoopInstaller/Main"})],
                    apps=[ScoopFileElement.from_dict({"name": "git", "source": "main", "version": "2.42.0"})],
                ).to_dict(),
            )
        ],
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
        configs=[
            ConfigFile(
                id="scoop",
                content=ScoopManifest(
                    buckets=[ScoopFileElement.from_dict({"name": "extras", "source": "https://github.com/ScoopInstaller/Extras"})],
                    apps=[ScoopFileElement.from_dict({"name": "vscode", "source": "extras"})],
                ).to_dict(),
            )
        ],
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
        configs=[
            ConfigFile(
                id="scoop",
                content=ScoopManifest(
                    buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/ScoopInstaller/Main"})],
                    apps=[ScoopFileElement.from_dict({"name": "git", "source": "main", "version": "2.42.0"})],
                ).to_dict(),
            )
        ],
    )

    variant = VariantConfig(
        name="test_variant",
        configs=[
            ConfigFile(
                id="scoop",
                content=ScoopManifest(
                    buckets=[ScoopFileElement.from_dict({"name": "extras", "source": "https://github.com/ScoopInstaller/Extras"})],
                    apps=[ScoopFileElement.from_dict({"name": "vscode", "source": "extras"})],
                ).to_dict(),
            )
        ],
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


def test_scoop_install_generates_scoop_manifest(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="test_platform",
        configs=[
            ConfigFile(
                id="scoop",
                content=ScoopManifest(
                    buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/ScoopInstaller/Main"})],
                    apps=[ScoopFileElement.from_dict({"name": "git", "source": "main", "version": "2.42.0"})],
                ).to_dict(),
            )
        ],
    )

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform)

    scoop_install = ScoopInstall(exec_context, "install")
    manifest = scoop_install._collect_dependencies()
    scoop_install._generate_scoop_manifest(manifest)

    assert scoop_install._output_manifest_file.exists()

    with scoop_install._output_manifest_file.open() as manifest_file:
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
        configs=[
            ConfigFile(
                id="scoop",
                content=ScoopManifest(
                    buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/ScoopInstaller/Main"})],
                    apps=[],
                ).to_dict(),
            )
        ],
    )

    variant = VariantConfig(
        name="test_variant",
        configs=[
            ConfigFile(
                id="scoop",
                content=ScoopManifest(
                    buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/different/main"})],
                    apps=[],
                ).to_dict(),
            )
        ],
    )

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform, variant=variant)

    scoop_install = ScoopInstall(exec_context, "install")
    collected_dependencies = scoop_install._collect_dependencies()

    assert len(collected_dependencies.buckets) == 1
    assert collected_dependencies.buckets[0].name == "main"
    assert collected_dependencies.buckets[0].source == "https://github.com/different/main"


def test_scoop_install_variant_specific_directories(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="windows_platform",
        configs=[
            ConfigFile(
                id="scoop",
                content=ScoopManifest(
                    buckets=[ScoopFileElement.from_dict({"name": "main", "source": "https://github.com/ScoopInstaller/Main"})],
                    apps=[ScoopFileElement.from_dict({"name": "git", "source": "main"})],
                ).to_dict(),
            )
        ],
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
        assert scoop_install._output_manifest_file == expected_scoop_file
