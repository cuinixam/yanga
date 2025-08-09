from pathlib import Path
from typing import Any, Optional

from py_app_dev.core.logging import logger
from pypeline.domain.pipeline import PipelineStep

from yanga.cmake.builder import CMakeBuildSystemGenerator
from yanga.cmake.cmake_backend import CMakePath
from yanga.cmake.runner import CMakeRunner
from yanga.domain.execution_context import ExecutionContext


class GenerateBuildSystemFiles(PipelineStep[ExecutionContext]):
    def __init__(self, execution_context: ExecutionContext, group_name: Optional[str] = None, config: Optional[dict[str, Any]] = None) -> None:
        super().__init__(execution_context, group_name, config)
        self.logger = logger.bind()
        self.generated_files: list[Path] = []

    @property
    def output_dir(self) -> Path:
        return self.execution_context.create_artifacts_locator().variant_build_dir

    def get_name(self) -> str:
        return self.__class__.__name__

    def run(self) -> int:
        self.logger.info(f"Run {self.__class__.__name__} stage. Output dir: {self.output_dir}")
        generated_files = CMakeBuildSystemGenerator(self.execution_context, self.output_dir).generate()
        for file in generated_files:
            file.to_file()
        self.generated_files = [file.path for file in generated_files]
        return 0

    def get_inputs(self) -> list[Path]:
        return self.execution_context.user_config_files

    def get_outputs(self) -> list[Path]:
        return self.generated_files

    def update_execution_context(self) -> None:
        pass


class ExecuteBuild(PipelineStep[ExecutionContext]):
    """The step is always executed. The dependencies are handled by the build system itself."""

    def __init__(self, execution_context: ExecutionContext, group_name: Optional[str], config: Optional[dict[str, Any]] = None) -> None:
        super().__init__(execution_context, group_name, config)
        self.logger = logger.bind()

    @property
    def output_dir(self) -> Path:
        return self.execution_context.create_artifacts_locator().variant_build_dir

    def get_name(self) -> str:
        return self.__class__.__name__

    def run(self) -> int:
        self.logger.debug(f"Run {self.get_name()} stage. Output dir: {self.output_dir}")
        cmake_runner = CMakeRunner(self.execution_context.project_root_dir, self.output_dir)
        toolchain_file = None
        platform_name = self.execution_context.platform.name if self.execution_context.platform else None
        if self.execution_context.platform and self.execution_context.platform.toolchain_file:
            toolchain_file = CMakePath(
                self.execution_context.create_artifacts_locator().locate_artifact(self.execution_context.platform.toolchain_file, [self.execution_context.platform.file])
            ).to_string()
        self._run(cmake_runner.get_configure_command(toolchain_file, self.execution_context.variant_name, platform_name, self.execution_context.user_request.build_type))
        self._run(cmake_runner.get_build_command(self.execution_context.user_request.target_name))
        return 0

    def _run(self, cmd: list[str | Path]) -> None:
        self.execution_context.create_process_executor(cmd).execute()

    def get_inputs(self) -> list[Path]:
        return []

    def get_outputs(self) -> list[Path]:
        return []

    def update_execution_context(self) -> None:
        pass
