from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, OrderedDict, TypeAlias

import yaml
from mashumaro import DataClassDictMixin


@dataclass
class StageConfig(DataClassDictMixin):
    #: Stage name or class name if file is not specified
    stage: str
    #: Path to file with stage class
    file: Optional[str] = None
    #: Stage class name
    class_name: Optional[str] = None
    #: Stage description
    description: Optional[str] = None
    #: Stage timeout in seconds
    timeout_sec: Optional[int] = None


PipelineConfig: TypeAlias = OrderedDict[str, List[StageConfig]]


@dataclass
class YangaConfig(DataClassDictMixin):
    #: Pipeline stages
    pipeline: PipelineConfig

    @classmethod
    def from_file(cls, config_file: Path) -> "YangaConfig":
        with open(config_file) as fs:
            config_dict = yaml.safe_load(fs)
        return cls.from_dict(config_dict)
