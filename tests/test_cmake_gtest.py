from pathlib import Path

import pytest

from tests.utils import assert_element_of_type, assert_elements_of_type, find_elements_of_type
from yanga.cmake.cmake_backend import (
    CMakeAddExecutable,
    CMakeAddLibrary,
    CMakeCustomCommand,
    CMakeCustomTarget,
    CMakeInclude,
    CMakeIncludeDirectories,
    CMakeTargetIncludeDirectories,
    CMakeVariable,
    IncludeScope,
)
from yanga.cmake.gtest import GTestCMakeGenerator, GTestCMakeGeneratorConfig, GTestComponentCMakeGenerator
from yanga.domain.components import Component
from yanga.domain.config import MockingConfiguration, TestingConfiguration
from yanga.domain.execution_context import ExecutionContext


@pytest.fixture
def gtest_cmake_generator(execution_context: ExecutionContext, output_dir: Path) -> GTestCMakeGenerator:
    return GTestCMakeGenerator(execution_context, output_dir)


def test_generate(gtest_cmake_generator: GTestCMakeGenerator) -> None:
    elements = gtest_cmake_generator.generate()
    assert elements

    variables = assert_elements_of_type(elements, CMakeVariable, 3)
    assert [var.name for var in variables] == ["CMAKE_CXX_STANDARD", "CMAKE_CXX_STANDARD_REQUIRED", "gtest_force_shared_crt"]
    assert_elements_of_type(elements, CMakeInclude, 0)


def test_create_variant_cmake_elements(
    gtest_cmake_generator: GTestCMakeGenerator,
) -> None:
    elements = gtest_cmake_generator.create_gtest_integration_cmake_elements()
    assert elements


def test_cmake_build_components_file(
    gtest_cmake_generator: GTestCMakeGenerator,
) -> None:
    elements = gtest_cmake_generator.create_components_cmake_elements()

    object_libraries = assert_elements_of_type(elements, CMakeAddLibrary, 2)
    assert {lib.name for lib in object_libraries} == {"CompA_PC", "CompBNotTestable_PC"}
    executable = assert_element_of_type(elements, CMakeAddExecutable)
    assert executable.name == "CompA"
    targets = assert_elements_of_type(elements, CMakeCustomTarget, 4)
    assert {target.name for target in targets} == {"CompA_mockup", "CompA_test", "CompA_build", "CompA_coverage"}


def test_get_include_directories(gtest_cmake_generator: GTestCMakeGenerator) -> None:
    assert len(gtest_cmake_generator.get_include_directories().paths) == 6


def test_automock_enabled_by_default(execution_context: ExecutionContext, output_dir: Path) -> None:
    # Run IUT
    elements = GTestCMakeGenerator(execution_context, output_dir).generate()

    targets = assert_elements_of_type(elements, CMakeCustomTarget, 5)
    assert {target.name for target in targets} == {"CompA_mockup", "CompA_test", "CompA_build", "CompA_coverage", "coverage"}
    # Expect the partial link library required to find the symbols to be mocked
    executable = assert_element_of_type(elements, CMakeAddExecutable, lambda exec: exec.name == "CompA")
    assert [str(source) for source in executable.sources] == ["test_compA_source.cpp", f"{output_dir.as_posix()}/CompA/mockup_CompA.cc"]
    assert set(executable.libraries) == {"GTest::gtest_main", "GTest::gmock_main", "pthread", "CompA_PC_lib"}
    custom_command = assert_element_of_type(elements, CMakeCustomCommand, lambda cmd: cmd.description.startswith("Run the test executable"))
    assert len(custom_command.commands) == 1
    # The command should now be the full path to the executable in the component directory
    command_str = str(custom_command.commands[0].command)
    assert "CompA" in command_str, f"Expected CompA in command path: {command_str}"
    # Check that the arguments include the component-specific JUnit XML path
    args = [str(arg) for arg in custom_command.commands[0].arguments]
    junit_arg = next((arg for arg in args if "junit.xml" in arg), None)
    assert junit_arg is not None, f"JUnit XML argument not found in: {args}"
    assert "CompA" in junit_arg, f"Component-specific path not found in JUnit argument: {junit_arg}"


def test_automock_disabled_generates_no_mock_targets(execution_context: ExecutionContext, output_dir: Path) -> None:
    """Verify that when automock is explicitly disabled, no partial link library and no mockup-related custom targets are generated."""
    # Run IUT
    elements = GTestCMakeGenerator(execution_context, output_dir, {"mocking": {"enabled": False}}).generate()

    # No mockup-related custom targets should be generated.
    targets = assert_elements_of_type(elements, CMakeCustomTarget, 4)
    assert {target.name for target in targets} == {"CompA_test", "CompA_build", "CompA_coverage", "coverage"}

    # No partial link library should be generated.
    object_libraries = assert_elements_of_type(elements, CMakeAddLibrary, 2)
    assert {lib.target_name for lib in object_libraries} == {"CompA_PC_lib", "CompBNotTestable_PC_lib"}

    executable = assert_element_of_type(elements, CMakeAddExecutable, lambda exec: exec.name == "CompA")
    assert [str(source) for source in executable.sources] == ["test_compA_source.cpp"]
    assert set(executable.libraries) == {"GTest::gtest_main", "GTest::gmock_main", "pthread", "CompA_PC_lib"}


def test_use_global_includes_disabled_generates_no_global_include_directories(execution_context: ExecutionContext, output_dir: Path) -> None:
    """Verify that when use_global_includes is disabled, no global include directories are generated."""
    # Global include directories should not be generated in the variant elements
    variant_elements = GTestCMakeGenerator(execution_context, output_dir, {"use_global_includes": False}).create_gtest_integration_cmake_elements()

    # Check that no CMakeIncludeDirectories is present in variant elements
    include_directories = find_elements_of_type(variant_elements, CMakeIncludeDirectories)
    assert len(include_directories) == 0


def test_use_global_includes_enabled_generates_global_include_directories(execution_context: ExecutionContext, output_dir: Path) -> None:
    """Verify that when use_global_includes is enabled (default), global include directories are generated."""
    # Global include directories should be generated in the variant elements
    variant_elements = GTestCMakeGenerator(execution_context, output_dir, {"use_global_includes": True}).create_gtest_integration_cmake_elements()

    # Check that CMakeIncludeDirectories is present in variant elements
    include_directories = find_elements_of_type(variant_elements, CMakeIncludeDirectories)
    assert len(include_directories) == 1  # Should have one CMakeIncludeDirectories element


def test_use_global_includes_disabled_adds_component_specific_include_directories(execution_context: ExecutionContext, output_dir: Path) -> None:
    """Verify that when use_global_includes is disabled, component-specific include directories are added as target_include_directories."""
    # Set up component with include directories
    component = find_elements_of_type(execution_context.components, Component)[0]  # Get the CompA component
    component.include_dirs = [Path("/component/inc"), Path("/component/src")]

    # Generate elements with use_global_includes=False
    elements = GTestCMakeGenerator(execution_context, output_dir, {"use_global_includes": False}).generate()

    # Find the executable
    executable = assert_element_of_type(elements, CMakeAddExecutable)
    assert executable.name == "CompA"

    # Check that CMakeTargetIncludeDirectories elements are generated
    target_includes = find_elements_of_type(elements, CMakeTargetIncludeDirectories)
    assert len(target_includes) > 0, "No CMakeTargetIncludeDirectories elements found"

    # Find the target include directories for our executable
    target_name = "CompA"
    component_target_includes = [ti for ti in target_includes if ti.target_name == target_name]
    assert len(component_target_includes) > 0, f"No target include directories found for target {target_name}"

    # Check that component include directories are included
    all_paths = []
    for ti in component_target_includes:
        all_paths.extend([str(path.path) for path in ti.paths])

    # Normalize paths for Windows compatibility
    normalized_paths = [Path(p).as_posix() for p in all_paths]
    assert "/component/inc" in normalized_paths, f"Component include directory not found in target includes: {normalized_paths}"
    assert "/component/src" in normalized_paths, f"Component include directory not found in target includes: {normalized_paths}"

    # Verify that the visibility is PRIVATE for executables with sources
    component_ti = component_target_includes[0]
    assert component_ti.scope == IncludeScope.PRIVATE, f"Expected PRIVATE visibility, got {component_ti.scope}"


def test_component_specific_directories_are_used(execution_context: ExecutionContext, output_dir: Path) -> None:
    """Verify that component-specific subdirectories are used for generated files."""
    elements = GTestCMakeGenerator(execution_context, output_dir).generate()

    # Find custom commands that contain component-specific paths
    custom_commands = find_elements_of_type(elements, CMakeCustomCommand)

    # Look for JUnit XML output files in component-specific directories
    junit_outputs = [cmd for cmd in custom_commands if cmd.outputs and any("_junit.xml" in str(output) for output in cmd.outputs)]
    assert len(junit_outputs) > 0, "No JUnit XML custom commands found"

    # Verify the JUnit XML file is in a component-specific directory
    junit_cmd = junit_outputs[0]
    assert junit_cmd.outputs
    junit_output_path = str(junit_cmd.outputs[0])
    assert "CompA_junit.xml" in junit_output_path, f"Expected CompA_junit.xml in path: {junit_output_path}"
    # The path should contain the component name as a subdirectory
    assert "CompA" in junit_output_path, f"Component subdirectory not found in JUnit path: {junit_output_path}"

    # Look for mockup generation commands
    mockup_commands = [cmd for cmd in custom_commands if cmd.outputs and any("mockup_" in str(output) for output in cmd.outputs)]
    assert len(mockup_commands) > 0, "No mockup generation commands found"

    # Verify mockup files are in component-specific directories
    mockup_cmd = mockup_commands[0]
    assert mockup_cmd.outputs
    mockup_output_paths = [str(output) for output in mockup_cmd.outputs]
    for path in mockup_output_paths:
        assert "mockup_CompA" in path, f"Expected mockup_CompA in path: {path}"
        assert "CompA" in path, f"Component subdirectory not found in mockup path: {path}"


def test_executable_output_directory_is_set(execution_context: ExecutionContext, output_dir: Path) -> None:
    """Verify that executables are configured to output to component-specific directories."""
    elements = GTestCMakeGenerator(execution_context, output_dir).generate()

    # Import the target properties class for type checking
    from yanga.cmake.cmake_backend import CMakeSetTargetProperties

    # Find CMakeSetTargetProperties elements
    target_properties = find_elements_of_type(elements, CMakeSetTargetProperties)
    assert len(target_properties) > 0, "No target properties found"

    # Find the properties for CompA executable
    comp_a_properties = [tp for tp in target_properties if tp.target == "CompA"]
    assert len(comp_a_properties) == 1, f"Expected 2 target properties for CompA (runtime and discovery), found {len(comp_a_properties)}"

    # Find the runtime output directory property
    runtime_props = [tp for tp in comp_a_properties if "RUNTIME_OUTPUT_DIRECTORY" in tp.properties]
    assert len(runtime_props) == 1, "RUNTIME_OUTPUT_DIRECTORY property not found"

    runtime_dir = str(runtime_props[0].properties["RUNTIME_OUTPUT_DIRECTORY"])
    assert "CompA" in runtime_dir, f"Component subdirectory not found in runtime output directory: {runtime_dir}"


def test_component_mocking_config_overrides_global(execution_context: ExecutionContext, output_dir: Path) -> None:
    """Verify that component-specific mocking configuration overrides global mocking settings."""
    global_mocking_config = GTestCMakeGeneratorConfig.from_dict({"mocking": {"enabled": True, "exclude_symbol_patterns": ["GlobalPattern1", "GlobalPattern2"], "strict": False}})
    component = Component(
        name="CompA",
        path=Path("CompA"),
        sources=[],
        testing=TestingConfiguration(sources=["test_compA_source.cpp"], mocking=MockingConfiguration(exclude_symbol_patterns=["CompAPattern1"], strict=True)),
    )
    generator = GTestComponentCMakeGenerator(execution_context, output_dir, global_mocking_config)

    config = generator._determine_component_generator_config(component)

    assert config.mocking is not None
    assert config.mocking.enabled is True, "Inherited global mocking enabled"
    assert config.mocking.exclude_symbol_patterns == ["CompAPattern1"], "Overridden exclude patterns"
    assert config.mocking.strict is True, "Overridden strict setting"
