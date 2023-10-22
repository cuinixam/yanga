from abc import ABC, abstractmethod
from pathlib import Path


class GeneratedFile(ABC):
    def __init__(self, path: Path) -> None:
        self.path: Path = path

    @abstractmethod
    def to_string(self) -> str:
        ...

    def to_file(self) -> None:
        with open(self.path, "w") as f:
            f.write(self.to_string())
