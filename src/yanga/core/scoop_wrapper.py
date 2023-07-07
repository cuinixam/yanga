import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Union

from mashumaro import DataClassDictMixin
from mashumaro.mixins.json import DataClassJSONMixin

from .exceptions import UserNotificationException
from .logging import logger
from .subprocess import SubprocessExecutor, which  # nosec


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
class InstalledApp:
    #: App name
    name: str
    #: App version
    version: str
    #: App root directory
    path: Path
    #: List of bin directories relative to the app path
    bin_dirs: List[Path]


@dataclass
class InstalledScoopApp(InstalledApp):
    #: App scoop manifest file
    manifest_file: Path


class ScoopWrapper:
    def __init__(self) -> None:
        self.scoop_executable = self._find_scoop_executable()
        self.scoop_root_dir = self._find_scoop_root_dir(self.scoop_executable)
        self.logger = logger.bind()

    @property
    def apps_directory(self) -> Path:
        return self.scoop_root_dir.joinpath("apps")

    def install(self, scoop_file: Path) -> List[InstalledScoopApp]:
        """Install scoop apps from a scoop file.
        It returns a list with all apps required to be installed as installed apps."""
        return self.do_install(
            ScoopInstallConfigFile.from_file(scoop_file), self.get_installed_apps()
        )

    def _find_scoop_executable(self) -> Path:
        scoop_path = which("scoop")
        if not scoop_path:
            raise UserNotificationException(
                "Scoop not found in PATH. Please run the build script again."
            )
        return scoop_path

    def _find_scoop_root_dir(self, scoop_executable_path: Path) -> Path:
        pattern = r"^(.*?/scoop/)"
        match = re.match(pattern, scoop_executable_path.absolute().as_posix())

        if match:
            return Path(match.group(1))
        else:
            raise UserNotificationException(
                f"Could not determine scoop directory for {scoop_executable_path}."
            )

    def parse_bin_dirs(
        self, bin_data: Union[str, List[Union[str, List[str]]]]
    ) -> List[Path]:
        """Parse the bin directory from the manifest file."""

        def get_parent_dir(bin_entry: Union[str, List[str]]) -> Optional[Path]:
            bin_path = (
                Path(bin_entry[0]) if isinstance(bin_entry, list) else Path(bin_entry)
            )
            return bin_path.parent if len(bin_path.parts) > 1 else None

        result = []
        if isinstance(bin_data, str):
            result = [parent for parent in [get_parent_dir(bin_data)] if parent]
        elif isinstance(bin_data, list):
            result = [
                parent
                for parent in [get_parent_dir(bin_entry) for bin_entry in bin_data]
                if parent
            ]
        return list(set(result))

    def parse_manifest_file(self, manifest_file: Path) -> InstalledScoopApp:
        app_directory: Path = manifest_file.parent
        tool_name: str = app_directory.parent.name
        with open(manifest_file) as f:
            manifest_data: Dict[str, Any] = json.load(f)
            tool_version: str = manifest_data.get("version", None)
            bin_dirs: List[Path] = self.parse_bin_dirs(manifest_data.get("bin", []))
            return InstalledScoopApp(
                name=tool_name,
                version=tool_version,
                path=app_directory,
                manifest_file=manifest_file,
                bin_dirs=bin_dirs,
            )

    def get_installed_apps(self) -> List[InstalledScoopApp]:
        installed_tools: List[InstalledScoopApp] = []
        self.logger.info(f"Looking for installed apps in {self.apps_directory}")
        manifest_files = list(self.apps_directory.glob("*/*/manifest.json"))

        with ThreadPoolExecutor() as executor:
            future_to_file = {
                executor.submit(self.parse_manifest_file, manifest_file): manifest_file
                for manifest_file in manifest_files
            }
            for future in as_completed(future_to_file):
                installed_tools.append(future.result())

        return installed_tools

    def do_install(
        self,
        scoop_install_config: ScoopInstallConfigFile,
        installed_apps: List[InstalledScoopApp],
    ) -> List[InstalledScoopApp]:
        """Install scoop apps from a scoop file."""

        newly_installed_apps = self.do_install_missing(
            scoop_install_config, installed_apps
        )
        # If some apps where just installed we need to update the list of installed apps
        if newly_installed_apps:
            self.logger.info(
                "New apps were installed, update the list of installed apps."
            )
            updated_installed_apps = self.get_installed_apps()
        else:
            updated_installed_apps = installed_apps
        apps = self.map_required_apps_to_installed_apps(
            scoop_install_config.app_names, updated_installed_apps
        )
        return apps

    def do_install_missing(
        self,
        scoop_install_config: ScoopInstallConfigFile,
        installed_apps: List[InstalledScoopApp],
    ) -> List[ScoopFileElement]:
        """Check which apps are installed and install the missing ones."""
        apps_to_install = self.get_tools_to_be_installed(
            scoop_install_config, installed_apps
        )
        if not apps_to_install:
            self.logger.info("All Scoop apps already installed. Skip installation.")
            return []
        already_installed_apps = set(scoop_install_config.apps) - set(apps_to_install)
        if already_installed_apps:
            self.logger.info(
                f"Scoop apps already installed: {','.join(str(app) for app in already_installed_apps)}"
            )
        self.logger.info(
            f"Start installing missing apps: {','.join(str(app) for app in apps_to_install)}"
        )

        # Create a temporary scoopfile with the remaining apps to install and install them
        with TemporaryDirectory() as tmp_dir:
            tmp_scoop_file = Path(tmp_dir).joinpath("scoopfile.json")
            ScoopInstallConfigFile(
                scoop_install_config.buckets, apps_to_install
            ).to_file(tmp_scoop_file)
            SubprocessExecutor(
                [self.scoop_executable, "import", tmp_scoop_file]
            ).execute()
        return apps_to_install

    @staticmethod
    def map_required_apps_to_installed_apps(
        app_names: List[str],
        installed_apps: List[InstalledScoopApp],
    ) -> List[InstalledScoopApp]:
        """Map the required apps to the installed apps."""
        # convert the list of installed apps into a dictionary for faster lookup
        installed_apps_dict = {app.name: app for app in installed_apps}
        try:
            apps = [installed_apps_dict[app_name] for app_name in app_names]
        except KeyError as e:
            raise UserNotificationException(
                f"Could not find {e} in the installed apps. Something went wrong during the scoop installation."
            )
        return apps

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
