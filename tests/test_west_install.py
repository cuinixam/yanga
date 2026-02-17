from pathlib import Path

from pypeline.steps.west_install import WestDependency, WestInstallResult, WestManifest, WestManifestFile, WestRemote

from tests.utils import assert_element_of_type, assert_elements_of_type
from yanga.domain.config import ConfigFile, PlatformConfig, VariantConfig, VariantPlatformsConfig
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest
from yanga.steps.west_install import WestInstall


def _west_config(manifest: WestManifest) -> ConfigFile:
    """Helper to create a west ConfigFile from a WestManifest."""
    return ConfigFile(id="west", content={"manifest": manifest.to_dict()})


def test_west_install_with_platform_dependencies(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="test_platform",
        description="Test platform",
        configs=[
            _west_config(
                WestManifest(
                    remotes=[WestRemote(name="gtest", url_base="https://github.com/google")],
                    projects=[WestDependency(name="googletest", remote="gtest", revision="v1.14.0", path="external/gtest")],
                )
            )
        ],
    )

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform)

    west_install = WestInstall(exec_context, "install")
    merged_manifest = west_install._merge_manifests()

    remote = assert_element_of_type(merged_manifest.remotes, WestRemote)
    assert remote.name == "gtest"
    assert remote.url_base == "https://github.com/google"

    project = assert_element_of_type(merged_manifest.projects, WestDependency)
    assert project.name == "googletest"
    assert project.remote == "gtest"
    assert project.revision == "v1.14.0"
    assert project.path == "external/gtest"


def test_west_install_with_variant_dependencies(tmp_path: Path) -> None:
    project_dir = tmp_path

    variant = VariantConfig(
        name="test_variant",
        description="Test variant",
        configs=[
            _west_config(
                WestManifest(
                    remotes=[WestRemote(name="catch2", url_base="https://github.com/catchorg")],
                    projects=[WestDependency(name="Catch2", remote="catch2", revision="v3.4.0", path="external/catch2")],
                )
            )
        ],
    )

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), variant=variant)

    west_install = WestInstall(exec_context, "install")
    merged_manifest = west_install._merge_manifests()

    remote = assert_element_of_type(merged_manifest.remotes, WestRemote)
    assert remote.name == "catch2"
    assert remote.url_base == "https://github.com/catchorg"

    project = assert_element_of_type(merged_manifest.projects, WestDependency)
    assert project.name == "Catch2"
    assert project.remote == "catch2"
    assert project.revision == "v3.4.0"
    assert project.path == "external/catch2"


def test_west_install_merges_platform_and_variant_dependencies(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="test_platform",
        configs=[
            _west_config(
                WestManifest(
                    remotes=[WestRemote(name="gtest", url_base="https://github.com/google")],
                    projects=[WestDependency(name="googletest", remote="gtest", revision="v1.14.0", path="external/gtest")],
                )
            )
        ],
    )

    variant = VariantConfig(
        name="test_variant",
        configs=[
            _west_config(
                WestManifest(
                    remotes=[WestRemote(name="catch2", url_base="https://github.com/catchorg")],
                    projects=[WestDependency(name="Catch2", remote="catch2", revision="v3.4.0", path="external/catch2")],
                )
            )
        ],
    )

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform, variant=variant)

    west_install = WestInstall(exec_context, "install")
    merged_manifest = west_install._merge_manifests()

    remotes = assert_elements_of_type(merged_manifest.remotes, WestRemote, 2)
    assert {remote.name for remote in remotes} == {"gtest", "catch2"}

    projects = assert_elements_of_type(merged_manifest.projects, WestDependency, 2)
    assert {project.name for project in projects} == {"googletest", "Catch2"}


def test_west_install_with_no_dependencies(tmp_path: Path) -> None:
    project_dir = tmp_path

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"))

    west_install = WestInstall(exec_context, "install")
    merged_manifest = west_install._merge_manifests()

    assert_elements_of_type(merged_manifest.remotes, WestRemote, 0)
    assert_elements_of_type(merged_manifest.projects, WestDependency, 0)


def test_west_install_generates_west_yaml(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="test_platform",
        configs=[
            _west_config(
                WestManifest(
                    remotes=[WestRemote(name="gtest", url_base="https://github.com/google")],
                    projects=[WestDependency(name="googletest", remote="gtest", revision="v1.14.0", path="external/gtest", clone_depth=1)],
                )
            )
        ],
    )

    exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform)

    west_install = WestInstall(exec_context, "install")
    manifest = west_install._merge_manifests()
    west_install._write_west_manifest_file(manifest)

    assert west_install._output_manifest_file.exists()

    import yaml

    with west_install._output_manifest_file.open() as yaml_file:
        content = yaml.safe_load(yaml_file)

    assert "manifest" in content
    assert "remotes" in content["manifest"]
    assert "projects" in content["manifest"]

    remotes = content["manifest"]["remotes"]
    assert len(remotes) == 1
    remote = remotes[0]
    assert remote["name"] == "gtest"
    assert remote["url-base"] == "https://github.com/google"

    projects = content["manifest"]["projects"]
    assert len(projects) == 1
    project = projects[0]
    assert project["name"] == "googletest"
    assert project["remote"] == "gtest"
    assert project["revision"] == "v1.14.0"
    assert project["path"] == "external/gtest"
    assert project["clone-depth"] == 1


def test_west_install_variant_specific_directories(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="linux_platform",
        configs=[
            _west_config(
                WestManifest(
                    remotes=[WestRemote(name="test_remote", url_base="https://github.com/test")],
                    projects=[WestDependency(name="test_project", remote="test_remote", revision="main", path="external/test")],
                )
            )
        ],
    )

    for variant_name in ["variant_a", "variant_b"]:
        variant = VariantConfig(name=variant_name)
        exec_context = ExecutionContext(
            project_root_dir=project_dir,
            variant_name=variant_name,
            user_request=UserVariantRequest(variant_name),
            platform=platform,
            variant=variant,
        )

        west_install = WestInstall(exec_context, "install")
        merged_manifest = west_install._merge_manifests()
        west_install._write_west_manifest_file(merged_manifest)

        expected_west_file = project_dir / ".yanga" / "build" / variant_name / "linux_platform" / "west.yaml"
        assert expected_west_file.exists(), f"west.yaml should exist for variant {variant_name}"
        assert west_install._output_manifest_file == expected_west_file

    variant_a_file = project_dir / ".yanga" / "build" / "variant_a" / "linux_platform" / "west.yaml"
    variant_b_file = project_dir / ".yanga" / "build" / "variant_b" / "linux_platform" / "west.yaml"
    assert variant_a_file.exists()
    assert variant_b_file.exists()


def test_west_install_uses_shared_external_directory(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="test_platform",
        configs=[
            _west_config(
                WestManifest(
                    remotes=[WestRemote(name="test_remote", url_base="https://github.com/test")],
                    projects=[WestDependency(name="test_project", remote="test_remote", revision="main", path="external/test")],
                )
            )
        ],
    )

    variant_a = VariantConfig(name="variant_a")
    variant_b = VariantConfig(name="variant_b")

    exec_context_a = ExecutionContext(
        project_root_dir=project_dir,
        variant_name="variant_a",
        user_request=UserVariantRequest("variant_a"),
        platform=platform,
        variant=variant_a,
    )

    exec_context_b = ExecutionContext(
        project_root_dir=project_dir,
        variant_name="variant_b",
        user_request=UserVariantRequest("variant_b"),
        platform=platform,
        variant=variant_b,
    )

    west_install_a = WestInstall(exec_context_a, "install")
    west_install_b = WestInstall(exec_context_b, "install")

    assert west_install_a.artifacts_locator.external_dependencies_dir == west_install_b.artifacts_locator.external_dependencies_dir
    expected_external_dir = project_dir / ".yanga" / "ext"
    assert west_install_a.artifacts_locator.external_dependencies_dir == expected_external_dir
    assert west_install_b.artifacts_locator.external_dependencies_dir == expected_external_dir

    expected_west_a = project_dir / ".yanga" / "build" / "variant_a" / "test_platform" / "west.yaml"
    expected_west_b = project_dir / ".yanga" / "build" / "variant_b" / "test_platform" / "west.yaml"
    assert west_install_a._output_manifest_file == expected_west_a
    assert west_install_b._output_manifest_file == expected_west_b

    outputs_a = west_install_a.get_outputs()
    assert expected_west_a in outputs_a

    outputs_b = west_install_b.get_outputs()
    assert expected_west_b in outputs_b


def test_west_install_tracks_individual_dependency_directories(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(
        name="test_platform",
        configs=[
            _west_config(
                WestManifest(
                    remotes=[WestRemote(name="github", url_base="https://github.com")],
                    projects=[
                        WestDependency(name="googletest", remote="github", revision="v1.14.0", path="external/gtest"),
                        WestDependency(name="libfoo", remote="github", revision="main", path="external/foo"),
                    ],
                )
            )
        ],
    )

    variant = VariantConfig(name="test_variant")
    exec_context = ExecutionContext(
        project_root_dir=project_dir,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
        platform=platform,
        variant=variant,
    )

    west_install = WestInstall(exec_context, "install")
    merged_manifest = west_install._merge_manifests()

    workspace_dir = west_install._west_workspace_dir
    workspace_dir.mkdir(parents=True, exist_ok=True)
    gtest_dir = workspace_dir / "external" / "gtest"
    gtest_dir.mkdir(parents=True, exist_ok=True)
    foo_dir = workspace_dir / "external" / "foo"
    foo_dir.mkdir(parents=True, exist_ok=True)

    west_install._record_installed_directories(merged_manifest)

    assert len(west_install.install_result.installed_dirs) == 3
    assert workspace_dir in west_install.install_result.installed_dirs
    assert gtest_dir in west_install.install_result.installed_dirs
    assert foo_dir in west_install.install_result.installed_dirs

    west_install.install_result.to_json_file(west_install._install_result_file)
    assert west_install._install_result_file.exists()

    loaded_result = WestInstallResult.from_json_file(west_install._install_result_file)
    assert len(loaded_result.installed_dirs) == 3
    assert workspace_dir in loaded_result.installed_dirs
    assert gtest_dir in loaded_result.installed_dirs
    assert foo_dir in loaded_result.installed_dirs


def test_west_manifest_file_from_file(tmp_path: Path) -> None:
    project_dir = tmp_path

    west_yaml_content = """
manifest:
    remotes:
        - name: gtest
          url-base: https://github.com/google
        - name: catch2
          url-base: https://github.com/catchorg

    projects:
        - name: googletest
          remote: gtest
          revision: v1.14.0
          path: external/gtest
        - name: Catch2
          remote: catch2
          revision: v3.4.0
          path: external/catch2
"""

    west_yaml_file = project_dir / "west.yaml"
    west_yaml_file.write_text(west_yaml_content.strip())

    manifest_file = WestManifestFile.from_file(west_yaml_file)
    assert manifest_file.file == west_yaml_file

    manifest = manifest_file.manifest

    gtest_remote = assert_element_of_type(manifest.remotes, WestRemote, lambda r: r.name == "gtest")
    assert gtest_remote.url_base == "https://github.com/google"

    catch2_remote = assert_element_of_type(manifest.remotes, WestRemote, lambda r: r.name == "catch2")
    assert catch2_remote.url_base == "https://github.com/catchorg"

    gtest_project = assert_element_of_type(manifest.projects, WestDependency, lambda p: p.name == "googletest")
    assert gtest_project.remote == "gtest"
    assert gtest_project.revision == "v1.14.0"
    assert gtest_project.path == "external/gtest"

    catch2_project = assert_element_of_type(manifest.projects, WestDependency, lambda p: p.name == "Catch2")
    assert catch2_project.remote == "catch2"
    assert catch2_project.revision == "v3.4.0"
    assert catch2_project.path == "external/catch2"


def test_west_install_with_global_west_yaml_using_manifest_file(tmp_path: Path) -> None:
    project_dir = tmp_path

    global_west_content = """
manifest:
    remotes:
        - name: global_remote
          url-base: https://github.com/global

    projects:
        - name: global_project
          remote: global_remote
          revision: main
          path: external/global_dep
"""

    global_west_file = project_dir / "west.yaml"
    global_west_file.write_text(global_west_content.strip())

    exec_context = ExecutionContext(
        project_root_dir=project_dir,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
    )

    west_install = WestInstall(exec_context, "install")
    merged_manifest = west_install._merge_manifests()

    remote = assert_element_of_type(merged_manifest.remotes, WestRemote)
    assert remote.name == "global_remote"
    assert remote.url_base == "https://github.com/global"

    project = assert_element_of_type(merged_manifest.projects, WestDependency)
    assert project.name == "global_project"
    assert project.remote == "global_remote"
    assert project.revision == "main"
    assert project.path == "external/global_dep"


def test_west_install_with_variant_platform_specific_dependencies(tmp_path: Path) -> None:
    project_dir = tmp_path

    platform = PlatformConfig(name="test_platform")

    variant = VariantConfig(
        name="test_variant",
        platforms={
            "test_platform": VariantPlatformsConfig(
                components=["platform_component"],
                configs=[
                    _west_config(
                        WestManifest(
                            remotes=[WestRemote(name="platform_remote", url_base="https://github.com/platform")],
                            projects=[WestDependency(name="platform_lib", remote="platform_remote", revision="v1.0.0", path="external/platform_lib")],
                        )
                    )
                ],
            )
        },
    )

    exec_context = ExecutionContext(
        project_root_dir=project_dir,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
        platform=platform,
        variant=variant,
    )

    west_install = WestInstall(exec_context, "install")
    merged_manifest = west_install._merge_manifests()

    remote = assert_element_of_type(merged_manifest.remotes, WestRemote)
    assert remote.name == "platform_remote"
    assert remote.url_base == "https://github.com/platform"

    project = assert_element_of_type(merged_manifest.projects, WestDependency)
    assert project.name == "platform_lib"
    assert project.remote == "platform_remote"
    assert project.revision == "v1.0.0"
    assert project.path == "external/platform_lib"


def test_west_install_merges_all_dependencies_including_variant_platform_specific(tmp_path: Path) -> None:
    project_dir = tmp_path

    # Platform with its own dependencies
    platform = PlatformConfig(
        name="test_platform",
        configs=[
            _west_config(
                WestManifest(
                    remotes=[WestRemote(name="platform_remote", url_base="https://github.com/platform")],
                    projects=[WestDependency(name="platform_lib", remote="platform_remote", revision="v2.0.0", path="external/platform")],
                )
            )
        ],
    )

    # Variant with global dependencies and platform-specific dependencies
    variant = VariantConfig(
        name="test_variant",
        configs=[
            _west_config(
                WestManifest(
                    remotes=[WestRemote(name="variant_remote", url_base="https://github.com/variant")],
                    projects=[WestDependency(name="variant_lib", remote="variant_remote", revision="v1.0.0", path="external/variant")],
                )
            )
        ],
        platforms={
            "test_platform": VariantPlatformsConfig(
                components=["platform_component"],
                configs=[
                    _west_config(
                        WestManifest(
                            remotes=[WestRemote(name="variant_platform_remote", url_base="https://github.com/variant-platform")],
                            projects=[WestDependency(name="variant_platform_lib", remote="variant_platform_remote", revision="v3.0.0", path="external/variant_platform")],
                        )
                    )
                ],
            )
        },
    )

    exec_context = ExecutionContext(
        project_root_dir=project_dir,
        variant_name="test_variant",
        user_request=UserVariantRequest("test_variant"),
        platform=platform,
        variant=variant,
    )

    west_install = WestInstall(exec_context, "install")
    merged_manifest = west_install._merge_manifests()

    # Should have 3 remotes: platform, variant, and variant-platform-specific
    remotes = assert_elements_of_type(merged_manifest.remotes, WestRemote, 3)
    assert {remote.name for remote in remotes} == {"platform_remote", "variant_remote", "variant_platform_remote"}

    # Should have 3 projects: platform, variant, and variant-platform-specific
    projects = assert_elements_of_type(merged_manifest.projects, WestDependency, 3)
    assert {project.name for project in projects} == {"platform_lib", "variant_lib", "variant_platform_lib"}
