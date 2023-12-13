from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class IncludeDirectoriesProvider(ABC):
    @abstractmethod
    def get_include_directories(self) -> List[Path]:
        ...
