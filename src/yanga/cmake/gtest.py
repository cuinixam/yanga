from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Optional

from mashumaro import DataClassDictMixin

from yanga.domain.component_analyzer import ComponentAnalyzer
from yanga.domain.components import Component
from yanga.domain.config import MockingConfiguration
from yanga.domain.execution_context import (
    ExecutionContext,
    UserRequest,
    UserRequestScope,
    UserRequestTarget,
)

from .cmake_backend import (
    CMakeAddExecutable,
    CMakeAddSubdirectory,
    CMakeCommand,
    CMakeComment,
    CMakeCustomCommand,
    CMakeCustomTarget,
    CMakeElement,
    CMakeEmptyLine,
    CMakeIncludeDirectories,
    CMakeObjectLibrary,
    CMakePath,
    CMakeSetTargetProperties,
    CMakeTargetIncludeDirectories,
    CMakeVariable,
)
from .generator import CMakeGenerator


@dataclass
class GTestCMakeGeneratorConfig(DataClassDictMixin):
    #: If this is enabled, all includes are defined globally and not component specific
    use_global_includes: bool = False
    #: Mocking configuration
    mocking: Optional[MockingConfiguration] = None

    @property
    def automock(self) -> bool:
        if self.mocking and self.mocking.enabled is not None:
            return self.mocking.enabled
        return True


class GTestCMakeArtifactsLocator:
    """Defines the paths to the CMake artifacts."""

    def __init__(self, output_dir: Path, execution_context: ExecutionContext) -> None:
        # The directory where the build files will be generated
        self.artifacts_locator = execution_context.create_artifacts_locator()
        self.cmake_build_dir = CMakePath(output_dir, "CMAKE_BUILD_DIR")
        self.cmake_gtest_dir = CMakePath(self.artifacts_locator.locate_artifact("gtest", [self.artifacts_locator.build_dir]))

    def get_component_build_dir(self, component_name: str) -> CMakePath:
        """Get the component-specific build directory."""
        return self.cmake_build_dir.joinpath(component_name)


class GTestCMakeComponent:
    def __init__(self, component: Component, execution_context: ExecutionContext) -> None:
        self.component = component
        self.execution_context = execution_context
        self.component_analyzer = ComponentAnalyzer([self.component], self.execution_context.create_artifacts_locator())

    @property
    def name(self) -> str:
        return self.component.name

    @property
    def executable_name(self) -> str:
        """The name of the component test executable used to run the tests."""
        return self.component.name

    @property
    def partial_link_name(self) -> str:
        """
        The name of the component partial link library containing only the productive sources.

        Required to determine the required mocks for  the component.
        """
        return f"{self.component.name}_PC"

    def is_testable(self) -> bool:
        return self.component_analyzer.is_testable()

    def get_include_directories(self) -> list[CMakePath]:
        """TODO: Every component shall define its own dependencies. Collecting all include directories is not correct."""
        collector = ComponentAnalyzer(
            self.execution_context.components,
            self.execution_context.create_artifacts_locator(),
        )
        include_dirs = collector.collect_include_directories() + self.execution_context.include_directories
        return [CMakePath(path) for path in include_dirs]


class CMakeMockupCreator:
    def __init__(self, gtest_cmake_component: GTestCMakeComponent, artifacts_locator: GTestCMakeArtifactsLocator, mocking_config: Optional[MockingConfiguration]):
        self.artifacts_locator = artifacts_locator
        self.gtest_cmake_component = gtest_cmake_component
        self.mocking_config = mocking_config

    def generate(self) -> list[CMakeElement]:
        elements: list[CMakeElement] = []
        # Create the partial link library containing only the productive sources to be able to find the required mocks
        sources = [CMakePath(source) for source in self.gtest_cmake_component.component_analyzer.collect_sources()]
        component_sources_object_library = CMakeObjectLibrary(self.gtest_cmake_component.partial_link_name, self.gtest_cmake_component.component_analyzer.collect_sources())
        elements.append(component_sources_object_library)
        # Add include directories specific to this component
        include_dirs: list[CMakePath] = self.gtest_cmake_component.get_include_directories()
        # Add the component-specific build directory for the component to find the generated mockup sources
        component_build_dir = self.artifacts_locator.get_component_build_dir(self.gtest_cmake_component.name)
        include_dirs.append(component_build_dir)
        if include_dirs:
            # Determine visibility: use PRIVATE for libraries with sources, INTERFACE for header-only
            visibility = "INTERFACE" if not sources else "PRIVATE"
            target_includes = CMakeTargetIncludeDirectories(component_sources_object_library.target_name, include_dirs, visibility)
            elements.append(target_includes)
        # Custom command to create the partial link library
        partial_link_obj = component_build_dir.joinpath(f"{self.gtest_cmake_component.partial_link_name}.o")
        custom_command = CMakeCustomCommand(
            "Create partial link library containing only the productive sources",
            [partial_link_obj],
            [component_sources_object_library.target_name],
            [
                CMakeCommand(
                    "${CMAKE_CXX_COMPILER}",
                    [
                        "-r",
                        "-nostdlib",
                        "-o",
                        partial_link_obj,
                        f"$<TARGET_OBJECTS:{component_sources_object_library.target_name}>",
                    ],
                )
            ],
        )
        elements.append(custom_command)
        # Custom command to run clanguru and generate the mockup sources
        clanguru_args = []
        if self.mocking_config:
            clanguru_args.append("--strict" if self.mocking_config.strict else "--no-strict")
            if self.mocking_config.exclude_symbol_patterns:
                for pattern in self.mocking_config.exclude_symbol_patterns:
                    clanguru_args.extend(["--exclude-symbol-pattern", f'"{pattern}"'])

        generate_mockup_cmake_cmd = CMakeCustomCommand(
            description="Run clanguru to generate mockup sources",
            outputs=[CMakePath(file) for file in self.get_mockup_generated_files()],
            depends=[partial_link_obj],
            commands=[
                CMakeCommand(
                    "clanguru",
                    [
                        "mock",
                        "--filename",
                        f"mockup_{self.gtest_cmake_component.component.name}",
                        *[f"--source-file {source}" for source in sources],
                        "--partial-object-file",
                        partial_link_obj,
                        "--output-dir",
                        component_build_dir,
                        "--compilation-database",
                        self.artifacts_locator.cmake_build_dir.joinpath("compile_commands.json"),
                        *clanguru_args,
                    ],
                )
            ],
        )
        elements.append(generate_mockup_cmake_cmd)
        # Add custom target for the mockup generation
        elements.append(
            CMakeCustomTarget(
                UserRequest(
                    UserRequestScope.COMPONENT,
                    component_name=self.gtest_cmake_component.name,
                    target=UserRequestTarget.MOCKUP,
                ).target_name,
                f"Generate mockup sources for {self.gtest_cmake_component.name}",
                [],
                generate_mockup_cmake_cmd.outputs,  # type: ignore
            )
        )
        return elements

    def get_mockup_generated_files(self) -> list[Path]:
        return [self.get_mockup_file("log"), self.get_mockup_file("h"), *self.get_mockup_sources()]

    def get_mockup_sources(self) -> list[Path]:
        return [self.get_mockup_file("cc")]

    def get_mockup_file(self, file_extension: str) -> Path:
        component_build_dir = self.artifacts_locator.get_component_build_dir(self.gtest_cmake_component.name)
        return component_build_dir.joinpath(f"mockup_{self.gtest_cmake_component.name}.{file_extension}").to_path()


class GTestComponentCMakeGenerator:
    def __init__(self, execution_context: ExecutionContext, output_dir: Path, config: GTestCMakeGeneratorConfig) -> None:
        self.execution_context = execution_context
        self.artifacts_locator = GTestCMakeArtifactsLocator(output_dir, execution_context)
        self.config = config

    def generate(self, component: Component) -> list[CMakeElement]:
        component_generator_config = self._determine_component_generator_config(component)

        gtest_cmake_component = GTestCMakeComponent(component, self.execution_context)
        component_analyzer = gtest_cmake_component.component_analyzer
        mockup_generator = None
        if component_generator_config.automock:
            mockup_generator = CMakeMockupCreator(gtest_cmake_component, self.artifacts_locator, component_generator_config.mocking)
        # Skip components without tests
        if not component_analyzer.is_testable():
            return []
        elements: list[CMakeElement] = []
        elements.append(CMakeComment(f"Component {component.name}"))

        # Create the component executable
        sources = component_analyzer.collect_sources() + component_analyzer.collect_test_sources()
        if mockup_generator:
            sources += mockup_generator.get_mockup_sources()
        test_executable = self.add_executable(gtest_cmake_component.executable_name, sources)
        elements.append(test_executable)

        # Set the executable output directory to the component-specific directory
        component_build_dir = self.artifacts_locator.get_component_build_dir(component.name)
        target_properties = CMakeSetTargetProperties(test_executable.name, {"RUNTIME_OUTPUT_DIRECTORY": component_build_dir})
        elements.append(target_properties)

        # Add component-specific include directories when global includes are disabled
        if not component_generator_config.use_global_includes:
            include_dirs: list[CMakePath] = gtest_cmake_component.get_include_directories()
            # Add the component-specific build directory for the component to find the generated mockup sources
            component_build_dir = self.artifacts_locator.get_component_build_dir(component.name)
            include_dirs.append(component_build_dir)
            if include_dirs:
                # Determine visibility: use PRIVATE for executables with sources, INTERFACE for header-only
                visibility = "INTERFACE" if not sources else "PRIVATE"
                target_includes = CMakeTargetIncludeDirectories(test_executable.name, include_dirs, visibility)
                elements.append(target_includes)

        # Create the custom target to execute the tests
        execute_tests_command = self.run_executable(component.name, test_executable.name)
        elements.append(execute_tests_command)

        # Create the component mockup sources
        if mockup_generator:
            elements.extend(mockup_generator.generate())

        # Create the component custom targets
        elements.extend(
            [
                CMakeCustomTarget(
                    UserRequest(
                        UserRequestScope.COMPONENT,
                        component_name=component.name,
                        target=UserRequestTarget.TEST,
                    ).target_name,
                    f"Execute tests for {component.name}",
                    [],
                    execute_tests_command.outputs,  # type: ignore
                    True,
                ),
                CMakeCustomTarget(
                    UserRequest(
                        UserRequestScope.COMPONENT,
                        component_name=component.name,
                        target=UserRequestTarget.BUILD,
                    ).target_name,
                    f"Execute tests for {component.name}",
                    [],
                    execute_tests_command.outputs,  # type: ignore
                    True,
                ),
            ]
        )
        elements.append(CMakeEmptyLine())

        return elements

    def _determine_component_generator_config(self, component: Component) -> GTestCMakeGeneratorConfig:
        """Take over the component mocking configuration over the global generator configuration."""
        result = self.config
        if component.testing and component.testing.mocking:
            if not result.mocking:
                result.mocking = component.testing.mocking
            else:
                if component.testing.mocking.enabled is not None:
                    result.mocking.enabled = component.testing.mocking.enabled
                if component.testing.mocking.exclude_symbol_patterns:
                    result.mocking.exclude_symbol_patterns = component.testing.mocking.exclude_symbol_patterns
        return result

    def add_executable(self, component_name: str, sources: list[Path]) -> CMakeAddExecutable:
        return CMakeAddExecutable(
            f"{component_name}",
            [CMakePath(source) for source in sources],
            ["GTest::gtest_main", "GTest::gmock_main", "pthread"],
            [
                "-ggdb",  # Include detailed debug information to be able to debug the executable.
                "--coverage",  # Enable coverage tracking information to be generated.
            ],
            ["--coverage"],  # Enable coverage analysis.
        )

    def run_executable(self, component_name: str, component_executable_name: str) -> CMakeCustomCommand:
        component_build_dir = self.artifacts_locator.get_component_build_dir(component_name)
        junit_report_file = component_build_dir.joinpath(f"{component_name}_junit.xml")
        # The executable will be in the component-specific directory
        executable_path = component_build_dir.joinpath(component_executable_name)
        command = CMakeCommand(
            executable_path,
            [
                f"--gtest_output=xml:{junit_report_file}",
                "||",
                "${CMAKE_COMMAND}",
                "-E",
                "true",
            ],
        )
        outputs = [component_build_dir.joinpath(f"{component_name}_junit.xml")]
        return CMakeCustomCommand(
            "Run the test executable, generate JUnit report and return success independent of the test result",
            outputs,
            [component_executable_name],
            [command],
        )


class GTestCMakeGenerator(CMakeGenerator):
    """Generates CMake elements to build an executable for a variant."""

    def __init__(self, execution_context: ExecutionContext, output_dir: Path, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__(execution_context, output_dir, config)
        self.artifacts_locator = GTestCMakeArtifactsLocator(output_dir, execution_context)

    @property
    def variant_name(self) -> Optional[str]:
        return self.execution_context.variant_name

    @cached_property
    def config_obj(self) -> GTestCMakeGeneratorConfig:
        """Lazily creates and caches a GTestCMakeGeneratorConfig instance."""
        return GTestCMakeGeneratorConfig.from_dict(self.config) if self.config else GTestCMakeGeneratorConfig()

    def generate(self) -> list[CMakeElement]:
        elements: list[CMakeElement] = []
        elements.append(CMakeComment(f"Generated by {self.__class__.__name__}"))
        # configure cmake to generate compile commands
        elements.append(CMakeVariable("CMAKE_EXPORT_COMPILE_COMMANDS", "ON", True, "BOOL", "", True))
        elements.extend(self.create_variant_cmake_elements())
        elements.extend(self.create_components_cmake_elements())
        return elements

    def create_variant_cmake_elements(self) -> list[CMakeElement]:
        elements: list[CMakeElement] = []
        elements.append(CMakeVariable("CMAKE_CXX_STANDARD", "14"))
        elements.append(CMakeVariable("CMAKE_CXX_STANDARD_REQUIRED", "ON"))
        elements.append(CMakeVariable("gtest_force_shared_crt", "ON", True, "BOOL", "", True))
        cmake_build_dir_var = self.artifacts_locator.cmake_build_dir.to_cmake_element()
        if cmake_build_dir_var:
            elements.append(cmake_build_dir_var)
        elements.append(CMakeComment("Add local GoogleTest directory"))
        elements.append(
            CMakeAddSubdirectory(
                self.artifacts_locator.cmake_gtest_dir,
                self.artifacts_locator.cmake_build_dir.joinpath(".gtest"),
            )
        )
        if self.config_obj.use_global_includes:
            elements.append(self.get_include_directories())
        else:
            elements.append(CMakeComment("Use global includes for all components disabled."))
        return elements

    def get_include_directories(self) -> CMakeIncludeDirectories:
        collector = ComponentAnalyzer(
            self.execution_context.components,
            self.execution_context.create_artifacts_locator(),
        )
        include_dirs = collector.collect_include_directories() + self.execution_context.include_directories
        # Add the GTest and GMock include directory
        for name in ["googletest", "googlemock"]:
            include_dirs.append(self.artifacts_locator.cmake_gtest_dir.joinpath(f"{name}/include").to_path())
        # Add the component-specific build directories to the include directories to be able to include the generated mockup sources
        for component in self.execution_context.components:
            component_build_dir = self.artifacts_locator.get_component_build_dir(component.name)
            include_dirs.append(component_build_dir.to_path())
        return CMakeIncludeDirectories([CMakePath(path) for path in include_dirs])

    def create_components_cmake_elements(self) -> list[CMakeElement]:
        elements: list[CMakeElement] = []
        component_generator = GTestComponentCMakeGenerator(self.execution_context, self.output_dir, self.config_obj)
        for component in self.execution_context.components:
            elements.extend(component_generator.generate(component))
        return elements
