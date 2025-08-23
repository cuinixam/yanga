from pathlib import Path
from tempfile import TemporaryDirectory

from yanga.domain.config import (
    PlatformConfig,
    VariantConfig,
    WestDependency,
    WestManifest,
    WestManifestFile,
    WestRemote,
)
from yanga.domain.execution_context import ExecutionContext, UserVariantRequest
from yanga.steps.west_install import WestInstall, WestInstallExecutionInfo


def test_west_install_with_platform_dependencies():
    with TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create a platform with west dependencies
        platform = PlatformConfig(
            name="test_platform",
            description="Test platform",
            west_manifest=WestManifest(
                remotes=[WestRemote(name="gtest", url_base="https://github.com/google")],
                projects=[WestDependency(name="googletest", remote="gtest", revision="v1.14.0", path="external/gtest")],
            ),
        )

        # Create execution context
        exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform)

        # Create WestInstall step
        west_install = WestInstall(exec_context, "install")

        # Test dependency collection
        collected_dependencies = west_install._collect_dependencies()

        # Verify platform dependencies are collected
        assert len(collected_dependencies.remotes) == 1
        assert collected_dependencies.remotes[0].name == "gtest"
        assert collected_dependencies.remotes[0].url_base == "https://github.com/google"

        assert len(collected_dependencies.projects) == 1
        assert collected_dependencies.projects[0].name == "googletest"
        assert collected_dependencies.projects[0].remote == "gtest"
        assert collected_dependencies.projects[0].revision == "v1.14.0"
        assert collected_dependencies.projects[0].path == "external/gtest"


def test_west_install_with_variant_dependencies():
    with TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create a variant with west dependencies
        variant = VariantConfig(
            name="test_variant",
            description="Test variant",
            west_manifest=WestManifest(
                remotes=[WestRemote(name="catch2", url_base="https://github.com/catchorg")],
                projects=[WestDependency(name="Catch2", remote="catch2", revision="v3.4.0", path="external/catch2")],
            ),
        )

        # Create execution context
        exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), variant=variant)

        # Create WestInstall step
        west_install = WestInstall(exec_context, "install")

        # Test dependency collection
        collected_dependencies = west_install._collect_dependencies()

        # Verify variant dependencies are collected
        assert len(collected_dependencies.remotes) == 1
        assert collected_dependencies.remotes[0].name == "catch2"
        assert collected_dependencies.remotes[0].url_base == "https://github.com/catchorg"

        assert len(collected_dependencies.projects) == 1
        assert collected_dependencies.projects[0].name == "Catch2"
        assert collected_dependencies.projects[0].remote == "catch2"
        assert collected_dependencies.projects[0].revision == "v3.4.0"
        assert collected_dependencies.projects[0].path == "external/catch2"


def test_west_install_merges_platform_and_variant_dependencies():
    with TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create platform with dependencies
        platform = PlatformConfig(
            name="test_platform",
            west_manifest=WestManifest(
                remotes=[WestRemote(name="gtest", url_base="https://github.com/google")],
                projects=[WestDependency(name="googletest", remote="gtest", revision="v1.14.0", path="external/gtest")],
            ),
        )

        # Create variant with different dependencies
        variant = VariantConfig(
            name="test_variant",
            west_manifest=WestManifest(
                remotes=[WestRemote(name="catch2", url_base="https://github.com/catchorg")],
                projects=[WestDependency(name="Catch2", remote="catch2", revision="v3.4.0", path="external/catch2")],
            ),
        )

        # Create execution context with both platform and variant
        exec_context = ExecutionContext(
            project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform, variant=variant
        )

        # Create WestInstall step
        west_install = WestInstall(exec_context, "install")

        # Test dependency collection
        collected_dependencies = west_install._collect_dependencies()

        # Verify both platform and variant dependencies are merged
        assert len(collected_dependencies.remotes) == 2
        remote_names = {remote.name for remote in collected_dependencies.remotes}
        assert remote_names == {"gtest", "catch2"}

        assert len(collected_dependencies.projects) == 2
        project_names = {project.name for project in collected_dependencies.projects}
        assert project_names == {"googletest", "Catch2"}


def test_west_install_with_no_dependencies():
    with TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create execution context without platform or variant dependencies
        exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"))

        # Create WestInstall step
        west_install = WestInstall(exec_context, "install")

        # Test dependency collection
        collected_dependencies = west_install._collect_dependencies()

        # Verify no dependencies are collected
        assert len(collected_dependencies.remotes) == 0
        assert len(collected_dependencies.projects) == 0


def test_west_install_generates_west_yaml():
    with TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create platform with dependencies
        platform = PlatformConfig(
            name="test_platform",
            west_manifest=WestManifest(
                remotes=[WestRemote(name="gtest", url_base="https://github.com/google")],
                projects=[WestDependency(name="googletest", remote="gtest", revision="v1.14.0", path="external/gtest")],
            ),
        )

        # Create execution context
        exec_context = ExecutionContext(project_root_dir=project_dir, variant_name="test_variant", user_request=UserVariantRequest("test_variant"), platform=platform)

        # Create WestInstall step
        west_install = WestInstall(exec_context, "install")

        # Collect dependencies
        manifest = west_install._collect_dependencies()

        # Generate west.yaml
        west_install._generate_west_manifest(manifest)

        # Verify west.yaml was created
        assert west_install.west_manifest_file.exists()

        # Verify content of generated west.yaml
        import yaml

        with open(west_install.west_manifest_file) as f:
            content = yaml.safe_load(f)

        assert "manifest" in content
        assert "remotes" in content["manifest"]
        assert "projects" in content["manifest"]

        # Check remote
        remotes = content["manifest"]["remotes"]
        assert len(remotes) == 1
        assert remotes[0]["name"] == "gtest"
        assert remotes[0]["url-base"] == "https://github.com/google"

        # Check project
        projects = content["manifest"]["projects"]
        assert len(projects) == 1
        assert projects[0]["name"] == "googletest"
        assert projects[0]["remote"] == "gtest"
        assert projects[0]["revision"] == "v1.14.0"
        assert projects[0]["path"] == "external/gtest"


def test_west_install_variant_specific_directories():
    with TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create platform with dependencies
        platform = PlatformConfig(
            name="linux_platform",
            west_manifest=WestManifest(
                remotes=[WestRemote(name="test_remote", url_base="https://github.com/test")],
                projects=[WestDependency(name="test_project", remote="test_remote", revision="main", path="external/test")],
            ),
        )

        # Test different variant names
        for variant_name in ["variant_a", "variant_b"]:
            exec_context = ExecutionContext(
                project_root_dir=project_dir,
                variant_name=variant_name,
                user_request=UserVariantRequest(variant_name),
                platform=platform,
            )

            west_install = WestInstall(exec_context, "install")
            collected_dependencies = west_install._collect_dependencies()
            west_install._generate_west_manifest(collected_dependencies)

            # Verify each variant gets its own directory
            expected_west_file = project_dir / "build" / variant_name / "linux_platform" / "west.yaml"
            assert expected_west_file.exists(), f"west.yaml should exist for variant {variant_name}"
            assert west_install.west_manifest_file == expected_west_file

        # Verify both files exist simultaneously
        variant_a_file = project_dir / "build" / "variant_a" / "linux_platform" / "west.yaml"
        variant_b_file = project_dir / "build" / "variant_b" / "linux_platform" / "west.yaml"
        assert variant_a_file.exists()
        assert variant_b_file.exists()


def test_west_install_uses_shared_external_directory():
    with TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create platform with dependencies
        platform = PlatformConfig(
            name="test_platform",
            west_manifest=WestManifest(
                remotes=[WestRemote(name="test_remote", url_base="https://github.com/test")],
                projects=[WestDependency(name="test_project", remote="test_remote", revision="main", path="external/test")],
            ),
        )

        # Create execution context for first variant
        exec_context_a = ExecutionContext(
            project_root_dir=project_dir,
            variant_name="variant_a",
            user_request=UserVariantRequest("variant_a"),
            platform=platform,
        )

        # Create execution context for second variant
        exec_context_b = ExecutionContext(
            project_root_dir=project_dir,
            variant_name="variant_b",
            user_request=UserVariantRequest("variant_b"),
            platform=platform,
        )

        # Create WestInstall steps for both variants
        west_install_a = WestInstall(exec_context_a, "install")
        west_install_b = WestInstall(exec_context_b, "install")

        # Verify both use the same external dependencies directory
        assert west_install_a.artifacts_locator.external_dependencies_dir == west_install_b.artifacts_locator.external_dependencies_dir
        expected_external_dir = project_dir / "build" / "external"
        assert west_install_a.artifacts_locator.external_dependencies_dir == expected_external_dir
        assert west_install_b.artifacts_locator.external_dependencies_dir == expected_external_dir

        # Verify west.yaml files are still variant-specific
        expected_west_a = project_dir / "build" / "variant_a" / "test_platform" / "west.yaml"
        expected_west_b = project_dir / "build" / "variant_b" / "test_platform" / "west.yaml"
        assert west_install_a.west_manifest_file == expected_west_a
        assert west_install_b.west_manifest_file == expected_west_b

        # Verify outputs include the shared external directory
        # Need to collect dependencies first so _collected_dependencies is set
        west_install_a._collected_dependencies = west_install_a._collect_dependencies()
        west_install_b._collected_dependencies = west_install_b._collect_dependencies()

        outputs_a = west_install_a.get_outputs()
        assert expected_external_dir in outputs_a
        assert expected_west_a in outputs_a

        outputs_b = west_install_b.get_outputs()
        assert expected_external_dir in outputs_b
        assert expected_west_b in outputs_b


def test_west_install_tracks_individual_dependency_directories():
    with TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create platform with multiple dependencies
        platform = PlatformConfig(
            name="test_platform",
            west_manifest=WestManifest(
                remotes=[WestRemote(name="github", url_base="https://github.com")],
                projects=[
                    WestDependency(name="googletest", remote="github", revision="v1.14.0", path="external/gtest"),
                    WestDependency(name="libfoo", remote="github", revision="main", path="external/foo"),
                ],
            ),
        )

        # Create execution context
        exec_context = ExecutionContext(
            project_root_dir=project_dir,
            variant_name="test_variant",
            user_request=UserVariantRequest("test_variant"),
            platform=platform,
        )

        west_install = WestInstall(exec_context, "install")

        # Collect dependencies
        west_install._collected_dependencies = west_install._collect_dependencies()

        # Create mock dependency directories that match what West creates
        # West creates directories directly in external_dir, stripping the "external/" prefix
        external_dir = west_install.artifacts_locator.external_dependencies_dir
        external_dir.mkdir(parents=True, exist_ok=True)
        gtest_dir = external_dir / "gtest"
        gtest_dir.mkdir(parents=True, exist_ok=True)
        foo_dir = external_dir / "foo"
        foo_dir.mkdir(parents=True, exist_ok=True)

        # Track dependency directories
        west_install._track_dependency_directories()

        # Verify execution info contains all directories
        assert len(west_install.execution_info.dependency_dirs) == 3  # external + gtest + foo
        assert external_dir in west_install.execution_info.dependency_dirs
        assert gtest_dir in west_install.execution_info.dependency_dirs
        assert foo_dir in west_install.execution_info.dependency_dirs

        # Verify get_outputs includes all tracked directories
        outputs = west_install.get_outputs()
        assert external_dir in outputs
        assert gtest_dir in outputs
        assert foo_dir in outputs

        # Verify execution info can be saved and loaded
        west_install.execution_info.to_json_file(west_install.execution_info_file)
        assert west_install.execution_info_file.exists()

        loaded_info = WestInstallExecutionInfo.from_json_file(west_install.execution_info_file)
        assert len(loaded_info.dependency_dirs) == 3
        assert external_dir in loaded_info.dependency_dirs
        assert gtest_dir in loaded_info.dependency_dirs
        assert foo_dir in loaded_info.dependency_dirs


def test_west_manifest_file_from_file():
    with TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create a west.yaml file similar to the template
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

        # Load the file using WestManifestFile.from_file()
        manifest_file = WestManifestFile.from_file(west_yaml_file)

        # Verify the file path was tracked
        assert manifest_file.file == west_yaml_file

        # Verify the manifest content
        manifest = manifest_file.manifest

        # Check remotes
        assert len(manifest.remotes) == 2
        gtest_remote = next((r for r in manifest.remotes if r.name == "gtest"), None)
        assert gtest_remote is not None
        assert gtest_remote.url_base == "https://github.com/google"

        catch2_remote = next((r for r in manifest.remotes if r.name == "catch2"), None)
        assert catch2_remote is not None
        assert catch2_remote.url_base == "https://github.com/catchorg"

        # Check projects
        assert len(manifest.projects) == 2
        gtest_project = next((p for p in manifest.projects if p.name == "googletest"), None)
        assert gtest_project is not None
        assert gtest_project.remote == "gtest"
        assert gtest_project.revision == "v1.14.0"
        assert gtest_project.path == "external/gtest"

        catch2_project = next((p for p in manifest.projects if p.name == "Catch2"), None)
        assert catch2_project is not None
        assert catch2_project.remote == "catch2"
        assert catch2_project.revision == "v3.4.0"
        assert catch2_project.path == "external/catch2"


def test_west_install_with_global_west_yaml_using_manifest_file():
    with TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create a global west.yaml file
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

        # Create execution context with no platform/variant dependencies
        exec_context = ExecutionContext(
            project_root_dir=project_dir,
            variant_name="test_variant",
            user_request=UserVariantRequest("test_variant"),
        )

        # Create WestInstall step
        west_install = WestInstall(exec_context, "install")

        # Test dependency collection - should read from global west.yaml using WestManifestFile
        collected_dependencies = west_install._collect_dependencies()

        # Verify global dependencies are collected
        assert len(collected_dependencies.remotes) == 1
        assert collected_dependencies.remotes[0].name == "global_remote"
        assert collected_dependencies.remotes[0].url_base == "https://github.com/global"

        assert len(collected_dependencies.projects) == 1
        assert collected_dependencies.projects[0].name == "global_project"
        assert collected_dependencies.projects[0].remote == "global_remote"
        assert collected_dependencies.projects[0].revision == "main"
        assert collected_dependencies.projects[0].path == "external/global_dep"
