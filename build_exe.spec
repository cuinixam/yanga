# -*- mode: python ; coding: utf-8 -*-

import cookiecutter
from pathlib import Path

# Yanga is using the cookiecutter main to initialize a yanga project from a template
# The cookiecutter main requires the VERSION.txt and it is not included in the package
# We need to copy the VERSION.txt to the build directory in the cookiecutter directory.
cookiecutter_version_file = Path(cookiecutter.__file__).parent / "VERSION.txt"

block_cipher = None

a = Analysis(
    ["src/yanga/ymain.py"],
    pathex=[],
    binaries=[],
    datas=[
        (cookiecutter_version_file.as_posix(), "cookiecutter"),
        ("src/yanga/commands/project_templates/", "yanga/commands/project_templates/"),
        ("src/yanga/gui/resources", "yanga/gui/resources"),
    ],
    hiddenimports=["cookiecutter.extensions", "yanga.ybuild.stages"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="yanga",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)
