import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List

from py_app_dev.core.logging import logger, time_it
from py_app_dev.core.subprocess import SubprocessExecutor

from yanga.ybuild.components import BuildComponent

from .builder import Builder
from .generated_file import GeneratedFile


def make_list_unique(seq: List[Any]) -> List[Any]:
    return list(dict.fromkeys(seq))


@dataclass
class CMakeLibrary:
    name: str
    files: List[str] = field(default_factory=list)
    public_include_dirs: List[str] = field(default_factory=list)


class CMakeLists(GeneratedFile):
    tab_prefix = " " * 4

    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self.project_name = ""
        self.cmake_version = ""
        self.source_files: List[Path] = []
        self.include_directories: List[Path] = []
        # TODO: self.libraries: List[CMakeLibrary] = []

    def to_string(self) -> str:
        content = [
            f"cmake_minimum_required(VERSION {self.cmake_version})",
            f"project({self.project_name})",
            "",
            "set(CMAKE_CXX_STANDARD 99)",
            "",
            "set(CMAKE_C_COMPILER clang)",
            "set(CMAKE_CXX_COMPILER clang++)",
            "",
        ]
        content.extend(self._generate_source_files())
        content.append("")
        content.extend(self._generate_include_directories())
        content.append("")
        content.append("add_executable(${PROJECT_NAME} ${SOURCE_FILES})")
        return "\n".join(content) + "\n"

    def _generate_source_files(self) -> List[str]:
        return (
            ["set(SOURCE_FILES "] + self._add_tabulated_paths(self.source_files) + [")"]
        )

    def _generate_include_directories(self) -> List[str]:
        return (
            ["include_directories("]
            + self._add_tabulated_paths(self.include_directories)
            + [")"]
        )

    def _add_tabulated_paths(self, paths: List[Path]) -> List[str]:
        return [self._add_tabulated_path(path) for path in paths]

    def _add_tabulated_path(self, path: Path) -> str:
        return self.tab_prefix + path.absolute().as_posix()


class BuildFileCollector:
    def __init__(self, components: List[BuildComponent]) -> None:
        self.components = components

    def collect_sources(self) -> List[Path]:
        files: List[Path] = []
        for component in self.components:
            files.extend(
                [component.path.joinpath(source) for source in component.sources]
            )
        return files

    def collect_include_directories(self) -> List[Path]:
        # TODO: check if there are specific include directories for each component
        includes = [path.parent for path in self.collect_sources()]
        # remove duplicates and return
        return make_list_unique(includes)


class CMakeListsBuilder(Builder):
    file_name = "CMakeLists.txt"

    def __init__(self, output_path: Path, cmake_version: str = "3.20") -> None:
        self.output_path = output_path
        self.components: List[BuildComponent] = []
        self.cmake_lists = CMakeLists(self.output_path.joinpath(self.file_name))
        self.cmake_lists.cmake_version = cmake_version
        self.include_directories: List[Path] = []

    def with_project_name(self, name: str) -> Builder:
        self.cmake_lists.project_name = name
        return self

    def with_components(self, components: List[BuildComponent]) -> Builder:
        self.components = components
        return self

    def with_include_directories(self, include_directories: List[Path]) -> Builder:
        self.include_directories.extend(include_directories)
        return self

    def build(self) -> GeneratedFile:
        collector = BuildFileCollector(self.components)
        self.cmake_lists.source_files = collector.collect_sources()
        self.cmake_lists.include_directories = make_list_unique(
            self.include_directories + collector.collect_include_directories()
        )
        return self.cmake_lists


class CMakeRunner:
    executable = "cmake"

    def __init__(self, install_directories: List[Path]) -> None:
        self.logger = logger.bind()
        self.install_directories = install_directories

    def run(self, build_dir: Path, target: str = "all") -> None:
        self.configure(build_dir)
        self.build(build_dir, target)

    @time_it("CMake configure")
    def configure(self, build_dir: Path) -> None:
        build_dir_str = build_dir.absolute().as_posix()
        arguments = f" -S{build_dir_str}" f" -B{build_dir_str}" f" -G Ninja "
        self.run_cmake(arguments)

    @time_it("CMake build")
    def build(self, build_dir: Path, target: str = "all") -> None:
        build_dir_str = build_dir.absolute().as_posix()
        arguments = f" --build {build_dir_str}" f" --target {target} -- "
        self.run_cmake(arguments)

    def run_cmake(self, arguments: str) -> None:
        # Add the install directories to the PATH
        env = os.environ.copy()
        env["PATH"] = ";".join(
            [path.absolute().as_posix() for path in self.install_directories]
            + [env["PATH"]]
        )
        command = self.executable + " " + arguments
        SubprocessExecutor([command], env=env).execute()
