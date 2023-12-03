import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Set

from yanga.project.config import YangaUserConfig


def find_files(start_dir: Path, search_pattern: str, exclude_dirs: List[str] = []) -> Set[Path]:
    """Find files matching the search_pattern within start_dir, excluding the directories in exclude_dirs.

    Args:
        start_dir (Path): The directory to start the search from.
        search_pattern (str): The pattern of file names to search for.
        exclude_dirs (List[str]): A list of relative paths to exclude from the search.

    Returns:
        Set[Path]: A set of Paths to the files found.
    """
    start_dir = start_dir.resolve()
    exclude_paths = {start_dir.joinpath(d) for d in exclude_dirs}
    found_files = set()

    for dirpath, dirnames, filenames in os.walk(start_dir):
        # Modify dirnames in-place when you want to prevent os.walk from descending
        # into certain directories.
        # It's a feature of os.walk that allows for more efficient file system operations.
        dirnames[:] = [d for d in dirnames if not _is_excluded(Path(dirpath).joinpath(d), exclude_paths)]
        for filename in filenames:
            if Path(filename).match(search_pattern):
                found_files.add(Path(dirpath).joinpath(filename))

    return found_files


def _is_excluded(dir_path: Path, exclude_paths: Set[Path]) -> bool:
    """Check if the directory is in the exclude paths set."""
    return any(dir_path == exclude_path or dir_path.is_relative_to(exclude_path) for exclude_path in exclude_paths)


class YangaConfigSlurper:
    """Read all 'yanga.yaml' configuration files from the project."""

    CONFIG_FILE = "yanga.yaml"

    def __init__(self, project_dir: Path, exclude_dirs: List[str] = []) -> None:
        self.project_dir = project_dir
        self.exclude_dirs = exclude_dirs

    def slurp(self) -> List[YangaUserConfig]:
        user_configs = []
        config_files = find_files(self.project_dir, self.CONFIG_FILE, self.exclude_dirs)
        with ThreadPoolExecutor() as executor:
            future_to_file = {
                executor.submit(self.parse_config_file, config_file): config_file for config_file in config_files
            }
            for future in as_completed(future_to_file):
                user_configs.append(future.result())
        return user_configs

    def parse_config_file(self, config_file: Path) -> YangaUserConfig:
        return YangaUserConfig.from_file(config_file)
