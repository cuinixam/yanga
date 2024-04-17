import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, List, Optional, Union

from py_app_dev.core.logging import logger, time_it
from py_app_dev.core.subprocess import SubprocessExecutor


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


class CMakeLibrary(CMakeElement):
    def __init__(
        self,
        name: str,
        files: List[Path] | None = None,
        type: LibraryType = LibraryType.OBJECT,
    ) -> None:
        self.name = name
        self.files = files if files else []
        self.type = type

    @property
    def target_name(self) -> str:
        return f"{self.name}_lib"

    def to_string(self) -> str:
        return f"add_library({self.target_name} {self.type.name} {self._get_files_string()})"

    def _get_files_string(self) -> str:
        return " ".join([file.as_posix() for file in self.files])


class CMakeObjectLibrary(CMakeLibrary):
    def __init__(self, name: str, files: List[Path] | None = None) -> None:
        super().__init__(name, files, LibraryType.OBJECT)


@dataclass
class CMakeVariable(CMakeElement):
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
        return CMakeVariable(self.variable, self.to_path().as_posix()) if self.variable else None

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
        return "\n".join(["include_directories(", *self._add_tabulated_paths(self.paths), ")"])

    def _add_tabulated_paths(self, paths: List[CMakePath]) -> List[str]:
        return [self._add_tabulated_path(path) for path in paths]

    def _add_tabulated_path(self, path: CMakePath) -> str:
        return self.tab_prefix + path.to_string()


@dataclass
class CMakeAddExecutable(CMakeElement):
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
        return "target_link_libraries(" + " ".join([self.name, *self.libraries]) + ")"

    def _get_sources(self) -> List[str]:
        return [self._get_source(source) for source in self.sources]

    def _get_source(self, source: str | CMakePath | CMakeObjectLibrary) -> str:
        """
        Get the source as string.

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
        return [f"{self.tab_prefix}OUTPUT {' '.join([output.to_string() for output in self.outputs])}"]

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


class CMakeFile:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.content: List[CMakeElement] = []

    def to_string(self) -> str:
        return "\n".join(str(elem) for elem in self.content)

    def to_file(self) -> None:
        dir = self.path.parent
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            f.write(self.to_string())

    def append(self, content: Optional[CMakeElement]) -> "CMakeFile":
        if content:
            self.content.append(content)
        return self

    def extend(self, content: List[CMakeElement]) -> "CMakeFile":
        for element in content:
            self.append(element)
        return self


class CMakeEnableTesting(CMakeElement):
    def __init__(self) -> None:
        super().__init__()

    def to_string(self) -> str:
        return "enable_testing()"


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
