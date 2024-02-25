from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from .cmake_backend import CMakeElement

from yanga.domain.execution_context import ExecutionContext


class CMakeGenerator(ABC):
    """Base class for CMake generators."""

    def __init__(self, execution_context: ExecutionContext, output_dir: Path) -> None:
        self.execution_context = execution_context
        self.output_dir = output_dir

    @abstractmethod
    def generate(self) -> List[CMakeElement]:
        pass
