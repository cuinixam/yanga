from pathlib import Path
from typing import Optional

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.find import find_elements_of_type
from py_app_dev.core.logging import logger
from py_app_dev.core.pipeline import PipelineLoader

from yanga.cmake.artifacts_locator import BuildArtifact, CMakeArtifactsLocator
from yanga.domain.execution_context import ExecutionContext
from yanga.domain.reports import ComponentReportData, FeaturesReportRelevantFile, ReportData, ReportRelevantFiles, VariantReportData
from yanga.domain.targets import Target, TargetsData, TargetType

from .cmake_backend import (
    CMakeAddExecutable,
    CMakeCustomCommand,
    CMakeCustomTarget,
    CMakeMinimumVersion,
    CMakeObjectLibrary,
    CMakePath,
    CMakeProject,
    CMakeVariable,
)
from .generator import CMakeFile, CMakeGenerator, GeneratedFile, GeneratedFileIf


class CMakeGeneratorReference:
    def __init__(self, group_name: Optional[str], _class: type[CMakeGenerator]) -> None:
        self.group_name = group_name
        self._class = _class

    @property
    def name(self) -> str:
        return self._class.__name__


class CMakeBuildSystemGenerator:
    def __init__(
        self,
        execution_context: ExecutionContext,
        output_dir: Path,
    ):
        self.logger = logger.bind()
        self.execution_context = execution_context
        self.output_dir = output_dir
        # The directory where the CMakeLists.txt file is located
        self.cmake_current_list_dir = CMakePath(self.output_dir, "CMAKE_CURRENT_LIST_DIR")
        self.artifacts_locator = CMakeArtifactsLocator(output_dir, execution_context.create_artifacts_locator())

    @property
    def variant_cmake_file(self) -> CMakePath:
        return self.cmake_current_list_dir.joinpath("variant.cmake")

    @property
    def config_cmake_file(self) -> CMakePath:
        return self.cmake_current_list_dir.joinpath("config.cmake")

    @property
    def report_config_file(self) -> CMakePath:
        return self.artifacts_locator.get_build_artifact(BuildArtifact.REPORT_CONFIG)

    @property
    def variant_name(self) -> str:
        return self.execution_context.variant_name or "MyProject"

    def generate(self) -> list[GeneratedFileIf]:
        files: list[GeneratedFileIf] = []
        cmake_files: list[CMakeFile] = []
        cmake_files.append(self.create_config_cmake_file())
        cmake_files.append(self.create_variant_cmake_file())
        files.extend(cmake_files)
        files.append(self.create_report_config_file())
        files.append(self.create_target_dependencies_file(cmake_files))
        return files

    def create_cmake_lists(self) -> CMakeFile:
        cmake_file = CMakeFile(self.output_dir.joinpath("CMakeLists.txt"))
        cmake_file.append(CMakeMinimumVersion("4.1"))
        platform = self.execution_context.platform
        if platform and platform.toolchain_file:
            cmake_file.append(
                CMakeVariable(
                    "CMAKE_TOOLCHAIN_FILE",
                    CMakePath(self.execution_context.create_artifacts_locator().locate_artifact(platform.toolchain_file, [platform.file])).to_string(),
                )
            )
        cmake_file.append(CMakeProject(self.variant_name))
        return cmake_file

    def create_variant_cmake_file(self) -> CMakeFile:
        cmake_file = CMakeFile(self.variant_cmake_file.to_path())
        cmake_build_dir_var = self.artifacts_locator.cmake_build_dir.to_cmake_element()
        if cmake_build_dir_var:
            cmake_file.append(cmake_build_dir_var)
        # Load all configured CMake generators
        platform = self.execution_context.platform
        if platform:
            try:
                steps_references = PipelineLoader[CMakeGenerator](platform.cmake_generators, self.execution_context.project_root_dir).load_steps()
                for step_reference in steps_references:
                    step = step_reference._class(self.execution_context, self.output_dir, step_reference.config)
                    cmake_file.extend(step.generate())
            except FileNotFoundError as e:
                raise UserNotificationException(e) from e
            except TypeError as e:
                raise UserNotificationException(f"{e}. Please check {platform.file} for {step}.") from e
        return cmake_file

    def create_config_cmake_file(self) -> CMakeFile:
        from .variant_config import ConfigCMakeGenerator

        cmake_file = CMakeFile(self.config_cmake_file.to_path())
        config_generator = ConfigCMakeGenerator(self.execution_context, self.output_dir)
        cmake_file.extend(config_generator.generate())
        # configure cmake to generate compile commands
        cmake_file.append(CMakeVariable("CMAKE_EXPORT_COMPILE_COMMANDS", "ON", True, "BOOL", "", True))
        return cmake_file

    def create_report_config_file(self) -> GeneratedFileIf:
        # Collect all ReportRelevantFiles from the data registry
        relevant_files_entries = self.execution_context.data_registry.find_data(ReportRelevantFiles)

        # Group report relevant files by component name. Use a default list
        components_data: dict[str, list[ReportRelevantFiles]] = {}
        variant_data: list[ReportRelevantFiles] = []
        for entry in relevant_files_entries:
            # Only collect data relevant for components
            if entry.target.component_name:
                if components_data.get(entry.target.component_name):
                    components_data[entry.target.component_name].append(entry)
                else:
                    components_data[entry.target.component_name] = [entry]
            else:
                variant_data.append(entry)
        config = ReportData(
            variant_name=self.execution_context.variant_name or "",
            platform_name=self.execution_context.platform.name if self.execution_context.platform else "",
            project_dir=self.execution_context.project_root_dir,
            components=[
                ComponentReportData(
                    name=component_name,
                    files=files,
                    build_dir=self.artifacts_locator.get_component_build_dir(component_name).to_path(),
                )
                for component_name, files in components_data.items()
            ],
        )
        if variant_data:
            config.variant_data = VariantReportData(
                files=variant_data,
                build_dir=self.artifacts_locator.cmake_build_dir.to_path(),
            )
        features_config_file = self.execution_context.data_registry.find_data(FeaturesReportRelevantFile)
        if features_config_file:
            # TODO: Handle multiple feature config files?
            config.features_json_config = features_config_file[0].json_config_file
        return GeneratedFile(self.report_config_file.to_path(), config.to_json_string())

    def create_target_dependencies_file(self, cmake_files: list[CMakeFile]) -> GeneratedFileIf:
        """
        Create a json file that contains the CMake target dependencies tree for the current variant and each component.

        Parse all cmake files, search for the custom targets and their dependencies, and create a json file.
        This file is required to create a graph of the targets and their dependencies.
        """
        targets: list[Target] = []

        # Extract all elements from cmake files
        all_elements = []
        for cmake_file in cmake_files:
            all_elements.extend(cmake_file.content)

        # Find all custom commands
        custom_commands = find_elements_of_type(all_elements, CMakeCustomCommand)
        for custom_command in custom_commands:
            dependencies = []
            outputs = []

            # Extract dependencies
            if custom_command.depends:
                dependencies.extend([str(dep) for dep in custom_command.depends])

            # Extract outputs
            if custom_command.outputs:
                outputs.extend([str(output) for output in custom_command.outputs])

            targets.append(
                Target(
                    name=f"cmd_{custom_command.description.replace(' ', '_').lower()}",
                    description=custom_command.description,
                    depends=dependencies,
                    outputs=outputs,
                    target_type=TargetType.CUSTOM_COMMAND,
                )
            )

        # Find all custom targets
        custom_targets = find_elements_of_type(all_elements, CMakeCustomTarget)
        for custom_target in custom_targets:
            dependencies = []
            outputs = []

            # Extract dependencies
            if custom_target.depends:
                dependencies.extend([str(dep) for dep in custom_target.depends])

            # Extract outputs/byproducts
            if custom_target.byproducts:
                outputs.extend([str(byproduct) for byproduct in custom_target.byproducts])

            targets.append(Target(name=custom_target.name, description=custom_target.description, depends=dependencies, outputs=outputs, target_type=TargetType.CUSTOM_TARGET))

        # Find all executables
        executables = find_elements_of_type(all_elements, CMakeAddExecutable)
        for executable in executables:
            dependencies = []

            # Add library dependencies
            if executable.libraries:
                dependencies.extend(executable.libraries)

            targets.append(
                Target(
                    name=executable.name,
                    description=f"Executable target: {executable.name}",
                    depends=dependencies,
                    outputs=[executable.name],  # The executable itself is the output
                    target_type=TargetType.EXECUTABLE,
                )
            )

        # Find all object libraries
        object_libraries = find_elements_of_type(all_elements, CMakeObjectLibrary)
        for obj_lib in object_libraries:
            targets.append(
                Target(
                    name=obj_lib.target_name,
                    description=f"Object library: {obj_lib.name}",
                    depends=[],  # Object libraries typically don't have explicit dependencies in our structure
                    outputs=[obj_lib.target_name],
                    target_type=TargetType.OBJECT_LIBRARY,
                )
            )

        targets_data = TargetsData(targets=targets)
        return GeneratedFile(
            self.cmake_current_list_dir.joinpath("targets_data.json").to_path(),
            targets_data.to_json_string(),
        )
