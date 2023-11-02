from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from yanga.ybuild.components import BuildComponent

from .generated_file import GeneratedFile


class Builder(ABC):
    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path

    @abstractmethod
    def with_project_name(self, name: str) -> "Builder":
        ...

    @abstractmethod
    def with_components(self, components: List[BuildComponent]) -> "Builder":
        ...

    @abstractmethod
    def with_include_directories(self, include_directories: List[Path]) -> "Builder":
        ...

    @abstractmethod
    def build(self) -> GeneratedFile:
        ...
