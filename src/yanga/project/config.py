from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, OrderedDict, TypeAlias

import yaml
from mashumaro import DataClassDictMixin
from py_app_dev.core.exceptions import UserNotificationException
from yaml.parser import ParserError
from yaml.scanner import ScannerError


@dataclass
class StageConfig(DataClassDictMixin):
    #: Stage name or class name if file is not specified
    stage: str
    #: Path to file with stage class
    file: Optional[str] = None
    #: Python module with stage class
    module: Optional[str] = None
    #: Stage class name
    class_name: Optional[str] = None
    #: Stage description
    description: Optional[str] = None
    #: Stage timeout in seconds
    timeout_sec: Optional[int] = None


PipelineConfig: TypeAlias = OrderedDict[str, List[StageConfig]]


@dataclass
class PlatformConfig(DataClassDictMixin):
    #: Platform name
    name: str
    #: Description
    description: Optional[str] = None
    #: Compiler name
    compiler: Optional[str] = None
    #: Compiler name
    cpp_compiler: Optional[str] = None
    #: C standard
    c_standard: Optional[str] = None
    #: C++ standard
    cpp_standard: Optional[str] = None
    #: Compile options
    compile_options: List[str] = field(default_factory=list)
    #: Link options
    link_options: List[str] = field(default_factory=list)


@dataclass
class VariantBom(DataClassDictMixin):
    #: Base variant name
    inherit: Optional[str] = None
    #: Components
    components: List[str] = field(default_factory=list)
    #: Component sources
    sources: List[str] = field(default_factory=list)


@dataclass
class VariantConfig(DataClassDictMixin):
    #: Variant name
    name: str
    #: Description
    description: Optional[str] = None
    #: Bill of materials
    bom: Optional[VariantBom] = None
    #: Platforms
    platforms: List[str] = field(default_factory=list)
    #: Configuration
    config_file: Optional[str] = None


@dataclass
class ComponentConfig(DataClassDictMixin):
    #: Component name
    name: str
    #: Description
    description: Optional[str] = None
    #: Subcomponents
    components: List[str] = field(default_factory=list)
    #: Component sources
    sources: List[str] = field(default_factory=list)
    #: Component test sources
    test_sources: List[str] = field(default_factory=list)
    #: Component include directories
    include_directories: List[str] = field(default_factory=list)
    #: Component variants
    variants: List[VariantConfig] = field(default_factory=list)


@dataclass
class YangaUserConfig(DataClassDictMixin):
    pipeline: Optional[PipelineConfig] = None
    platforms: List[PlatformConfig] = field(default_factory=list)
    variants: List[VariantConfig] = field(default_factory=list)
    components: List[ComponentConfig] = field(default_factory=list)
    # This field is intended to keep track of where configuration was loaded from and
    # it is automatically added when configuration is loaded from file
    file: Optional[Path] = None

    @classmethod
    def from_file(cls, config_file: Path) -> "YangaUserConfig":
        config_dict = cls.parse_to_dict(config_file)
        return cls.from_dict(config_dict)

    @staticmethod
    def parse_to_dict(config_file: Path) -> Dict[str, Any]:
        try:
            with open(config_file) as fs:
                config_dict = yaml.safe_load(fs)
                # Add file name to config to keep track of where configuration was loaded from
                config_dict["file"] = config_file
            return config_dict
        except ScannerError as e:
            raise UserNotificationException(f"Failed scanning configuration file '{config_file}'. \nError: {e}")
        except ParserError as e:
            raise UserNotificationException(f"Failed parsing configuration file '{config_file}'. \nError: {e}")
