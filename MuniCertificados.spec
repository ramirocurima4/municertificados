# -*- mode: python ; coding: utf-8 -*-
"""Especificación PyInstaller (--onedir) para MuniCertificados."""

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

ctk_datas = collect_data_files("customtkinter")

app_datas = [
    ("assets/fonts", "assets/fonts"),
    ("assets/templates", "assets/templates"),
    ("assets/logos", "assets/logos"),
    ("assets/app_icon.ico", "assets"),
] + ctk_datas

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=app_datas,
    hiddenimports=[
        "customtkinter",
        "PIL",
        "PIL._tkinter_finder",
        "pymupdf",
        "openpyxl",
        "sqlite3",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pandas",
        "scipy",
        "matplotlib",
        "pytest",
        "IPython",
        "notebook",
        "onnxruntime",
        "pymupdf4llm",
        "pymupdf_layout",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MuniCertificados",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/app_icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MuniCertificados",
)
