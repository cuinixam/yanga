from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional, Union


def make_list_unique(seq: list[Any]) -> list[Any]:
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
        files: list[Path] | None = None,
        type: LibraryType = LibraryType.OBJECT,
        compile_options: list[str] | None = None,
    ) -> None:
        self.name = name
        self.files = files if files else []
        self.type = type
        self.compile_options = compile_options if compile_options else []

    @property
    def target_name(self) -> str:
        return f"{self.name}_lib"

    def to_string(self) -> str:
        content = f"add_library({self.target_name} {self.type.name} {self._get_files_string()})"
        if self.compile_options:
            content += "\n" + self._add_compile_options()
        return content

    def _get_files_string(self) -> str:
        return " ".join([file.as_posix() for file in self.files])

    def _add_compile_options(self) -> str:
        return f"target_compile_options({self.target_name} PRIVATE " + " ".join(self.compile_options) + ")"


class CMakeObjectLibrary(CMakeLibrary):
    def __init__(self, name: str, files: list[Path] | None = None, compile_options: list[str] | None = None) -> None:
        super().__init__(name, files, LibraryType.OBJECT, compile_options)


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
        rel_path = self.relative_path / path if self.relative_path else Path(path)
        return CMakePath(self.path, self.variable, rel_path)

    def __str__(self) -> str:
        return self.to_string()

    def with_suffix(self, suffix: str) -> "CMakePath":
        if self.relative_path:
            new_relative_path = self.relative_path.with_suffix(suffix)
            return CMakePath(self.path, self.variable, new_relative_path)
        else:
            new_path = self.path.with_suffix(suffix)
            return CMakePath(new_path, self.variable, None)


class CMakeInclude(CMakeElement):
    def __init__(self, path: str | CMakePath) -> None:
        super().__init__()
        self.path = path

    def to_string(self) -> str:
        return f"include({self.path})"


class CMakeIncludeDirectories(CMakeElement):
    def __init__(self, paths: list[CMakePath]) -> None:
        super().__init__()
        self.paths = paths

    def to_string(self) -> str:
        return "\n".join(["include_directories(", *self._add_tabulated_paths(self.paths), ")"])

    def _add_tabulated_paths(self, paths: list[CMakePath]) -> list[str]:
        return [self._add_tabulated_path(path) for path in paths]

    def _add_tabulated_path(self, path: CMakePath) -> str:
        return self.tab_prefix + path.to_string()


class CMakeTargetIncludeDirectories(CMakeElement):
    def __init__(self, target_name: str, paths: list[CMakePath], visibility: str = "PRIVATE") -> None:
        super().__init__()
        self.target_name = target_name
        self.paths = paths
        self.visibility = visibility  # PRIVATE, PUBLIC, or INTERFACE

    def to_string(self) -> str:
        if not self.paths:
            return ""
        paths_str = " ".join(path.to_string() for path in self.paths)
        return f"target_include_directories({self.target_name} {self.visibility} {paths_str})"


@dataclass
class CMakeAddExecutable(CMakeElement):
    name: str
    sources: list[Union[str, CMakePath, CMakeObjectLibrary]]
    libraries: list[str] = field(default_factory=list)
    compile_options: list[str] = field(default_factory=list)
    link_options: list[str] = field(default_factory=list)
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

    def _get_sources(self) -> list[str]:
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


@dataclass
class CMakeSetTargetProperties(CMakeElement):
    target: str
    properties: dict[str, str | CMakePath]

    def to_string(self) -> str:
        if not self.properties:
            return ""

        props = []
        for key, value in self.properties.items():
            props.extend([key, str(value)])

        return f"set_target_properties({self.target} PROPERTIES {' '.join(props)})"


class CMakeCommand(CMakeElement):
    def __init__(self, command: str | CMakePath, arguments: list[str | CMakePath]) -> None:
        super().__init__()
        self.command = command
        self.arguments = arguments

    def to_string(self) -> str:
        return f"COMMAND {self.command} {' '.join(str(arg) for arg in self.arguments)}"


class CMakeExecuteProcess(CMakeElement):
    def __init__(self, description: str, commands: list[CMakeCommand]) -> None:
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

    def _get_commands(self) -> list[str]:
        return [self.tab_prefix + str(command) for command in self.commands]


class CMakeDepends(CMakeElement):
    def __init__(self, depends: Sequence[str | CMakePath]) -> None:
        super().__init__()
        self.depends = depends

    def to_string(self) -> str:
        return f"{self.tab_prefix}DEPENDS {' '.join(str(depend) for depend in self.depends)}"


class CMakeByproducts(CMakeElement):
    def __init__(self, byproducts: list[CMakePath]) -> None:
        super().__init__()
        self.byproducts = byproducts

    def to_string(self) -> str:
        return f"{self.tab_prefix}BYPRODUCTS {' '.join(str(byproduct) for byproduct in self.byproducts)}"


@dataclass
class CMakeCustomCommand(CMakeElement):
    description: str
    outputs: list[CMakePath]
    depends: Sequence[str | CMakePath]
    commands: list[CMakeCommand]

    def to_string(self) -> str:
        content = [CMakeComment(self.description), "add_custom_command("]
        content.extend(self._get_outputs())
        content.append(CMakeDepends(self.depends).to_string())
        content.extend(self._get_commands())
        content.append(")")
        return "\n".join(str(line) for line in content)

    def _get_outputs(self) -> list[str]:
        return [f"{self.tab_prefix}OUTPUT {' '.join([output.to_string() for output in self.outputs])}"]

    def _get_commands(self) -> list[str]:
        return [self.tab_prefix + str(command) for command in self.commands]


@dataclass
class CMakeCustomTarget(CMakeElement):
    def __init__(
        self,
        name: str,
        description: str,
        commands: list[CMakeCommand],
        depends: Optional[Sequence[str | CMakePath]] = None,
        default_target: bool = False,
        byproducts: Optional[list[CMakePath]] = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.description = description
        self.depends = depends
        self.commands = commands
        self.default_target = default_target
        self.byproducts = byproducts

    def to_string(self) -> str:
        add_to_all_target = "ALL" if self.default_target else ""
        content = [
            CMakeComment(self.description),
            f"add_custom_target({self.name} {add_to_all_target}",
        ]
        content.extend(self._get_commands())
        if self.depends:
            content.append(CMakeDepends(self.depends).to_string())
        if self.byproducts:
            content.append(CMakeByproducts(self.byproducts).to_string())
        content.append(")")
        return "\n".join(str(line) for line in content)

    def _get_commands(self) -> list[str]:
        return [self.tab_prefix + str(command) for command in self.commands]


class CMakeAddSubdirectory(CMakeElement):
    """
    Add_subdirectory(source_dir [binary_dir] [EXCLUDE_FROM_ALL] [SYSTEM]).

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
    def __init__(self, variable: str, values: list[str]) -> None:
        super().__init__()
        self.variable = variable
        self.values = values

    def to_string(self) -> str:
        return f"list(APPEND {self.variable} {self._get_values_string()})"

    def _get_values_string(self) -> str:
        return " ".join(self.values)


class CMakeEnableTesting(CMakeElement):
    def __init__(self) -> None:
        super().__init__()

    def to_string(self) -> str:
        return "enable_testing()"
