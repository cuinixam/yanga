import io
import json
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

import yaml
from mashumaro import DataClassDictMixin
from mashumaro.config import TO_DICT_ADD_OMIT_NONE_FLAG, BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin
from py_app_dev.core.exceptions import UserNotificationException
from pypeline.domain.pipeline import PipelineConfig, PipelineStepConfig
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
    #: Build system cmake generators
    cmake_generators: List[PipelineStepConfig] = field(default_factory=list)
    # This field is intended to keep track of where configuration was loaded from and
    # it is automatically added when configuration is loaded from file
    file: Optional[Path] = None


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
    # This field is intended to keep track of where configuration was loaded from and
    # it is automatically added when configuration is loaded from file
    file: Optional[Path] = None


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
    # This field is intended to keep track of where configuration was loaded from and
    # it is automatically added when configuration is loaded from file
    file: Optional[Path] = None


@dataclass
class YangaUserConfig(DataClassDictMixin):
    pipeline: Optional[PipelineConfig] = None
    platforms: List[PlatformConfig] = field(default_factory=list)
    variants: List[VariantConfig] = field(default_factory=list)
    components: List[ComponentConfig] = field(default_factory=list)
    # This field is intended to keep track of where the configuration was loaded from and
    # it is automatically added when the configuration is loaded from the file
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
            raise UserNotificationException(f"Failed scanning configuration file '{config_file}'. \nError: {e}") from e
        except ParserError as e:
            raise UserNotificationException(f"Failed parsing configuration file '{config_file}'. \nError: {e}") from e


class BaseConfigJSONMixin(DataClassJSONMixin):
    class Config(BaseConfig):
        code_generation_options: ClassVar[List[str]] = [TO_DICT_ADD_OMIT_NONE_FLAG]

    @classmethod
    def from_json_file(cls, file_path: Path) -> "BaseConfigJSONMixin":
        try:
            result = cls.from_dict(json.loads(file_path.read_text()))
        except Exception as e:
            output = io.StringIO()
            traceback.print_exc(file=output)
            raise UserNotificationException(output.getvalue()) from e
        return result

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict(omit_none=True), indent=2)

    def to_json_file(self, file_path: Path) -> None:
        file_path.write_text(self.to_json_string())
