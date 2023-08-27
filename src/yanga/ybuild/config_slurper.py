from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

from yanga.ybuild.config import YangaUserConfig


class YangaConfigSlurper:
    """Read all 'yanga.yaml' configuration files from the project."""

    CONFIG_FILE = "yanga.yaml"

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir

    def slurp(self) -> List[YangaUserConfig]:
        user_configs = []
        config_files = list(self.project_dir.glob(f"*/*/{self.CONFIG_FILE}"))
        with ThreadPoolExecutor() as executor:
            future_to_file = {
                executor.submit(self.parse_config_file, config_file): config_file
                for config_file in config_files
            }
            for future in as_completed(future_to_file):
                user_configs.append(future.result())
        return user_configs

    def parse_config_file(self, config_file: Path) -> YangaUserConfig:
        return YangaUserConfig.from_file(config_file)
