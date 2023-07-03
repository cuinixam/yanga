import json
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Union

from mashumaro import DataClassDictMixin
from mashumaro.mixins.json import DataClassJSONMixin

from .exceptions import UserNotificationException
from .logging import logger
from .subprocess import SubprocessExecutor, get_app_path  # nosec


@dataclass
class ScoopFileElement(DataClassDictMixin):
    name: str = field(metadata={"alias": "Name"})
    source: str = field(metadata={"alias": "Source"})

    def __hash__(self) -> int:
        return hash(self.name + self.source)

    def __str__(self) -> str:
        return f"({self.source},{self.name})"


@dataclass
class ScoopInstallConfigFile(DataClassJSONMixin):
    buckets: List[ScoopFileElement]
    apps: List[ScoopFileElement]

    @property
    def bucket_names(self) -> List[str]:
        return [bucket.name for bucket in self.buckets]

    @property
    def app_names(self) -> List[str]:
        return [app.name for app in self.apps]

    @classmethod
    def from_file(cls, scoop_file: Path) -> "ScoopInstallConfigFile":
        with open(scoop_file) as f:
            return cls.from_dict(json.load(f))

    def to_file(self, scoop_file: Path) -> None:
        with open(scoop_file, "w") as f:
            json.dump(self.to_dict(), f, indent=4)


@dataclass
class InstalledScoopApp:
    name: str
    version: str
    path: Path
    manifest_file: Path
    bin_dirs: List[Path]


class ScoopWrapper:
    def __init__(self) -> None:
        self.scoop_path = self.get_scoop_path()
        self.logger = logger.bind()

    @property
    def scoop_executable(self) -> Path:
        return self.scoop_path.joinpath("scoop")

    @property
    def apps_directory(self) -> Path:
        return self.scoop_path.joinpath("apps")

    def install(self, scoop_file: Path) -> List[ScoopFileElement]:
        return self.do_install(
            ScoopInstallConfigFile.from_file(scoop_file), self.get_installed_apps()
        )

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

    def get_installed_apps(self) -> List[InstalledScoopApp]:
        installed_tools: List[InstalledScoopApp] = []
        for manifest_file in self.apps_directory.glob("**/manifest.json"):
            app_directory: Path = manifest_file.parent
            # There is a directory level for the version of the tool
            tool_name: str = app_directory.parent.name
            with open(manifest_file) as f:
                manifest_data: Dict[str, Any] = json.load(f)
                tool_version: str = manifest_data.get("version", None)
                bin_dirs: List[Path] = self.parse_bin_dirs(manifest_data.get("bin", []))
                installed_tools.append(
                    InstalledScoopApp(
                        name=tool_name,
                        version=tool_version,
                        path=app_directory,
                        manifest_file=manifest_file,
                        bin_dirs=bin_dirs,
                    )
                )
        return installed_tools

    def do_install(
        self,
        scoop_install_config: ScoopInstallConfigFile,
        installed_tools: List[InstalledScoopApp],
    ) -> List[ScoopFileElement]:
        """Check which apps are installed and install the missing ones."""
        apps_to_install = self.get_tools_to_be_installed(
            scoop_install_config, installed_tools
        )
        if not apps_to_install:
            self.logger.info("All Scoop apps already installed. Skip installation.")
            return []
        installed_apps = set(scoop_install_config.apps) - set(apps_to_install)
        self.logger.info(
            f"Scoop apps already installed: {','.join(str(app) for app in installed_apps)}"
        )
        self.logger.info(
            f"Scoop apps to install: {','.join(str(app) for app in apps_to_install)}"
        )

        # Create a temporary scoopfile with the remaining apps to install and install them
        with TemporaryDirectory() as tmp_dir:
            tmp_scoop_file = Path(tmp_dir).joinpath("scoopfile.json")
            ScoopInstallConfigFile(
                scoop_install_config.buckets, apps_to_install
            ).to_file(tmp_scoop_file)
            SubprocessExecutor(
                [self.scoop_executable, "install", tmp_scoop_file]
            ).execute()
        return apps_to_install

    @staticmethod
    def get_tools_to_be_installed(
        scoop_install_config: ScoopInstallConfigFile,
        installed_tools: List[InstalledScoopApp],
    ) -> List[ScoopFileElement]:
        """Check which apps are installed and install the missing ones."""
        installed_tools_names = {tool.name for tool in installed_tools}
        return [
            app
            for app in scoop_install_config.apps
            if app.name not in installed_tools_names
        ]
