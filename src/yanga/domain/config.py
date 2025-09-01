import json
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, ClassVar, Optional

import yaml
from mashumaro import DataClassDictMixin
from mashumaro.config import TO_DICT_ADD_OMIT_NONE_FLAG, BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.pipeline import PipelineConfig as GenericPipelineConfig
from pypeline.domain.pipeline import PipelineConfig
from yaml.parser import ParserError
from yaml.scanner import ScannerError


@dataclass
class WestDependency(DataClassDictMixin):
    #: Project name
    name: str
    #: Remote name
    remote: str
    #: Revision (tag, branch, or commit)
    revision: str
    #: Path where the dependency will be installed
    path: str


@dataclass
class WestRemote(DataClassDictMixin):
    #: Remote name
    name: str
    #: URL base
    url_base: str = field(metadata={"alias": "url-base"})


@dataclass
class WestManifest(DataClassDictMixin):
    #: Remote configurations
    remotes: list[WestRemote] = field(default_factory=list)
    #: Project dependencies
    projects: list[WestDependency] = field(default_factory=list)


@dataclass
class WestManifestFile(DataClassDictMixin):
    manifest: WestManifest
    # This field is intended to keep track of where configuration was loaded from and
    # it is automatically added when configuration is loaded from file
    file: Optional[Path] = None

    @classmethod
    def from_file(cls, config_file: Path) -> "WestManifestFile":
        config_dict = cls.parse_to_dict(config_file)
        return cls.from_dict(config_dict)

    @staticmethod
    def parse_to_dict(config_file: Path) -> dict[str, Any]:
        try:
            with open(config_file) as fs:
                config_dict = yaml.safe_load(fs)
                # Add file name to config to keep track of where configuration was loaded from
                config_dict["file"] = config_file
            return config_dict
        except ScannerError as e:
            raise UserNotificationException(f"Failed scanning west manifest file '{config_file}'. \nError: {e}") from e
        except ParserError as e:
            raise UserNotificationException(f"Failed parsing west manifest file '{config_file}'. \nError: {e}") from e


@dataclass
class MockingConfiguration(DataClassDictMixin):
    enabled: Optional[bool] = None
    strict: Optional[bool] = None
    exclude_symbol_patterns: list[str] | None = None


@dataclass
class TestingConfiguration(DataClassDictMixin):
    #: Component test sources
    sources: list[str] = field(default_factory=list)
    #: Mocking configuration
    mocking: Optional[MockingConfiguration] = None


@dataclass
class PlatformConfig(DataClassDictMixin):
    #: Platform name
    name: str
    #: Description
    description: Optional[str] = None
    #: Toolchain file
    toolchain_file: Optional[str] = None
    #: Build system cmake generators
    cmake_generators: GenericPipelineConfig = field(default_factory=list)
    #: Supported build types
    build_types: list[str] = field(default_factory=list)
    #: West dependencies for this platform
    west_manifest: Optional[WestManifest] = None
    # This field is intended to keep track of where configuration was loaded from and
    # it is automatically added when configuration is loaded from file
    file: Optional[Path] = None


@dataclass
class VariantBom(DataClassDictMixin):
    #: Base variant name
    inherit: Optional[str] = None
    #: Components
    components: list[str] = field(default_factory=list)
    #: Component sources
    sources: list[str] = field(default_factory=list)


@dataclass
class VariantConfig(DataClassDictMixin):
    #: Variant name
    name: str
    #: Description
    description: Optional[str] = None
    #: Bill of materials
    bom: Optional[VariantBom] = None
    #: Platform
    platform: Optional[str] = None
    #: Configuration
    features_selection_file: Optional[str] = None
    #: Generic configuration key-value pairs that will be exported as CMake variables
    config: dict[str, Any] = field(default_factory=dict)
    #: West dependencies for this variant
    west_manifest: Optional[WestManifest] = None
    # This field is intended to keep track of where configuration was loaded from and
    # it is automatically added when configuration is loaded from file
    file: Optional[Path] = None


class StringableEnum(Enum):
    @classmethod
    def from_string(cls, name: str) -> "StringableEnum":
        return getattr(cls, str(name).upper())

    def to_string(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.to_string()


def stringable_enum_field_metadata(
    enum_type: type[StringableEnum],
    alias: Optional[str] = None,
) -> dict[str, Any]:
    """Generates metadata for dataclass fields that handle stringable enum types."""
    metadata: dict[str, Callable[[Any], Any]] = {
        "deserialize": lambda type_str: (enum_type.from_string(type_str) if type_str else None),
        "serialize": lambda type_obj: type_obj.to_string() if type_obj else None,
    }
    if alias:
        metadata["alias"] = alias  # type: ignore
    return metadata


class IncludeDirectoryScope(StringableEnum):
    PUBLIC = auto()
    PRIVATE = auto()


@dataclass
class IncludeDirectory(DataClassDictMixin):
    #: Include directory path
    path: str
    #: Include directory scope
    scope: IncludeDirectoryScope = field(metadata=stringable_enum_field_metadata(IncludeDirectoryScope))


@dataclass
class ComponentConfig(DataClassDictMixin):
    #: Component name
    name: str
    #: Description
    description: Optional[str] = None
    #: Subcomponents - intended for `container` components that can collect other components to ease their management
    components: list[str] = field(default_factory=list)
    #: Component sources
    sources: list[str] = field(default_factory=list)
    #: Component test sources
    test_sources: list[str] = field(default_factory=list)
    #: Testing
    testing: Optional[TestingConfiguration] = None
    #: Documentation sources
    docs_sources: list[str] = field(default_factory=list)
    #: Component include directories
    include_directories: list[IncludeDirectory] = field(default_factory=list)
    #: Name of the components that this component requires header files from
    required_components: list[str] = field(default_factory=list)
    #: Directory relative to the project root where this component is located
    path: Optional[Path] = None

    # This field is intended to keep track of where configuration was loaded from and
    # it is automatically added when configuration is loaded from file
    file: Optional[Path] = None

    @property
    def private_include_directories(self) -> list[str]:
        return [d.path for d in self.include_directories if d.scope == IncludeDirectoryScope.PRIVATE]

    @property
    def public_include_directories(self) -> list[str]:
        return [d.path for d in self.include_directories if d.scope == IncludeDirectoryScope.PUBLIC]


@dataclass
class YangaUserConfig(DataClassDictMixin):
    #: Pipeline steps to execute
    pipeline: Optional[PipelineConfig] = None
    #: Supported platforms to build for
    platforms: list[PlatformConfig] = field(default_factory=list)
    #: Software product variants
    variants: list[VariantConfig] = field(default_factory=list)
    #: Software components that can be used to create variants
    components: list[ComponentConfig] = field(default_factory=list)

    # This field is intended to keep track of where the configuration was loaded from and
    # it is automatically added when the configuration is loaded from the file
    file: Optional[Path] = None

    @classmethod
    def from_file(cls, config_file: Path) -> "YangaUserConfig":
        config_dict = cls.parse_to_dict(config_file)
        return cls.from_dict(config_dict)

    @staticmethod
    def parse_to_dict(config_file: Path) -> dict[str, Any]:
        try:
            with open(config_file) as fs:
                config_dict = yaml.safe_load(fs)
                # Add file name to config to keep track of where configuration was loaded from
                config_dict["file"] = config_file
            return config_dict
        except ScannerError as e:
            raise UserNotificationException(f"Failed scanning configuration file '{config_file}'. \nError: {e}") from e
        except ParserError as e:
            raise UserNotificationException(f"Failed parsing configuration file '{config_file}'. \nError: {e}") from e


class BaseConfigJSONMixin(DataClassJSONMixin):
    class Config(BaseConfig):
        code_generation_options: ClassVar[list[str]] = [TO_DICT_ADD_OMIT_NONE_FLAG]

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict(omit_none=True), indent=2)

    def to_json_file(self, file_path: Path) -> None:
        file_path.write_text(self.to_json_string())
