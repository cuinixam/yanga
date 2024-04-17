from pathlib import Path
from typing import List, Optional

from yanga.domain.component_analyzer import ComponentAnalyzer
from yanga.domain.components import Component
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
    CMakeContent,
    CMakeCustomCommand,
    CMakeCustomTarget,
    CMakeElement,
    CMakeEmptyLine,
    CMakeEnableTesting,
    CMakeInclude,
    CMakeIncludeDirectories,
    CMakeListAppend,
    CMakeObjectLibrary,
    CMakePath,
    CMakeVariable,
)
from .generator import CMakeGenerator


class GTestCMakeArtifactsLocator:
    """Defines the paths to the CMake artifacts."""

    def __init__(self, output_dir: Path, execution_context: ExecutionContext) -> None:
        # The directory where the build files will be generated
        self.artifacts_locator = execution_context.create_artifacts_locator()
        self.cmake_build_dir = CMakePath(output_dir, "CMAKE_BUILD_DIR")
        self.cmake_gtest_dir = CMakePath(self.artifacts_locator.locate_artifact("external/gtest", [self.artifacts_locator.build_dir]))


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
        """The name of the component partial link library containing only the productive sources.
        Required to determine the required mocks for  the component."""
        return f"{self.component.name}_PC"

    def is_testable(self) -> bool:
        return self.component_analyzer.is_testable()

    def get_include_directories(self) -> List[CMakePath]:
        """TODO: Every component shall define its own dependencies. Collecting all include directories is not correct."""
        collector = ComponentAnalyzer(
            self.execution_context.components,
            self.execution_context.create_artifacts_locator(),
        )
        include_dirs = collector.collect_include_directories() + self.execution_context.include_directories
        return [CMakePath(path) for path in include_dirs]


class Hammocking:
    def __init__(self, gtest_cmake_component: GTestCMakeComponent, artifacts_locator: GTestCMakeArtifactsLocator):
        self.artifacts_locator = artifacts_locator
        self.gtest_cmake_component = gtest_cmake_component

    def generate(self) -> List[CMakeElement]:
        elements: List[CMakeElement] = []
        # Create the partial link library containing only the productive sources to be able to find the required mocks
        sources = [CMakePath(source) for source in self.gtest_cmake_component.component_analyzer.collect_sources()]
        component_sources_object_library = CMakeObjectLibrary(self.gtest_cmake_component.partial_link_name, self.gtest_cmake_component.component_analyzer.collect_sources())
        elements.append(component_sources_object_library)
        # Custom command to create the partial link library
        partial_link_obj = self.artifacts_locator.cmake_build_dir.joinpath(f"{self.gtest_cmake_component.partial_link_name}.o")
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
        # Custom command to run hammocking and generate the mockup sources
        generate_mockup_cmake_cmd = CMakeCustomCommand(
            description="Run hammocking to generate mockup sources",
            outputs=[CMakePath(file) for file in self.get_mockup_generated_files()],
            depends=[partial_link_obj],
            commands=[
                CMakeCommand(
                    "python -m hammocking",
                    [
                        "--suffix",
                        f"_{self.gtest_cmake_component.component.name}",
                        "--sources",
                        " ".join(str(source) for source in sources),
                        "--plink",
                        partial_link_obj,
                        "--outdir",
                        self.artifacts_locator.cmake_build_dir,
                        " ".join(["-I" + str(source) for source in self.gtest_cmake_component.get_include_directories()]),
                        "-x",
                        "c",
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

    def get_mockup_generated_files(self) -> List[Path]:
        return [self.get_mockup_file("h"), *self.get_mockup_sources()]

    def get_mockup_sources(self) -> List[Path]:
        return [self.get_mockup_file("cc")]

    def get_mockup_file(self, file_extension: str) -> Path:
        return self.artifacts_locator.cmake_build_dir.joinpath(f"mockup_{self.gtest_cmake_component.name}.{file_extension}").to_path()


class GTestComponentCMakeGenerator:
    def __init__(self, execution_context: ExecutionContext, output_dir: Path):
        self.execution_context = execution_context
        self.artifacts_locator = GTestCMakeArtifactsLocator(output_dir, execution_context)

    def generate(self, component: Component) -> List[CMakeElement]:
        gtest_cmake_component = GTestCMakeComponent(component, self.execution_context)
        component_analyzer = gtest_cmake_component.component_analyzer
        mockup_generator = Hammocking(gtest_cmake_component, self.artifacts_locator)
        # Skip components without tests
        if not component_analyzer.is_testable():
            return []
        elements: List[CMakeElement] = []
        elements.append(CMakeComment(f"Component {component.name}"))

        # Create the component executable
        sources = component_analyzer.collect_sources() + component_analyzer.collect_test_sources() + mockup_generator.get_mockup_sources()
        test_executable = self.add_executable(gtest_cmake_component.executable_name, sources)
        elements.append(test_executable)

        # Create the custom target to execute the tests
        execute_tests_command = self.run_executable(component.name, test_executable.name)
        elements.append(execute_tests_command)

        # Create the component mockup sources
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
        elements.append(CMakeContent(f"gtest_discover_tests({test_executable.name})"))
        elements.append(CMakeEmptyLine())

        return elements

    def add_executable(self, component_name: str, sources: List[Path]) -> CMakeAddExecutable:
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
        command = CMakeCommand(
            "${CMAKE_CTEST_COMMAND}",
            [
                "${CMAKE_CTEST_ARGUMENTS}",
                "--output-junit",
                f"{component_name}_junit.xml",
                "||",
                "${CMAKE_COMMAND}",
                "-E",
                "true",
            ],
        )
        outputs = [self.artifacts_locator.cmake_build_dir.joinpath(f"{component_name}_junit.xml")]
        return CMakeCustomCommand(
            "Run the test executable, generate JUnit report and return success independent of the test result",
            outputs,
            [component_executable_name],
            [command],
        )


class GTestCMakeGenerator(CMakeGenerator):
    """Generates CMake elements to build an executable for a variant."""

    def __init__(self, execution_context: ExecutionContext, output_dir: Path) -> None:
        super().__init__(execution_context, output_dir)
        self.artifacts_locator = GTestCMakeArtifactsLocator(output_dir, execution_context)

    @property
    def variant_name(self) -> Optional[str]:
        return self.execution_context.variant_name

    def generate(self) -> List[CMakeElement]:
        elements: List[CMakeElement] = []
        elements.append(CMakeComment(f"Generated by {self.__class__.__name__}"))
        elements.extend(self.create_variant_cmake_elements())
        elements.extend(self.create_components_cmake_elements())
        return elements

    def create_variant_cmake_elements(self) -> List[CMakeElement]:
        elements: List[CMakeElement] = []
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
        elements.append(CMakeInclude("GoogleTest"))
        elements.append(CMakeComment("Enable testing"))
        elements.append(CMakeInclude("CTest"))
        elements.append(CMakeListAppend("CMAKE_CTEST_ARGUMENTS", ["--output-on-failure"]))
        elements.append(CMakeEnableTesting())
        elements.append(self.get_include_directories())
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
        # Add the build directory to the include directories to be able to include the generated mockup sources
        include_dirs.append(self.artifacts_locator.cmake_build_dir.to_path())
        return CMakeIncludeDirectories([CMakePath(path) for path in include_dirs])

    def create_components_cmake_elements(self) -> List[CMakeElement]:
        elements: List[CMakeElement] = []
        component_generator = GTestComponentCMakeGenerator(self.execution_context, self.output_dir)
        for component in self.execution_context.components:
            elements.extend(component_generator.generate(component))
        return elements
