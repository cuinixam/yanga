from pathlib import Path
from typing import Any, Optional

from yanga.cmake.cmake_backend import CMakeElement
from yanga.cmake.generator import CMakeGenerator
from yanga.domain.execution_context import ExecutionContext


class CppCheckCMakeGenerator(CMakeGenerator):
    def __init__(
        self,
        execution_context: ExecutionContext,
        output_dir: Path,
        config: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(execution_context, output_dir, config)

    def generate(self) -> list[CMakeElement]:
        return []
