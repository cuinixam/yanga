from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from yanga.domain.execution_context import ExecutionContext

from .cmake_backend import CMakeElement


class CMakeGenerator(ABC):
    """Base class for CMake generators."""

    def __init__(self, execution_context: ExecutionContext, output_dir: Path, config: Optional[dict[str, Any]] = None) -> None:
        self.execution_context = execution_context
        self.config = config
        self.output_dir = output_dir

    @abstractmethod
    def generate(self) -> list[CMakeElement]:
        pass


class GeneratedFileIf(ABC):
    def __init__(self, path: Path) -> None:
        self.path = path

    @abstractmethod
    def to_string(self) -> str:
        pass

    def to_file(self) -> None:
        dir = self.path.parent
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            f.write(self.to_string())


class GeneratedFile(GeneratedFileIf):
    def __init__(self, path: Path, content: str) -> None:
        super().__init__(path)
        self.content = content

    def to_string(self) -> str:
        return self.content


class CMakeFile(GeneratedFileIf):
    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self.content: list[CMakeElement] = []

    def to_string(self) -> str:
        return "\n".join(str(elem) for elem in self.content)

    def append(self, content: Optional[CMakeElement]) -> "CMakeFile":
        if content:
            self.content.append(content)
        return self

    def extend(self, content: list[CMakeElement]) -> "CMakeFile":
        for element in content:
            self.append(element)
        return self
