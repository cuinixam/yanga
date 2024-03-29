# -*- mode: python ; coding: utf-8 -*-

import cookiecutter
from pathlib import Path

# Yanga is using the cookiecutter main to initialize a yanga project from a template
# The cookiecutter main requires the VERSION.txt and it is not included in the package
# We need to copy the VERSION.txt to the build directory in the cookiecutter directory.
cookiecutter_version_file = Path(cookiecutter.__file__).parent / "VERSION.txt"

# The Yanga pipeline steps and cmake generators modules, are modules which can be loaded
# dynamically if found in the user configuration files (yanga.yaml).
modules = [f.stem for f in Path("src/yanga/steps").glob("*.py") if f.name != "__init__.py"]
hidden_module_paths = [f"yanga.steps.{module}" for module in modules]
modules = [f.stem for f in Path("src/yanga/cmake").glob("*.py") if f.name != "__init__.py"]
hidden_module_paths = hidden_module_paths + [f"yanga.cmake.{module}" for module in modules]

block_cipher = None

# Analysis: Identifies the files needed for the executable
a = Analysis(
    ["src/yanga/ymain.py"],
    pathex=[],
    binaries=[],
    datas=[
        (cookiecutter_version_file.as_posix(), "cookiecutter"),
        ("src/yanga/commands/project_templates/", "yanga/commands/project_templates/"),
        ("src/yanga/gui/resources", "yanga/gui/resources"),
    ],
    hiddenimports=["shellingham.nt", "shellingham.posix", "cookiecutter.extensions"] + hidden_module_paths,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE: Creates the executable. This step does not bundle everything into a single file.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="yanga",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    icon="src/yanga/gui/resources/yanga.ico",
)

# COLLECT: Gathers all necessary files into one directory for --onedir mode.
# This is the key step ensuring the executable uses local files directly.
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name="yanga", strip=False, upx=True, upx_exclude=[])

# This spec file setup ensures that your application is packaged in a way that all dependencies
# are located in the same directory as the executable, without needing to unpack them at runtime.
