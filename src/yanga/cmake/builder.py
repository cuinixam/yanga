from pathlib import Path
from typing import List, Optional, Type

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from py_app_dev.core.pipeline import PipelineLoader

from yanga.domain.execution_context import ExecutionContext

from .cmake_backend import (
    CMakeFile,
    CMakeInclude,
    CMakeMinimumVersion,
    CMakePath,
    CMakeProject,
    CMakeVariable,
)
from .generator import CMakeGenerator


class CMakeGeneratorReference:
    def __init__(self, group_name: Optional[str], _class: Type[CMakeGenerator]) -> None:
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

    @property
    def variant_cmake_file(self) -> CMakePath:
        return self.cmake_current_list_dir.joinpath("variant.cmake")

    def generate(self) -> List[CMakeFile]:
        files = []
        cmake_lists_file = self.create_cmake_lists()
        files.append(cmake_lists_file)
        files.append(self.create_variant_cmake_file())
        cmake_lists_file.append(CMakeInclude(self.variant_cmake_file))
        return files

    def create_cmake_lists(self) -> CMakeFile:
        cmake_file = CMakeFile(self.output_dir.joinpath("CMakeLists.txt"))
        cmake_file.append(CMakeMinimumVersion("3.20"))
        platform = self.execution_context.platform
        if platform and platform.toolchain_file:
            cmake_file.append(
                CMakeVariable(
                    "CMAKE_TOOLCHAIN_FILE",
                    CMakePath(self.execution_context.create_artifacts_locator().locate_artifact(platform.toolchain_file, [platform.file])).to_string(),
                )
            )
        cmake_file.append(CMakeProject(self.execution_context.variant_name or "MyProject"))
        return cmake_file

    def create_variant_cmake_file(self) -> CMakeFile:
        cmake_file = CMakeFile(self.variant_cmake_file.to_path())
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
