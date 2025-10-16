import json
from pathlib import Path

from yanga.yide import IDEProjectGenerator, VSCodeCMakeKit


def test_create_cmake_kits_file_with_platforms(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create a sample yanga.yaml configuration file with platforms
    config_content = """
platforms:
  - name: win_exe
    description: Build Windows executable
    toolchain_file: platforms/windows/clang.cmake
  - name: gtest
    description: Build GTest tests
    toolchain_file: platforms/windows/gcc.cmake
"""
    config_file = project_dir / "yanga.yaml"
    config_file.write_text(config_content.strip())

    # Create the IDE project generator
    generator = IDEProjectGenerator(project_dir)

    # Generate the cmake kits file
    cmake_kits_file = generator.create_cmake_kits_file()

    # Check that the file path is correct
    expected_path = project_dir / ".vscode" / "cmake-kits.json"
    assert cmake_kits_file.path == expected_path

    # Check that the kits are correct
    assert len(cmake_kits_file.kits) == 2

    win_exe_kit = next((kit for kit in cmake_kits_file.kits if kit.name == "win_exe"), None)
    assert win_exe_kit is not None
    assert win_exe_kit.toolchainFile == "platforms/windows/clang.cmake"

    gtest_kit = next((kit for kit in cmake_kits_file.kits if kit.name == "gtest"), None)
    assert gtest_kit is not None
    assert gtest_kit.toolchainFile == "platforms/windows/gcc.cmake"


def test_create_cmake_kits_file_no_platforms(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create a minimal yanga.yaml configuration file without platforms
    config_content = """
variants:
  - name: test_variant
    components: []
"""
    config_file = project_dir / "yanga.yaml"
    config_file.write_text(config_content.strip())

    # Create the IDE project generator
    generator = IDEProjectGenerator(project_dir)

    # Generate the cmake kits file
    cmake_kits_file = generator.create_cmake_kits_file()

    # Check that no kits are generated
    assert len(cmake_kits_file.kits) == 0


def test_create_cmake_kits_file_platform_without_toolchain(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create a sample yanga.yaml configuration file with platform without toolchain
    config_content = """
platforms:
  - name: default_platform
    description: Default platform without toolchain
"""
    config_file = project_dir / "yanga.yaml"
    config_file.write_text(config_content.strip())

    # Create the IDE project generator
    generator = IDEProjectGenerator(project_dir)

    # Generate the cmake kits file
    cmake_kits_file = generator.create_cmake_kits_file()

    # Check that the kit is created with empty toolchain file
    assert len(cmake_kits_file.kits) == 1
    assert cmake_kits_file.kits[0].name == "default_platform"
    assert cmake_kits_file.kits[0].toolchainFile == ""


def test_ide_project_generator_run(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create a sample yanga.yaml configuration file
    config_content = """
platforms:
  - name: win_exe
    toolchain_file: platforms/windows/clang.cmake
"""
    config_file = project_dir / "yanga.yaml"
    config_file.write_text(config_content.strip())

    # Run the IDE project generator
    generator = IDEProjectGenerator(project_dir)
    generator.run()

    # Check that the cmake kits file was created
    cmake_kits_file_path = project_dir / ".vscode" / "cmake-kits.json"
    assert cmake_kits_file_path.exists()

    # Check the content of the generated file (full structure match)
    content = json.loads(cmake_kits_file_path.read_text())
    expected_content = [
        {
            "name": "win_exe",
            "toolchainFile": "platforms/windows/clang.cmake",
        }
    ]
    assert content == expected_content


def test_vscode_cmake_kit_serialization() -> None:
    kit = VSCodeCMakeKit(name="test_kit", toolchainFile="test/toolchain.cmake")

    expected_dict = {"name": "test_kit", "toolchainFile": "test/toolchain.cmake"}

    assert kit.to_dict() == expected_dict


def test_vscode_cmake_kit_serialization_without_environment_script() -> None:
    kit = VSCodeCMakeKit(name="test_kit", toolchainFile="test/toolchain.cmake")

    expected_dict = {"name": "test_kit", "toolchainFile": "test/toolchain.cmake"}

    assert kit.to_dict() == expected_dict


def test_create_cmake_variants_file_with_variants_and_build_types(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create a sample yanga.yaml configuration file with variants and platforms with build types
    config_content = """
variants:
  - name: EnglishVariant
    description: English language variant
    components: []
  - name: GermanVariant
    description: German language variant
    components: []

platforms:
  - name: win_exe
    description: Build Windows executable
    toolchain_file: platforms/windows/clang.cmake
    build_types: ["Debug", "Release", "RelWithDebInfo"]
  - name: linux_exe
    description: Build Linux executable
    toolchain_file: platforms/linux/gcc.cmake
    build_types: ["Debug", "Release", "MinSizeRel"]
"""
    config_file = project_dir / "yanga.yaml"
    config_file.write_text(config_content.strip())

    # Create the IDE project generator
    generator = IDEProjectGenerator(project_dir)

    # Generate the cmake variants file
    cmake_variants_file = generator.create_cmake_variants_file()

    # Check that the file path is correct
    expected_path = project_dir / ".vscode" / "cmake-variants.json"
    assert cmake_variants_file.path == expected_path

    # Write the file and check its content
    cmake_variants_file.to_file()
    content = json.loads(expected_path.read_text())

    expected_content = {
        "variant": {
            "choices": {
                "EnglishVariant": {
                    "short": "EnglishVariant",
                    "settings": {"VARIANT": "EnglishVariant"},
                },
                "GermanVariant": {
                    "short": "GermanVariant",
                    "settings": {"VARIANT": "GermanVariant"},
                },
            },
            "default": "EnglishVariant",
        },
        "buildType": {
            "choices": {
                "Debug": {"short": "Debug", "buildType": "Debug", "env": {"MY_BUILD_TYPE": "Debug"}},
                "MinSizeRel": {"short": "MinSizeRel", "buildType": "MinSizeRel", "env": {"MY_BUILD_TYPE": "MinSizeRel"}},
                "None": {"short": "None", "buildType": "None", "env": {"MY_BUILD_TYPE": ""}},
                "RelWithDebInfo": {"short": "RelWithDebInfo", "buildType": "RelWithDebInfo", "env": {"MY_BUILD_TYPE": "RelWithDebInfo"}},
                "Release": {"short": "Release", "buildType": "Release", "env": {"MY_BUILD_TYPE": "Release"}},
            },
            "default": "None",
        },
    }
    assert content == expected_content


def test_create_cmake_variants_file_with_default_build_types(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create configuration without build types in platforms
    config_content = """
variants:
  - name: TestVariant
    components: []

platforms:
  - name: default_platform
    description: Platform without build types
"""
    config_file = project_dir / "yanga.yaml"
    config_file.write_text(config_content.strip())

    # Create the IDE project generator
    generator = IDEProjectGenerator(project_dir)

    # Generate the cmake variants file
    cmake_variants_file = generator.create_cmake_variants_file()
    cmake_variants_file.to_file()

    # Read and check the generated content
    content = json.loads(cmake_variants_file.path.read_text())
    expected_content = {
        "variant": {
            "choices": {
                "TestVariant": {
                    "short": "TestVariant",
                    "settings": {"VARIANT": "TestVariant"},
                }
            },
            "default": "TestVariant",
        },
        "buildType": {
            "choices": {
                "Debug": {"short": "Debug", "buildType": "Debug", "env": {"MY_BUILD_TYPE": "Debug"}},
                "None": {"short": "None", "buildType": "None", "env": {"MY_BUILD_TYPE": ""}},
                "Release": {"short": "Release", "buildType": "Release", "env": {"MY_BUILD_TYPE": "Release"}},
            },
            "default": "None",
        },
    }
    assert content == expected_content


def test_create_cmake_variants_file_with_none_build_type(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create configuration with None build type in platforms
    config_content = """
variants:
  - name: TestVariant
    components: []

platforms:
  - name: platform_with_none
    description: Platform with None build type
    build_types: ["Debug", "Release"]
"""
    config_file = project_dir / "yanga.yaml"
    config_file.write_text(config_content.strip())

    # Create the IDE project generator
    generator = IDEProjectGenerator(project_dir)

    # Generate the cmake variants file
    cmake_variants_file = generator.create_cmake_variants_file()
    cmake_variants_file.to_file()

    # Read and check the generated content
    content = json.loads(cmake_variants_file.path.read_text())
    expected_content = {
        "variant": {
            "choices": {
                "TestVariant": {
                    "short": "TestVariant",
                    "settings": {"VARIANT": "TestVariant"},
                }
            },
            "default": "TestVariant",
        },
        "buildType": {
            "choices": {
                "Debug": {"short": "Debug", "buildType": "Debug", "env": {"MY_BUILD_TYPE": "Debug"}},
                "None": {"short": "None", "buildType": "None", "env": {"MY_BUILD_TYPE": ""}},
                "Release": {"short": "Release", "buildType": "Release", "env": {"MY_BUILD_TYPE": "Release"}},
            },
            "default": "None",
        },
    }
    assert content == expected_content
