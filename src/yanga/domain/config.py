from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from mashumaro import DataClassDictMixin
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.pipeline import PipelineConfig
from yaml.parser import ParserError
from yaml.scanner import ScannerError


@dataclass
class PlatformConfig(DataClassDictMixin):
    #: Platform name
    name: str
    #: Description
    description: Optional[str] = None
    #: Toolchain file
    toolchain_file: Optional[str] = None


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
    #: Platform
    platform: Optional[str] = None
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
