import json
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from mashumaro import DataClassDictMixin
from py_app_dev.core.logging import logger

from yanga.cmake.generator import GeneratedFileIf
from yanga.domain.config import BaseConfigJSONMixin
from yanga.domain.project_slurper import YangaProjectSlurper


@dataclass
class VSCodeCMakeKit(DataClassDictMixin):
    name: str
    toolchainFile: str


class VSCodeCMakeKitsFile(GeneratedFileIf):
    def __init__(self, path: Path, kits: list[VSCodeCMakeKit]) -> None:
        self.kits = kits
        super().__init__(path)

    def to_string(self) -> str:
        return json.dumps([kit.to_dict() for kit in self.kits], indent=2)


@dataclass
class VSCodeCMakeVariantSettings(BaseConfigJSONMixin):
    variant_name: str = field(metadata={"alias": "VARIANT"})


@dataclass
class VSCodeCMakeVariantChoice(BaseConfigJSONMixin):
    short: str
    settings: VSCodeCMakeVariantSettings | None = None
    build_type: str | None = field(default=None, metadata={"alias": "buildType"})


@dataclass
class VSCodeCMakeVariantElement(BaseConfigJSONMixin):
    choices: OrderedDict[str, VSCodeCMakeVariantChoice]
    default: str


@dataclass
class VSCodeCMakeVariantsData(BaseConfigJSONMixin):
    variant: VSCodeCMakeVariantElement
    build_type: VSCodeCMakeVariantElement = field(metadata={"alias": "buildType"})


class VSCodeCMakeVariantsFile(GeneratedFileIf):
    def __init__(self, path: Path, variants_data: VSCodeCMakeVariantsData) -> None:
        super().__init__(path)
        self.variants_data = variants_data

    def to_string(self) -> str:
        return self.variants_data.to_json_string()


class IDEProjectGenerator:
    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.vscode_dir = self.project_dir / ".vscode"
        self.logger = logger.bind()
        self.project_slurper = YangaProjectSlurper(self.project_dir)

    def run(self) -> None:
        self.logger.info(f"Generating VS Code project files in {self.project_dir} ...")
        self.create_cmake_kits_file().to_file()
        self.create_cmake_variants_file().to_file()

    def create_cmake_kits_file(self) -> VSCodeCMakeKitsFile:
        kits: list[VSCodeCMakeKit] = []

        # Create a kit entry for each platform
        for platform in self.project_slurper.platforms:
            kit = VSCodeCMakeKit(
                name=platform.name,
                toolchainFile=platform.toolchain_file or "",
            )
            kits.append(kit)

        return VSCodeCMakeKitsFile(self.vscode_dir / "cmake-kits.json", kits)

    def create_cmake_variants_file(self) -> VSCodeCMakeVariantsFile:
        # Collect all variants
        variant_choices = OrderedDict()
        default_variant = None

        for variant in self.project_slurper.variants:
            variant_choice = VSCodeCMakeVariantChoice(short=variant.name, settings=VSCodeCMakeVariantSettings(variant_name=variant.name))
            variant_choices[variant.name] = variant_choice
            if default_variant is None:
                default_variant = variant.name

        # Collect all build types from all platforms
        build_type_choices = OrderedDict()
        default_build_type = "Debug"

        all_build_types = set()
        for platform in self.project_slurper.platforms:
            all_build_types.update(platform.build_types)

        # If no build types are defined in platforms, use standard ones
        if not all_build_types:
            all_build_types = {"Debug", "Release"}

        for build_type in sorted(all_build_types):
            build_type_choice = VSCodeCMakeVariantChoice(
                short=build_type,
                build_type=build_type,
                # No settings field for build types
            )
            build_type_choices[build_type] = build_type_choice
            if build_type == "Debug":
                default_build_type = build_type

        # Create variant and build type elements
        variant_element = VSCodeCMakeVariantElement(choices=variant_choices, default=default_variant or "default")

        build_type_element = VSCodeCMakeVariantElement(choices=build_type_choices, default=default_build_type)

        variants_data = VSCodeCMakeVariantsData(variant=variant_element, build_type=build_type_element)

        return VSCodeCMakeVariantsFile(self.vscode_dir / "cmake-variants.json", variants_data)
