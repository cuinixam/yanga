from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.utils import CMakeAnalyzer
from yanga.cmake.cmake_backend import (
    CMakeAddExecutable,
    CMakeCustomCommand,
    CMakeCustomTarget,
    CMakeInclude,
    CMakeIncludeDirectories,
    CMakeObjectLibrary,
    CMakeTargetIncludeDirectories,
    CMakeVariable,
)
from yanga.cmake.gtest import GTestCMakeGenerator
from yanga.domain.artifacts import ProjectArtifactsLocator
from yanga.domain.components import Component
from yanga.domain.execution_context import ExecutionContext


@pytest.fixture
def locate_artifact():
    """Fixture to mock the locate_artifact method."""
    with patch(
        ProjectArtifactsLocator.__module__ + "." + ProjectArtifactsLocator.__name__ + ".locate_artifact",
        side_effect=lambda file, _: Path(file),
    ) as my_locate_artifact:
        yield my_locate_artifact


@pytest.fixture
def env(locate_artifact: Mock) -> ExecutionContext:
    assert locate_artifact, "Fixture locate_artifact is not explicitly used in this fixture, but is required by the fixture chain."
    env = Mock(spec=ExecutionContext)
    env.variant_name = "mock_variant"
    env.components = [
        Component(
            name="CompA",
            path=Path("compA"),
            sources=["source.cpp"],
            test_sources=["test_source.cpp"],
            include_dirs=[],
            is_subcomponent=False,
            description="Mock component A",
            components=[],
        ),
        Component(
            name="CompBNotTestable",
            path=Path("compB"),
            sources=["source.cpp"],
            test_sources=[],
            include_dirs=[],
            is_subcomponent=False,
            description="Mock component A",
            components=[],
        ),
    ]
    env.include_directories = [Path("/mock/include/dir")]
    env.create_artifacts_locator.return_value = ProjectArtifactsLocator(Path("/mock/project/root"), "mock_variant", "mock_platform", "mock_build_type")
    return env


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"


@pytest.fixture
def gtest_cmake_generator(env: ExecutionContext, output_dir: Path) -> GTestCMakeGenerator:
    return GTestCMakeGenerator(env, output_dir)


def test_generate(gtest_cmake_generator: GTestCMakeGenerator) -> None:
    elements = gtest_cmake_generator.generate()
    assert elements
    cmake_analyzer = CMakeAnalyzer(elements)
    variables = cmake_analyzer.assert_elements_of_type(CMakeVariable, 4)
    assert [var.name for var in variables] == ["CMAKE_CXX_STANDARD", "CMAKE_CXX_STANDARD_REQUIRED", "gtest_force_shared_crt", "CMAKE_BUILD_DIR"]
    includes = cmake_analyzer.assert_elements_of_type(CMakeInclude, 2)
    assert [include.path for include in includes] == ["GoogleTest", "CTest"]


def test_create_variant_cmake_elements(
    gtest_cmake_generator: GTestCMakeGenerator,
) -> None:
    elements = gtest_cmake_generator.create_variant_cmake_elements()
    assert elements


def test_cmake_build_components_file(
    gtest_cmake_generator: GTestCMakeGenerator,
) -> None:
    elements = gtest_cmake_generator.create_components_cmake_elements()
    cmake_analyzer = CMakeAnalyzer(elements)
    executable = cmake_analyzer.assert_element_of_type(CMakeAddExecutable)
    assert executable.name == "CompA"
    targets = cmake_analyzer.assert_elements_of_type(CMakeCustomTarget, 3)
    assert [target.name for target in targets] == ["CompA_mockup", "CompA_test", "CompA_build"]


def test_get_include_directories(gtest_cmake_generator: GTestCMakeGenerator) -> None:
    assert len(gtest_cmake_generator.get_include_directories().paths) == 5


def test_automock_enabled_by_default(env: ExecutionContext, output_dir: Path) -> None:
    # Run IUT
    elements = GTestCMakeGenerator(env, output_dir).generate()

    cmake_analyzer = CMakeAnalyzer(elements)
    custom_targets: list[CMakeCustomTarget] = cmake_analyzer.assert_elements_of_type(CMakeCustomTarget, 3)
    assert [target.name for target in custom_targets] == ["CompA_mockup", "CompA_test", "CompA_build"]
    # Expect the partial link library required to find the symbols to be mocked
    object_library = cmake_analyzer.assert_element_of_type(CMakeObjectLibrary)
    assert object_library.name == "CompA_PC"
    executable = cmake_analyzer.assert_element_of_type(CMakeAddExecutable)
    assert [str(source) for source in executable.sources] == ["source.cpp", "test_source.cpp", f"{output_dir.as_posix()}/mockup_CompA.cc"]
    custom_command = cmake_analyzer.assert_element_of_type(CMakeCustomCommand, lambda cmd: cmd.description.startswith("Run the test executable"))
    assert len(custom_command.commands) == 1
    assert custom_command.commands[0].command == "CompA"
    assert custom_command.commands[0].arguments == ["--gtest_output=xml:CompA_junit.xml", "||", "${CMAKE_COMMAND}", "-E", "true"]


def test_automock_disabled_generates_no_mock_targets(env: ExecutionContext, output_dir: Path) -> None:
    """Verify that when automock is explicitly disabled, no partial link library and no mockup-related custom targets are generated."""
    # Run IUT
    elements = GTestCMakeGenerator(env, output_dir, {"automock": False}).generate()

    cmake_analyzer = CMakeAnalyzer(elements)

    # No mockup-related custom targets should be generated.
    custom_targets: list[CMakeCustomTarget] = cmake_analyzer.assert_elements_of_type(CMakeCustomTarget, 2)
    assert [target.name for target in custom_targets] == ["CompA_test", "CompA_build"]

    # No partial link library should be generated.
    cmake_analyzer.assert_elements_of_type(CMakeObjectLibrary, 0)

    executable = cmake_analyzer.assert_element_of_type(CMakeAddExecutable)
    assert [str(source) for source in executable.sources] == ["source.cpp", "test_source.cpp"]


def test_use_global_includes_disabled_generates_no_global_include_directories(env: ExecutionContext, output_dir: Path) -> None:
    """Verify that when use_global_includes is disabled, no global include directories are generated."""
    # Global include directories should not be generated in the variant elements
    variant_elements = GTestCMakeGenerator(env, output_dir, {"use_global_includes": False}).create_variant_cmake_elements()
    variant_analyzer = CMakeAnalyzer(variant_elements)

    # Check that no CMakeIncludeDirectories is present in variant elements
    include_directories = variant_analyzer.find_elements_of_type(CMakeIncludeDirectories)
    assert len(include_directories) == 0


def test_use_global_includes_enabled_by_default_generates_global_include_directories(env: ExecutionContext, output_dir: Path) -> None:
    """Verify that when use_global_includes is enabled (default), global include directories are generated."""
    # Global include directories should be generated in the variant elements
    variant_elements = GTestCMakeGenerator(env, output_dir).create_variant_cmake_elements()
    variant_analyzer = CMakeAnalyzer(variant_elements)

    # Check that CMakeIncludeDirectories is present in variant elements
    include_directories = variant_analyzer.find_elements_of_type(CMakeIncludeDirectories)
    assert len(include_directories) == 1  # Should have one CMakeIncludeDirectories element


def test_use_global_includes_disabled_adds_component_specific_include_directories(env: ExecutionContext, output_dir: Path) -> None:
    """Verify that when use_global_includes is disabled, component-specific include directories are added as target_include_directories."""
    # Set up component with include directories
    component = env.components[0]  # Get the CompA component
    component.include_dirs = [Path("/component/inc"), Path("/component/src")]

    # Generate elements with use_global_includes=False
    elements = GTestCMakeGenerator(env, output_dir, {"use_global_includes": False}).generate()
    cmake_analyzer = CMakeAnalyzer(elements)

    # Find the executable
    executable = cmake_analyzer.assert_element_of_type(CMakeAddExecutable)

    # Check that CMakeTargetIncludeDirectories elements are generated
    target_includes = cmake_analyzer.find_elements_of_type(CMakeTargetIncludeDirectories)
    assert len(target_includes) > 0, "No CMakeTargetIncludeDirectories elements found"

    # Find the target include directories for our executable
    target_name = executable.name
    component_target_includes = [ti for ti in target_includes if ti.target_name == target_name]
    assert len(component_target_includes) > 0, f"No target include directories found for target {target_name}"

    # Check that component include directories are included
    all_paths = []
    for ti in component_target_includes:
        all_paths.extend([str(path.path) for path in ti.paths])

    # Normalize paths for Windows compatibility
    normalized_paths = [p.replace("\\", "/") for p in all_paths]
    assert "/component/inc" in normalized_paths, f"Component include directory not found in target includes: {normalized_paths}"
    assert "/component/src" in normalized_paths, f"Component include directory not found in target includes: {normalized_paths}"

    # Verify that the visibility is PRIVATE for executables with sources
    component_ti = component_target_includes[0]
    assert component_ti.visibility == "PRIVATE", f"Expected PRIVATE visibility, got {component_ti.visibility}"
