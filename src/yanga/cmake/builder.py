from pathlib import Path
from typing import Optional

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from py_app_dev.core.pipeline import PipelineLoader

from yanga.cmake.artifacts_locator import CMakeArtifactsLocator
from yanga.domain.execution_context import ExecutionContext
from yanga.domain.reports import ComponentReportConfig, ReportConfig, ReportRelevantFiles

from .cmake_backend import (
    CMakeMinimumVersion,
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
        self.artifacts_locator = CMakeArtifactsLocator(output_dir, execution_context)

    @property
    def variant_cmake_file(self) -> CMakePath:
        return self.cmake_current_list_dir.joinpath("variant.cmake")

    @property
    def config_cmake_file(self) -> CMakePath:
        return self.cmake_current_list_dir.joinpath("config.cmake")

    @property
    def report_config_file(self) -> CMakePath:
        return self.artifacts_locator.variant_report_config

    @property
    def variant_name(self) -> str:
        return self.execution_context.variant_name or "MyProject"

    def generate(self) -> list[GeneratedFileIf]:
        files: list[GeneratedFileIf] = []
        files.append(self.create_config_cmake_file())
        files.append(self.create_variant_cmake_file())
        files.append(self.create_report_config_file())
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
        for entry in relevant_files_entries:
            # Only collect data relevant for components
            if entry.target.component_name:
                if components_data.get(entry.target.component_name):
                    components_data[entry.target.component_name].append(entry)
                else:
                    components_data[entry.target.component_name] = [entry]

        config = ReportConfig(
            variant=self.execution_context.variant_name or "",
            platform=self.execution_context.platform.name if self.execution_context.platform else "",
            project_dir=self.execution_context.project_root_dir,
            components=[ComponentReportConfig(name=component_name, files=files) for component_name, files in components_data.items()],
        )
        return GeneratedFile(self.report_config_file.to_path(), config.to_json_string())
