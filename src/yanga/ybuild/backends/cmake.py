import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, List, Optional, Union

from py_app_dev.core.logging import logger, time_it
from py_app_dev.core.subprocess import SubprocessExecutor

from yanga.ybuild.components import BuildComponent

from .builder import Builder
from .generated_file import GeneratedFile


def make_list_unique(seq: List[Any]) -> List[Any]:
    return list(dict.fromkeys(seq))


class LibraryType(Enum):
    OBJECT = auto()


class CMakeElement(ABC):
    tab_prefix = " " * 4

    @abstractmethod
    def to_string(self) -> str:
        pass

    def __str__(self) -> str:
        return self.to_string()


class CMakeContent(CMakeElement):
    def __init__(self, content: str) -> None:
        super().__init__()
        self.content = content

    def to_string(self) -> str:
        return self.content


class CMakeEmptyLine(CMakeElement):
    def to_string(self) -> str:
        return ""


class CMakeComment(CMakeElement):
    def __init__(self, comment: str) -> None:
        super().__init__()
        self.comment = comment

    def to_string(self) -> str:
        return f"# {self.comment}"


class CMakeProject(CMakeElement):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    def to_string(self) -> str:
        return f"project({self.name})"


class CMakeMinimumVersion(CMakeElement):
    def __init__(self, version: str) -> None:
        super().__init__()
        self.version = version

    def to_string(self) -> str:
        return f"cmake_minimum_required(VERSION {self.version})"


@dataclass
class CMakeLibrary(CMakeElement):
    name: str
    files: List[Path] = field(default_factory=list)
    type: LibraryType = LibraryType.OBJECT

    @property
    def target_name(self) -> str:
        return f"{self.name}_lib"

    def to_string(self) -> str:
        return f"add_library({self.target_name} {self.type.name} {self._get_files_string()})"

    def _get_files_string(self) -> str:
        return " ".join([file.as_posix() for file in self.files])


class CMakeObjectLibrary(CMakeLibrary):
    def __init__(self, name: str, files: List[Path] = field(default_factory=list)) -> None:
        super().__init__(name, files, LibraryType.OBJECT)


@dataclass
class CMakeVariable(CMakeElement):
    """
    set(<variable> <value>... CACHE <type> <docstring> [FORCE])
    https://cmake.org/cmake/help/latest/command/set.html
    """

    name: str
    value: str
    cache: bool = False
    type: Optional[str] = None
    docstring: Optional[str] = None
    force: bool = False

    def to_string(self) -> str:
        arguments = [self.name, self.value]
        if self.cache:
            arguments.append("CACHE")
        if self.type:
            arguments.append(self.type)
        if self.docstring is not None:
            if self.docstring:
                arguments.append(self.docstring)
            else:
                arguments.append('""')
        if self.force:
            arguments.append("FORCE")
        return "set(" + " ".join(arguments) + ")"


class CMakePath:
    def __init__(
        self,
        path: Path,
        variable: Optional[str] = None,
        relative_path: Optional[Path] = None,
    ) -> None:
        super().__init__()
        self.path = path
        self.variable = variable
        self.relative_path = relative_path

    def to_cmake_element(self) -> Optional[CMakeElement]:
        return CMakeVariable(self.variable, self.to_string()) if self.variable else None

    def to_string(self) -> str:
        if self.variable:
            path = f"${{{self.variable}}}"
        else:
            path = self.path.as_posix()
        if self.relative_path:
            path += f"/{self.relative_path.as_posix()}"
        return path

    def to_path(self) -> Path:
        return self.path / self.relative_path if self.relative_path else self.path

    def joinpath(self, path: str) -> "CMakePath":
        return CMakePath(self.path, self.variable, Path(path))

    def __str__(self) -> str:
        return self.to_string()


class CMakeInclude(CMakeElement):
    def __init__(self, path: str | CMakePath) -> None:
        super().__init__()
        self.path = path

    def to_string(self) -> str:
        return f"include({self.path})"


class CMakeIncludeDirectories(CMakeElement):
    def __init__(self, paths: List[CMakePath]) -> None:
        super().__init__()
        self.paths = paths

    def to_string(self) -> str:
        return "\n".join(["include_directories("] + self._add_tabulated_paths(self.paths) + [")"])

    def _add_tabulated_paths(self, paths: List[CMakePath]) -> List[str]:
        return [self._add_tabulated_path(path) for path in paths]

    def _add_tabulated_path(self, path: CMakePath) -> str:
        return self.tab_prefix + path.to_string()


@dataclass
class CMakeAddExecutable(CMakeElement):
    """
    add_executable(<name> [WIN32] [MACOSX_BUNDLE]
                     [EXCLUDE_FROM_ALL]
                        [source1] [source2 ...])
    https://cmake.org/cmake/help/latest/command/add_executable.html#add-executable
    """

    name: str
    sources: List[Union[str, CMakePath, CMakeObjectLibrary]]
    libraries: List[str] = field(default_factory=list)
    compile_options: List[str] = field(default_factory=list)
    link_options: List[str] = field(default_factory=list)
    exclude_from_all: bool = False

    def to_string(self) -> str:
        content = self._add_executable()
        if self.libraries:
            # add target_link_libraries
            content += "\n" + self._add_target_link_libraries()
        if self.compile_options:
            content += "\n" + self._add_compile_options()
        if self.link_options:
            content += "\n" + self._add_link_options()
        return content

    def _add_executable(self) -> str:
        arguments = [self.name]
        if self.exclude_from_all:
            arguments.append("EXCLUDE_FROM_ALL")
        arguments.extend(self._get_sources())
        return "add_executable(" + " ".join(arguments) + ")"

    def _add_target_link_libraries(self) -> str:
        return "target_link_libraries(" + " ".join([self.name] + self.libraries) + ")"

    def _get_sources(self) -> List[str]:
        return [self._get_source(source) for source in self.sources]

    def _get_source(self, source: str | CMakePath | CMakeObjectLibrary) -> str:
        """
        - str: return as is
        - CMakePath: return the path as string
        - CMakeLibrary: return the target objects
        """
        if isinstance(source, CMakeObjectLibrary):
            return f"$<TARGET_OBJECTS:{source.target_name}>"
        else:
            return str(source)

    def _add_compile_options(self) -> str:
        return f"target_compile_options({self.name} PRIVATE " + " ".join(self.compile_options) + ")"

    def _add_link_options(self) -> str:
        return f"target_link_options({self.name} PRIVATE " + " ".join(self.link_options) + ")"


class CMakeCommand(CMakeElement):
    def __init__(self, command: str | CMakePath, arguments: List[str | CMakePath]) -> None:
        super().__init__()
        self.command = command
        self.arguments = arguments

    def to_string(self) -> str:
        return f"COMMAND {self.command} {' '.join(str(arg) for arg in self.arguments)}"


class CMakeExecuteProcess(CMakeElement):
    def __init__(self, description: str, commands: List[CMakeCommand]) -> None:
        super().__init__()
        self.description = description
        self.commands = commands

    def to_string(self) -> str:
        content = [CMakeComment(self.description), "execute_process("]
        content.extend(self._get_commands())
        content.extend(
            [
                f"{self.tab_prefix}RESULT_VARIABLE result",
                ")",
                "if(result)",
                f"{self.tab_prefix}message(FATAL_ERROR '{self.description} failed: ${{result}}')",
                "endif()",
            ]
        )
        return "\n".join(str(line) for line in content)

    def _get_commands(self) -> List[str]:
        return [self.tab_prefix + str(command) for command in self.commands]


class CMakeDepends(CMakeElement):
    def __init__(self, depends: List[str | CMakePath]) -> None:
        super().__init__()
        self.depends = depends

    def to_string(self) -> str:
        return f"{self.tab_prefix}DEPENDS {' '.join(str(depend) for depend in self.depends)}"


@dataclass
class CMakeCustomCommand(CMakeElement):
    description: str
    outputs: List[CMakePath]
    depends: List[str | CMakePath]
    commands: List[CMakeCommand]

    def to_string(self) -> str:
        content = [CMakeComment(self.description), "add_custom_command("]
        content.extend(self._get_outputs())
        content.append(CMakeDepends(self.depends).to_string())
        content.extend(self._get_commands())
        content.append(")")
        return "\n".join(str(line) for line in content)

    def _get_outputs(self) -> List[str]:
        return [f"{self.tab_prefix}OUTPUT {output.to_string()}" for output in self.outputs]

    def _get_commands(self) -> List[str]:
        return [self.tab_prefix + str(command) for command in self.commands]


@dataclass
class CMakeCustomTarget(CMakeElement):
    def __init__(
        self,
        name: str,
        description: str,
        commands: List[CMakeCommand],
        depends: Optional[List[str | CMakePath]] = None,
        default_target: bool = False,
    ) -> None:
        super().__init__()
        self.name = name
        self.description = description
        self.depends = depends
        self.commands = commands
        self.default_target = default_target

    def to_string(self) -> str:
        add_to_all_target = "ALL" if self.default_target else ""
        content = [
            CMakeComment(self.description),
            f"add_custom_target({self.name} {add_to_all_target}",
        ]
        content.extend(self._get_commands())
        if self.depends:
            content.append(CMakeDepends(self.depends).to_string())
        content.append(")")
        return "\n".join(str(line) for line in content)

    def _get_commands(self) -> List[str]:
        return [self.tab_prefix + str(command) for command in self.commands]


class CMakeAddSubdirectory(CMakeElement):
    """
    add_subdirectory(source_dir [binary_dir] [EXCLUDE_FROM_ALL] [SYSTEM])
    https://cmake.org/cmake/help/latest/command/add_subdirectory.html#add-subdirectory
    """

    def __init__(self, source_dir: CMakePath, build_dir: Optional[CMakePath] = None) -> None:
        super().__init__()
        self.source_dir = source_dir
        self.build_dir = build_dir

    def to_string(self) -> str:
        arguments = [self.source_dir.to_string()]
        if self.build_dir:
            arguments.append(self.build_dir.to_string())
        return "add_subdirectory(" + " ".join(arguments) + ")"


class CMakeListAppend(CMakeElement):
    def __init__(self, variable: str, values: List[str]) -> None:
        super().__init__()
        self.variable = variable
        self.values = values

    def to_string(self) -> str:
        return f"list(APPEND {self.variable} {self._get_values_string()})"

    def _get_values_string(self) -> str:
        return " ".join(self.values)


class CMakeFile(GeneratedFile):
    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self.content: List[CMakeElement] = []

    def to_string(self) -> str:
        return "\n".join(str(elem) for elem in self.content)

    def append(self, content: Optional[CMakeElement]) -> "CMakeFile":
        if content:
            self.content.append(content)
        return self


class CMakeEnableTesting(CMakeElement):
    def __init__(self) -> None:
        super().__init__()

    def to_string(self) -> str:
        return "enable_testing()"


class CMakeLists(GeneratedFile):
    tab_prefix = " " * 4

    def __init__(self, path: Path) -> None:
        super().__init__(path)
        self.project_name = ""
        self.cmake_version = ""
        self.source_files: List[Path] = []
        self.include_directories: List[Path] = []
        self.libraries: List[CMakeLibrary] = []

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
        content.extend(self._generate_libraries())
        content.append("")
        content.extend(self._generate_include_directories())
        libraries_deps = ""
        if self.libraries:
            libraries_deps = " ".join([f"$<TARGET_OBJECTS:{library.target_name}>" for library in self.libraries])

        content.append("")
        content.append(f"add_executable(${{PROJECT_NAME}} ${{SOURCE_FILES}} {libraries_deps})")
        return "\n".join(content) + "\n"

    def _generate_source_files(self) -> List[str]:
        return ["set(SOURCE_FILES "] + self._add_tabulated_paths(self.source_files) + [")"]

    def _generate_libraries(self) -> List[str]:
        return [library.to_string() for library in self.libraries]

    def _generate_include_directories(self) -> List[str]:
        return ["include_directories("] + self._add_tabulated_paths(self.include_directories) + [")"]

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
            files.extend([component.path.joinpath(source) for source in component.sources])
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
        for component in self.components:
            self.cmake_lists.libraries.append(
                CMakeLibrary(component.name, BuildFileCollector([component]).collect_sources())
            )
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
        env["PATH"] = ";".join([path.absolute().as_posix() for path in self.install_directories] + [env["PATH"]])
        command = self.executable + " " + arguments
        SubprocessExecutor([command], env=env).execute()
