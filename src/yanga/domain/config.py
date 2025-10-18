import json
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Optional

import yaml
from mashumaro.config import BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin
from py_app_dev.core.config import BaseConfigDictMixin
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.pipeline import PipelineConfig as GenericPipelineConfig
from py_app_dev.core.scoop_wrapper import ScoopFileElement
from pypeline.domain.pipeline import PipelineConfig
from yaml.parser import ParserError
from yaml.scanner import ScannerError


class BaseConfigJSONMixin(DataClassJSONMixin):
    class Config(BaseConfig):
        omit_none = True
        serialize_by_alias = True

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_json_file(self, file_path: Path) -> None:
        file_path.write_text(self.to_json_string())


@dataclass
class WestDependency(BaseConfigDictMixin):
    #: Project name
    name: str
    #: Remote name
    remote: str
    #: Revision (tag, branch, or commit)
    revision: str
    #: Path where the dependency will be installed
    path: str


@dataclass
class WestRemote(BaseConfigDictMixin):
    #: Remote name
    name: str
    #: URL base
    url_base: str = field(metadata={"alias": "url-base"})


@dataclass
class WestManifest(BaseConfigDictMixin):
    #: Remote configurations
    remotes: list[WestRemote] = field(default_factory=list)
    #: Project dependencies
    projects: list[WestDependency] = field(default_factory=list)


@dataclass
class WestManifestFile(BaseConfigDictMixin):
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
class ScoopManifest(BaseConfigJSONMixin):
    #: Scoop buckets
    buckets: list[ScoopFileElement] = field(default_factory=list)
    #: Scoop applications
    apps: list[ScoopFileElement] = field(default_factory=list)
    # This field is intended to keep track of where configuration was loaded from and
    # it is automatically added when configuration is loaded from file
    file: Optional[Path] = None

    @classmethod
    def from_file(cls, config_file: Path) -> "ScoopManifest":
        config_dict = cls.parse_to_dict(config_file)
        return cls.from_dict(config_dict)

    @staticmethod
    def parse_to_dict(config_file: Path) -> dict[str, Any]:
        try:
            with open(config_file) as fs:
                config_dict = json.loads(fs.read())
                # Add file name to config to keep track of where configuration was loaded from
                config_dict["file"] = config_file
            return config_dict
        except json.JSONDecodeError as e:
            raise UserNotificationException(f"Failed parsing scoop manifest file '{config_file}'. \nError: {e}") from e


@dataclass
class MockingConfiguration(BaseConfigDictMixin):
    enabled: Optional[bool] = None
    strict: Optional[bool] = None
    exclude_symbol_patterns: list[str] | None = None


@dataclass
class TestingConfiguration(BaseConfigDictMixin):
    #: Component test sources
    sources: list[str] = field(default_factory=list)
    #: Mocking configuration
    mocking: Optional[MockingConfiguration] = None


@dataclass
class DocsConfiguration(BaseConfigDictMixin):
    #: Component documentation sources
    sources: list[str] = field(default_factory=list)
    #: Do not generate documentation for the productive code.
    #  This might be used for integration tests components to avoid generating docs for productive code from other components.
    exclude_productive_code: bool = False


@dataclass
class PlatformConfig(BaseConfigDictMixin):
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
    #: Supported targets
    build_targets: Optional[list[str]] = None
    #: West dependencies for this platform
    west_manifest: Optional[WestManifest] = None
    #: Scoop dependencies for this platform
    scoop_manifest: Optional[ScoopManifest] = None
    #: Platform specific components
    components: Optional[list[str]] = None
    # This field is intended to keep track of where configuration was loaded from and
    # it is automatically added when configuration is loaded from file
    file: Optional[Path] = None


@dataclass
class VariantPlatformsConfig(BaseConfigDictMixin):
    """Platform specific configuration, used in case the variant needs to defines specific settings for some platforms."""

    #: Components
    components: list[str] = field(default_factory=list)
    #: Generic configuration key-value pairs that will be exported as CMake variables
    config: dict[str, Any] = field(default_factory=dict)
    #: West dependencies for this platform-specific variant configuration
    west_manifest: Optional[WestManifest] = None


@dataclass
class VariantConfig(BaseConfigDictMixin):
    #: Variant name
    name: str
    #: Description
    description: Optional[str] = None
    #: Components
    components: list[str] = field(default_factory=list)
    #: Platform specific configuration, used in case the variant needs to defines specific settings for some platforms
    platforms: Optional[dict[str, VariantPlatformsConfig]] = None
    #: Configuration
    features_selection_file: Optional[str] = None
    #: Generic configuration key-value pairs that will be exported as CMake variables
    config: dict[str, Any] = field(default_factory=dict)
    #: West dependencies for this variant
    west_manifest: Optional[WestManifest] = None
    #: Scoop dependencies for this variant
    scoop_manifest: Optional[ScoopManifest] = None
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
class IncludeDirectory(BaseConfigDictMixin):
    #: Include directory path
    path: str
    #: Include directory scope
    scope: IncludeDirectoryScope = field(metadata=stringable_enum_field_metadata(IncludeDirectoryScope))


@dataclass
class ComponentConfig(BaseConfigDictMixin):
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
    #: Documentation configuration
    docs: Optional[DocsConfiguration] = None
    #: Component include directories
    include_directories: list[IncludeDirectory] = field(default_factory=list)
    #: Name of the components that this component requires header files from
    required_components: list[str] = field(default_factory=list)
    #: Component alias to be used by other components to refer to this component
    alias: Optional[str] = None
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
class YangaUserConfig(BaseConfigDictMixin):
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
