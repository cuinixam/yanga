from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Optional

from mashumaro import DataClassDictMixin

from yanga.cmake.artifacts_locator import BuildArtifact, CMakeArtifactsLocator
from yanga.cmake.coverage import CoverageArtifactsLocator, CoverageRelevantFile
from yanga.domain.artifacts import ProjectArtifactsLocator
from yanga.domain.component_analyzer import ComponentAnalyzer
from yanga.domain.components import Component
from yanga.domain.config import MockingConfiguration
from yanga.domain.execution_context import (
    ExecutionContext,
    UserRequest,
    UserRequestScope,
    UserRequestTarget,
)
from yanga.domain.reports import ReportRelevantFiles, ReportRelevantFileType

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


class GTestCMakeArtifactsLocator(CMakeArtifactsLocator):
    """Defines the paths to the CMake artifacts for GTest."""

    def __init__(self, output_dir: Path, project_artifact_locator: ProjectArtifactsLocator) -> None:
        super().__init__(output_dir, project_artifact_locator)
        self.cmake_gtest_dir = CMakePath(self.artifacts_locator.locate_artifact("gtest", [self.artifacts_locator.build_dir]))


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
        collector = ComponentAnalyzer(
            self.execution_context.components,
            self.execution_context.create_artifacts_locator(),
        )
        include_dirs = collector.collect_include_directories() + self.execution_context.include_directories
        return [CMakePath(path) for path in include_dirs]


class CMakeMockupCreator:
    def __init__(
        self,
        gtest_cmake_component: GTestCMakeComponent,
        component_object_library_target: str,
        artifacts_locator: GTestCMakeArtifactsLocator,
        mocking_config: Optional[MockingConfiguration],
    ):
        self.artifacts_locator = artifacts_locator
        self.gtest_cmake_component = gtest_cmake_component
        self.mocking_config = mocking_config
        self.component_object_library_target = component_object_library_target

    def generate(self) -> list[CMakeElement]:
        elements: list[CMakeElement] = []
        # Create the partial link library containing only the productive sources to be able to find the required mocks
        sources = [CMakePath(source) for source in self.gtest_cmake_component.component_analyzer.collect_sources()]
        # Add the component-specific build directory for the component to find the generated mockup sources
        component_build_dir = self.artifacts_locator.get_component_build_dir(self.gtest_cmake_component.name)
        # Custom command to create the partial link library
        partial_link_obj = component_build_dir.joinpath(f"{self.gtest_cmake_component.partial_link_name}.o")
        custom_command = CMakeCustomCommand(
            description="Create partial link library containing only the productive sources",
            outputs=[partial_link_obj],
            depends=[self.component_object_library_target],
            commands=[
                CMakeCommand(
                    "${CMAKE_CXX_COMPILER}",
                    [
                        "-r",
                        "-nostdlib",
                        "-o",
                        partial_link_obj,
                        f"$<TARGET_OBJECTS:{self.component_object_library_target}>",
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
                generate_mockup_cmake_cmd.outputs,
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
        self.artifacts_locator = GTestCMakeArtifactsLocator(output_dir, execution_context.create_artifacts_locator())
        self.config = config

    def generate(self, component: Component) -> list[CMakeElement]:
        component_generator_config = self._determine_component_generator_config(component)

        component_build_dir = self.artifacts_locator.get_component_build_dir(component.name)
        gtest_cmake_component = GTestCMakeComponent(component, self.execution_context)
        component_analyzer = gtest_cmake_component.component_analyzer

        elements: list[CMakeElement] = []
        elements.append(CMakeComment(f"Component {component.name}"))

        # Create the component executable
        productive_sources = component_analyzer.collect_sources()

        # Always create the component productive sources object library
        component_sources_object_library = CMakeObjectLibrary(
            name=gtest_cmake_component.partial_link_name,
            files=productive_sources,
            compile_options=[
                "-ggdb",  # Include detailed debug information to be able to debug the executable.
                "--coverage",  # Enable coverage tracking information to be generated.
            ],
        )
        elements.append(component_sources_object_library)
        # Add include directories specific to this component plus the component build dir to find generated mockup sources
        include_dirs: list[CMakePath] = [component_build_dir, *gtest_cmake_component.get_include_directories()]
        if include_dirs and not component_generator_config.use_global_includes:
            # Determine visibility: use PRIVATE for libraries with sources, INTERFACE for header-only
            visibility = "INTERFACE" if not productive_sources else "PRIVATE"
            target_includes = CMakeTargetIncludeDirectories(component_sources_object_library.target_name, include_dirs, visibility)
            elements.append(target_includes)

        mockup_generator = None
        if component_generator_config.automock:
            mockup_generator = CMakeMockupCreator(
                gtest_cmake_component,
                component_sources_object_library.target_name,
                self.artifacts_locator,
                component_generator_config.mocking,
            )

        # Components without tests will just be compiled
        if component_analyzer.is_testable():
            all_sources = component_analyzer.collect_test_sources()
            if mockup_generator:
                all_sources += mockup_generator.get_mockup_sources()
            test_executable = self.add_executable(gtest_cmake_component.executable_name, all_sources, component_sources_object_library.target_name)
            elements.append(test_executable)

            # Set the executable output directory to the component-specific directory
            component_build_dir = self.artifacts_locator.get_component_build_dir(component.name)
            target_properties = CMakeSetTargetProperties(test_executable.name, {"RUNTIME_OUTPUT_DIRECTORY": component_build_dir})
            elements.append(target_properties)

            # Add component-specific include directories when global includes are disabled
            if include_dirs and not component_generator_config.use_global_includes:
                # Determine visibility: use PRIVATE for executables with sources, INTERFACE for header-only
                visibility = "INTERFACE" if not all_sources else "PRIVATE"
                target_includes = CMakeTargetIncludeDirectories(test_executable.name, include_dirs, visibility)
                elements.append(target_includes)

            # Create the custom target to execute the tests
            execute_tests_command = self.run_executable(component.name, test_executable.name)
            elements.append(execute_tests_command)

            # Generate coverage report
            coverage_cmd = self.create_coverage_report(component.name, execute_tests_command, productive_sources, component_sources_object_library.target_name)
            elements.append(coverage_cmd)
            component_coverage_target = UserRequest(
                UserRequestScope.COMPONENT,
                component_name=component.name,
                target=UserRequestTarget.COVERAGE,
            )

            elements.append(
                CMakeCustomTarget(
                    name=component_coverage_target.target_name,
                    description=f"Generate coverage report for {component.name}",
                    commands=[],
                    depends=coverage_cmd.outputs,
                )
            )

            # Register the component coverage md report as relevant for the component report
            self.execution_context.data_registry.insert(
                ReportRelevantFiles(
                    target=component_coverage_target,
                    files_to_be_included=[self.artifacts_locator.get_component_build_artifact(component.name, BuildArtifact.COVERAGE_DOC).to_path()],
                    file_type=ReportRelevantFileType.COVERAGE_RESULT,
                ),
                component_coverage_target.target_name,
            )
            # Register the component coverage json report as relevant for the merged coverage report
            self.execution_context.data_registry.insert(
                CoverageRelevantFile(
                    target=component_coverage_target,
                    json_report=self.artifacts_locator.get_component_build_artifact(component.name, BuildArtifact.COVERAGE_JSON),
                ),
                component_coverage_target.target_name,
            )

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
                        execute_tests_command.outputs,
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
                        execute_tests_command.outputs,
                        True,
                    ),
                ]
            )
        else:
            elements.append(CMakeComment(f"Component {component.name} is not testable, only compiling sources."))
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

    def add_executable(self, component_name: str, sources: list[Path], component_object_library: str) -> CMakeAddExecutable:
        return CMakeAddExecutable(
            name=f"{component_name}",
            sources=[CMakePath(source) for source in sources],
            libraries=["GTest::gtest_main", "GTest::gmock_main", "pthread", component_object_library],
            compile_options=[
                "-ggdb",  # Include detailed debug information to be able to debug the executable.
            ],
            link_options=["--coverage"],  # Enable coverage analysis.
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

    def create_coverage_report(
        self,
        component_name: str,
        execute_tests_command: CMakeCustomCommand,
        sources: list[Path],
        component_object_library: str,
    ) -> CMakeCustomCommand:
        artifacts_locator = CoverageArtifactsLocator.from_cmake_artifacts_locator(self.artifacts_locator)
        component_build_dir = artifacts_locator.get_component_build_dir(component_name)
        gcovr_config_file = component_build_dir.joinpath("gcovr.cfg")
        gcovr_json_file = artifacts_locator.get_component_build_artifact(component_name, BuildArtifact.COVERAGE_JSON)
        coverage_doc_file = artifacts_locator.get_component_build_artifact(component_name, BuildArtifact.COVERAGE_DOC)
        gcovr_html_dir = artifacts_locator.get_component_coverage_html_dir(component_name)
        gcovr_html_file = gcovr_html_dir.joinpath("index.html")

        return CMakeCustomCommand(
            description=f"Generate coverage report for component {component_name}",
            outputs=[gcovr_config_file, gcovr_json_file, gcovr_html_file, coverage_doc_file],
            depends=execute_tests_command.outputs,
            commands=[
                CMakeCommand(
                    "yanga_cmd",
                    [
                        "gcovr_config_component",
                        "--component-objects",
                        f"$<TARGET_OBJECTS:{component_object_library}>",
                        "--source-files",
                        *[CMakePath(src) for src in sources],
                        "--output-file",
                        gcovr_config_file,
                    ],
                ),
                CMakeCommand(
                    "yanga_cmd",
                    [
                        "gcovr_doc",
                        "--output-file",
                        coverage_doc_file,
                    ],
                ),
                CMakeCommand(
                    "gcovr",
                    [
                        "--config",
                        gcovr_config_file,
                        "--json",
                        "--output",
                        gcovr_json_file,
                        "--json-pretty",
                    ],
                ),
                CMakeCommand(
                    "${CMAKE_COMMAND}",
                    [
                        "-E",
                        "make_directory",
                        gcovr_html_dir,
                    ],
                ),
                CMakeCommand(
                    "gcovr",
                    [
                        "--config",
                        gcovr_config_file,
                        "--add-tracefile",
                        gcovr_json_file,
                        "--html",
                        "--html-details",
                        "--output",
                        gcovr_html_file,
                    ],
                ),
            ],
        )


class GTestCMakeGenerator(CMakeGenerator):
    """Generates CMake elements to build an executable for a variant."""

    def __init__(self, execution_context: ExecutionContext, output_dir: Path, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__(execution_context, output_dir, config)
        self.artifacts_locator = GTestCMakeArtifactsLocator(output_dir, execution_context.create_artifacts_locator())

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
        elements.extend(self.create_gtest_integration_cmake_elements())
        elements.extend(self.create_components_cmake_elements())
        elements.extend(self.create_variant_cmake_elements())
        return elements

    def create_gtest_integration_cmake_elements(self) -> list[CMakeElement]:
        elements: list[CMakeElement] = []
        elements.append(CMakeVariable("CMAKE_CXX_STANDARD", "14"))
        elements.append(CMakeVariable("CMAKE_CXX_STANDARD_REQUIRED", "ON"))
        elements.append(CMakeVariable("gtest_force_shared_crt", "ON", True, "BOOL", "", True))
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

    def create_variant_cmake_elements(self) -> list[CMakeElement]:
        elements: list[CMakeElement] = []
        # Collect all coverage json reports for the variant coverage report
        coverage_relevant_json_reports = [entry.json_report for entry in self.execution_context.data_registry.find_data(CoverageRelevantFile)]
        gcovr_config_file = self.artifacts_locator.cmake_build_dir.joinpath("gcovr.cfg")
        coverage_doc_file = self.artifacts_locator.get_build_artifact(BuildArtifact.COVERAGE_DOC)
        # We need to generate the html report in a subdirectory to be able to link it relatively from the markdown file
        coverage_doc_file_relative_path = coverage_doc_file.to_path().relative_to(self.artifacts_locator.project_root_dir).parent.as_posix()
        gcovr_html_dir = self.artifacts_locator.cmake_variant_reports_dir.joinpath(coverage_doc_file_relative_path).joinpath("coverage")
        gcovr_html_file = gcovr_html_dir.joinpath("index.html")

        coverage_cmd = CMakeCustomCommand(
            description="Generate coverage report for the variant",
            outputs=[gcovr_config_file, coverage_doc_file, gcovr_html_file],
            depends=coverage_relevant_json_reports,
            commands=[
                CMakeCommand(
                    "yanga_cmd",
                    [
                        "gcovr_config_variant",
                        "--variant-report-config",
                        self.artifacts_locator.get_build_artifact(BuildArtifact.REPORT_CONFIG),
                        "--output-file",
                        gcovr_config_file,
                    ],
                ),
                CMakeCommand(
                    "yanga_cmd",
                    [
                        "gcovr_doc",
                        "--output-file",
                        coverage_doc_file,
                    ],
                ),
                CMakeCommand(
                    "gcovr",
                    [
                        "--config",
                        gcovr_config_file,
                        "--html",
                        "--html-details",
                        "--output",
                        gcovr_html_file,
                    ],
                ),
            ],
        )
        elements.append(coverage_cmd)
        variant_coverage_target = UserRequest(
            UserRequestScope.VARIANT,
            target=UserRequestTarget.COVERAGE,
        )
        elements.append(
            CMakeCustomTarget(
                name=variant_coverage_target.target_name,
                description="Generate variant coverage report",
                commands=[],
                depends=coverage_cmd.outputs,
            )
        )
        # Register the variant coverage md report as relevant for the variant report
        self.execution_context.data_registry.insert(
            ReportRelevantFiles(
                target=variant_coverage_target,
                files_to_be_included=[coverage_doc_file.to_path()],
                file_type=ReportRelevantFileType.COVERAGE_RESULT,
            ),
            variant_coverage_target.target_name,
        )
        return elements
