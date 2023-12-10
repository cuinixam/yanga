from enum import Enum, auto
from pathlib import Path
from typing import List

from yanga.ybuild.backends.cmake import CMakeListsBuilder

from ..backends.generated_file import GeneratedFile
from ..environment import BuildEnvironment


class BuildSystemBackend(Enum):
    CMAKE = auto()
    NINJA = auto()


class BuildSystemGenerator:
    def __init__(
        self,
        backend: BuildSystemBackend,
        environment: BuildEnvironment,
        output_dir: Path,
    ):
        self.backend = backend
        self.environment = environment
        self.output_dir = output_dir

    def generate(self) -> List[GeneratedFile]:
        return [self.create_cmake_lists()]

    def create_cmake_lists(self) -> GeneratedFile:
        return (
            CMakeListsBuilder(self.output_dir)
            .with_project_name(self.environment.variant_name)
            .with_components(self.environment.components)
            # TODO: include directories should not be hardcoded here
            .with_include_directories([self.output_dir.joinpath("../gen")])
            .build()
        )
