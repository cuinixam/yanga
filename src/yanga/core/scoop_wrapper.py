import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .exceptions import UserNotificationException
from .subprocess import SubprocessExecutor, get_app_path  # nosec


@dataclass
class ScoopApp:
    name: str
    version: str
    path: Path
    manifest_file: Path
    bin_dirs: List[Path]


class ScoopWrapper:
    def __init__(self) -> None:
        self.scoop_path = self.get_scoop_path()

    @property
    def apps_directory(self) -> Path:
        return self.scoop_path.joinpath("apps")

    def install(self, scoop_file: Path) -> List[ScoopApp]:
        SubprocessExecutor([self.scoop_path, "install", scoop_file]).execute()
        # TODO: return the list of the installed apps
        return []

    def get_scoop_path(self) -> Path:
        scoop_path = get_app_path("scoop")
        if not scoop_path:
            raise UserNotificationException(
                "Scoop not found in PATH. Please run the build script again."
            )
        return scoop_path

    def parse_bin_dirs(
        self, bin_data: Union[str, List[Union[str, List[str]]]]
    ) -> List[Path]:
        """Parse the bin directory from the manifest file."""

        def get_parent_dir(bin_entry: Union[str, List[str]]) -> Optional[Path]:
            bin_path = (
                Path(bin_entry[0]) if isinstance(bin_entry, list) else Path(bin_entry)
            )
            return bin_path.parent if len(bin_path.parts) > 1 else None

        if isinstance(bin_data, str):
            return [parent for parent in [get_parent_dir(bin_data)] if parent]
        elif isinstance(bin_data, list):
            return [
                parent
                for parent in [get_parent_dir(bin_entry) for bin_entry in bin_data]
                if parent
            ]
        return []

    def get_installed_tools(self) -> List[ScoopApp]:
        installed_tools: List[ScoopApp] = []
        for manifest_file in self.apps_directory.glob("**/manifest.json"):
            app_directory: Path = manifest_file.parent
            # There is a directory level for the version of the tool
            tool_name: str = app_directory.parent.name
            with open(manifest_file) as f:
                manifest_data: Dict[str, Any] = json.load(f)
                tool_version: str = manifest_data.get("version", None)
                bin_dirs: List[Path] = self.parse_bin_dirs(manifest_data.get("bin", []))
                installed_tools.append(
                    ScoopApp(
                        name=tool_name,
                        version=tool_version,
                        path=app_directory,
                        manifest_file=manifest_file,
                        bin_dirs=bin_dirs,
                    )
                )
        return installed_tools
