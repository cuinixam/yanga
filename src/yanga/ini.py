import configparser
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from mashumaro import DataClassDictMixin

if sys.version_info >= (3, 11):
    import tomllib  # Python 3.11 and later
else:
    import tomli as tomllib  # For earlier Python versions


@dataclass
class YangaIni(DataClassDictMixin):
    #: Custom name for the YANGA configuration files. Default is 'yanga.yaml'
    configuration_file_name: Optional[str] = None
    #: Exclude directories from parsing
    exclude_dirs: List[str] = field(default_factory=list)

    @classmethod
    def from_toml_or_ini(cls, ini_file: Optional[Path], pyproject_toml: Optional[Path]) -> "YangaIni":
        # Initialize an empty dictionary to hold configurations
        config_data: Dict[str, Any] = {}

        # Load configurations from the INI file if provided
        if ini_file and ini_file.is_file():
            ini_config = cls.load_ini_config(ini_file)
            config_data.update(ini_config)

        # Load configurations from the TOML file if provided
        if pyproject_toml and pyproject_toml.is_file():
            toml_config = cls.load_toml_config(pyproject_toml)
            # TOML configurations take precedence over INI configurations
            config_data.update(toml_config)
        return cls.from_dict(config_data)

    @staticmethod
    def load_ini_config(ini_file: Path) -> Dict[str, Any]:
        """Read the ini file and return the configuration as a dictionary."""
        config: Dict[str, Any] = {}
        parser = configparser.ConfigParser()
        parser.read(ini_file)
        for section in parser.sections():
            for key, value in parser.items(section):
                if key == "exclude_dirs":
                    config[key] = [x.strip() for x in value.split(",")]
                else:
                    config[key] = value
        return config

    @staticmethod
    def load_toml_config(pyproject_toml: Path) -> Dict[str, Any]:
        """Read the pyproject.toml file and return the configuration as a dictionary."""
        config = {}
        with pyproject_toml.open("rb") as f:
            data = tomllib.load(f)

            # Access the [tool.yanga] section
            yanga_config = data.get("tool", {}).get("yanga", {})
            config.update(yanga_config)
        return config
