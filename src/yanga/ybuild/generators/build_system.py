from enum import Enum, auto
from pathlib import Path
from typing import Any, List

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger

from yanga.ybuild.backends.cmake import (
    CMakeAddExecutable,
    CMakeAddSubdirectory,
    CMakeCommand,
    CMakeComment,
    CMakeContent,
    CMakeCustomCommand,
    CMakeCustomTarget,
    CMakeEmptyLine,
    CMakeEnableTesting,
    CMakeExecuteProcess,
    CMakeFile,
    CMakeInclude,
    CMakeIncludeDirectories,
    CMakeListAppend,
    CMakeMinimumVersion,
    CMakeObjectLibrary,
    CMakePath,
    CMakeProject,
    CMakeVariable,
)
from yanga.ybuild.components import BuildComponent
from yanga.ybuild.generators.build_system_request import (
    BuildVariantRequest,
    CompileComponentRequest,
    TestComponentRequest,
    TestVariantRequest,
)

from ..backends.generated_file import GeneratedFile
from ..environment import BuildEnvironment


def make_list_unique(seq: List[Any]) -> List[Any]:
    return list(dict.fromkeys(seq))


class BuildSystemBackend(Enum):
    CMAKE = auto()
    NINJA = auto()


class BuildComponentAnalyzer:
    def __init__(self, components: List[BuildComponent]) -> None:
        self.components = components

    def collect_sources(self) -> List[Path]:
        files: List[Path] = []
        for component in self.components:
            files.extend([component.path.joinpath(source) for source in component.sources])
        return files

    def collect_test_sources(self) -> List[Path]:
        files: List[Path] = []
        for component in self.components:
            files.extend([component.path.joinpath(source) for source in component.test_sources])
        return files

    def collect_include_directories(self) -> List[Path]:
        # TODO: check if there are specific include directories for each component
        includes = [path.parent for path in self.collect_sources()]
        # remove duplicates and return
        return make_list_unique(includes)

    def get_testable_components(self) -> List[BuildComponent]:
        return [component for component in self.components if component.test_sources]

    def is_testable(self) -> bool:
        return any(component.test_sources for component in self.components)


class BuildSystemGenerator:
    def __init__(
        self,
        backend: BuildSystemBackend,
        environment: BuildEnvironment,
        output_dir: Path,
    ):
        self.logger = logger.bind()
        self.backend = backend
        self.environment = environment
        self.output_dir = output_dir
        self.output_test_dir = output_dir.joinpath("test")

    def generate(self) -> List[GeneratedFile]:
        files = []
        if self.backend == BuildSystemBackend.CMAKE:
            files.extend(CmakeBuildFilesGenerator(self.environment, self.output_dir).generate())
            if BuildComponentAnalyzer(self.environment.components).is_testable():
                self.logger.info("Generating test build files")
                files.extend(CmakeTestFilesGenerator(self.environment, self.output_test_dir).generate())
        else:
            raise UserNotificationException("Only CMake build system files generation is supported for now")
        # TODO: CMakeFile objects are GeneratedFile objects. Try to fix warning without ignoring type check
        return files  # type: ignore


class CmakeBuildFilesGenerator:
    """Generates CMakeLists.txt, variant.cmake, and components.cmake files
    for building the variant for a specific platform.
    """

    def __init__(self, environment: BuildEnvironment, output_dir: Path) -> None:
        self.environment = environment
        self.output_dir = output_dir
        # The directory where the CMakeLists.txt file is located
        self.cmake_current_list_dir = CMakePath(self.output_dir, "CMAKE_CURRENT_LIST_DIR")
        # The directory where the build files will be generated
        self.cmake_build_dir = CMakePath(self.output_dir / "build", "CMAKE_BUILD_DIR")

    @property
    def variant_name(self) -> str:
        return self.environment.variant_name

    @property
    def variant_cmake_file(self) -> CMakePath:
        return self.cmake_current_list_dir.joinpath("variant.cmake")

    @property
    def components_cmake_file(self) -> CMakePath:
        return self.cmake_current_list_dir.joinpath("components.cmake")

    def generate(self) -> List[CMakeFile]:
        return [self.create_cmake_lists(), self.create_variants_cmake(), self.create_components_cmake()]

    def create_cmake_lists(self) -> CMakeFile:
        cmake_file = CMakeFile(self.output_dir.joinpath("CMakeLists.txt"))
        cmake_file.append(CMakeMinimumVersion("3.20"))
        cmake_file.append(CMakeProject(self.variant_name))
        cmake_file.append(CMakeInclude(self.variant_cmake_file))
        return cmake_file

    def create_variants_cmake(self) -> CMakeFile:
        cmake_file = CMakeFile(self.variant_cmake_file.to_path())
        vars = {"CMAKE_CXX_STANDARD": "99", "CMAKE_C_COMPILER": "clang", "CMAKE_CXX_COMPILER": "clang++"}
        for var, value in vars.items():
            cmake_file.append(CMakeVariable(var, value))
        cmake_file.append(CMakeInclude(self.components_cmake_file))
        cmake_file.append(self.get_include_directories())
        # TODO: I do not like that I have to know here that the components are object libraries
        variant_executable = CMakeAddExecutable(
            "${PROJECT_NAME}",
            sources=[],
            libraries=[CMakeObjectLibrary(component.name).target_name for component in self.environment.components],
        )

        cmake_file.append(variant_executable)
        cmake_file.append(
            CMakeCustomTarget(
                BuildVariantRequest(self.variant_name).target_name,
                f"Build variant {self.variant_name}",
                [],
                [variant_executable.name],
            )
        )
        if BuildComponentAnalyzer(self.environment.components).is_testable():
            # TODO: this is a command for calling a cmake runner.
            # Use the CMakeRunner class somehow otherwise the command options will be duplicated
            command = CMakeCommand(
                "${CMAKE_COMMAND}",
                [
                    "-S",
                    self.cmake_current_list_dir.joinpath("test"),
                    "-B",
                    self.cmake_current_list_dir.joinpath("test/build"),
                    "-G",
                    "Ninja",
                ],
            )
            cmake_file.append(CMakeExecuteProcess("Configure the test cmake project", [command]))
            test_variant_target = TestVariantRequest(self.variant_name).target_name
            command = CMakeCommand(
                "${CMAKE_COMMAND}",
                [
                    "--build",
                    self.cmake_current_list_dir.joinpath("test/build"),
                    "--target",
                    test_variant_target,
                ],
            )
            cmake_file.append(
                CMakeCustomTarget(
                    test_variant_target,
                    "Running all tests",
                    [command],
                )
            )
        else:
            cmake_file.append(CMakeComment("Skip including test project. No testable components found."))
        return cmake_file

    def get_include_directories(self) -> CMakeIncludeDirectories:
        collector = BuildComponentAnalyzer(self.environment.components)
        include_dirs = collector.collect_include_directories() + self.environment.include_directories
        return CMakeIncludeDirectories([CMakePath(path) for path in include_dirs])

    def create_components_cmake(self) -> CMakeFile:
        cmake_file = CMakeFile(self.components_cmake_file.to_path())
        for component in self.environment.components:
            component_analyzer = BuildComponentAnalyzer([component])
            component_library = CMakeObjectLibrary(component.name, component_analyzer.collect_sources())
            cmake_file.append(component_library)
            cmake_file.append(
                CMakeCustomTarget(
                    CompileComponentRequest(self.variant_name, component.name).target_name,
                    f"Compile component {component.name}",
                    [],
                    [component_library.target_name],
                )
            )
            if component_analyzer.is_testable():
                command = CMakeCommand(
                    "${CMAKE_COMMAND}",
                    [
                        "--build",
                        self.cmake_current_list_dir.joinpath("test/build"),
                        "--target",
                        f"{component.name}_test",
                    ],
                )
                cmake_file.append(
                    CMakeCustomTarget(
                        f"{component.name}_test",
                        f"Running {component.name}_test",
                        [command],
                    )
                )
        return cmake_file


class CmakeTestFilesGenerator:
    """Generates CMakeLists.txt, variant.cmake, and components.cmake files
    for running tests on the variant and its components."""

    def __init__(self, environment: BuildEnvironment, output_dir: Path) -> None:
        self.environment = environment
        self.output_dir = output_dir
        # The directory where the CMakeLists.txt file is located
        self.cmake_source_dir = CMakePath(self.output_dir, "CMAKE_CURRENT_LIST_DIR")
        # The directory where the build files will be generated
        self.cmake_build_dir = CMakePath(self.output_dir, "CMAKE_BUILD_DIR", Path("build"))

    @property
    def variant_name(self) -> str:
        return self.environment.variant_name

    @property
    def variant_cmake_file(self) -> CMakePath:
        return self.cmake_source_dir.joinpath("variant.cmake")

    @property
    def components_cmake_file(self) -> CMakePath:
        return self.cmake_source_dir.joinpath("components.cmake")

    def generate(self) -> List[CMakeFile]:
        return [self.create_cmake_lists(), self.create_variants_cmake(), self.create_components_cmake()]

    def create_cmake_lists(self) -> CMakeFile:
        cmake_file = CMakeFile(self.output_dir.joinpath("CMakeLists.txt"))
        cmake_file.append(CMakeMinimumVersion("3.20"))
        cmake_file.append(CMakeProject(self.variant_name))
        cmake_file.append(CMakeInclude(self.variant_cmake_file))
        return cmake_file

    def create_variants_cmake(self) -> CMakeFile:
        cmake_file = CMakeFile(self.variant_cmake_file.to_path())
        cmake_file.append(CMakeVariable("CMAKE_CXX_STANDARD", "14"))
        cmake_file.append(CMakeVariable("CMAKE_CXX_STANDARD_REQUIRED", "ON"))
        cmake_file.append(CMakeVariable("gtest_force_shared_crt", "ON", True, "BOOL", "", True))
        cmake_file.append(CMakeComment("Add local GoogleTest directory"))
        cmake_file.append(
            CMakeAddSubdirectory(
                self.cmake_source_dir.joinpath("../../../external/gtest"),
                self.cmake_build_dir.joinpath(".gtest"),
            )
        )
        cmake_file.append(CMakeInclude("GoogleTest"))
        cmake_file.append(CMakeComment("Enable testing"))
        cmake_file.append(CMakeInclude("CTest"))
        cmake_file.append(CMakeListAppend("CMAKE_CTEST_ARGUMENTS", ["--output-on-failure"]))
        cmake_file.append(CMakeEnableTesting())
        cmake_file.append(CMakeInclude(self.components_cmake_file))
        cmake_file.append(self.get_include_directories())
        return cmake_file

    def get_include_directories(self) -> CMakeIncludeDirectories:
        collector = BuildComponentAnalyzer(self.environment.components)
        include_dirs = collector.collect_include_directories() + self.environment.include_directories
        return CMakeIncludeDirectories([CMakePath(path) for path in include_dirs])

    def create_components_cmake(self) -> CMakeFile:
        cmake_file = CMakeFile(self.components_cmake_file.to_path())
        for component in self.environment.components:
            component_analyzer = BuildComponentAnalyzer([component])
            # Skip components without tests
            if not component_analyzer.is_testable():
                continue
            cmake_file.append(CMakeComment(f"Component {component.name}"))
            sources = component_analyzer.collect_sources() + component_analyzer.collect_test_sources()
            component_test_executable_target = f"{component.name}_build_test_executable"
            cmake_file.append(
                CMakeAddExecutable(
                    component_test_executable_target,
                    [CMakePath(source) for source in sources],
                    ["GTest::gtest_main"],
                    [
                        "-ggdb",  # Include detailed debug information to be able to debug the executable.
                        "--coverage",  # Enable coverage tracking information to be generated.
                    ],
                    ["--coverage"],  # Enable coverage analysis.
                )
            )
            command = CMakeCommand(
                "${CMAKE_CTEST_COMMAND}",
                [
                    "${CMAKE_CTEST_ARGUMENTS}",
                    "--output-junit",
                    f"{component.name}_junit.xml",
                    "||",
                    "${CMAKE_COMMAND}",
                    "-E",
                    "true",
                ],
            )
            outputs = [self.cmake_build_dir.joinpath(f"{component.name}_junit.xml")]
            cmake_file.append(
                CMakeCustomCommand(
                    "Run the test executable, generate JUnit report and return success independent of the test result",
                    outputs,
                    [component_test_executable_target],
                    [command],
                )
            )
            cmake_file.append(
                CMakeCustomTarget(
                    TestComponentRequest(self.variant_name, component.name).target_name,
                    f"Execute tests for {component.name}",
                    [],
                    outputs,  # type: ignore
                    True,
                )
            )
            cmake_file.append(CMakeContent(f"gtest_discover_tests({component_test_executable_target})"))
            cmake_file.append(CMakeEmptyLine())
        return cmake_file
