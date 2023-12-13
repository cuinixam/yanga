from abc import ABC, abstractmethod
from pathlib import Path


class GeneratedFile(ABC):
    def __init__(self, path: Path) -> None:
        self.path: Path = path

    @abstractmethod
    def to_string(self) -> str:
        ...

    def to_file(self) -> None:
        dir = self.path.parent
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            f.write(self.to_string())
