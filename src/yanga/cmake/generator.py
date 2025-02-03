from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from yanga.domain.execution_context import ExecutionContext

from .cmake_backend import CMakeElement


class CMakeGenerator(ABC):
    """Base class for CMake generators."""

    def __init__(self, execution_context: ExecutionContext, output_dir: Path, config: Optional[Dict[str, Any]] = None) -> None:
        self.execution_context = execution_context
        self.config = config
        self.output_dir = output_dir

    @abstractmethod
    def generate(self) -> List[CMakeElement]:
        pass
