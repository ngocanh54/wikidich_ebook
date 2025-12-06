# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Wikidich Ebook Creator macOS app.
Build with: pyinstaller wikidich_ebook.spec
"""

import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Collect all data files from ebooklib and other packages
datas = []
datas += collect_data_files('ebooklib')
datas += collect_data_files('tqdm')

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'wikidich_ebook',
        'wikidich_ebook.models',
        'wikidich_ebook.config',
        'wikidich_ebook.utils',
        'wikidich_ebook.scraper',
        'wikidich_ebook.parser',
        'wikidich_ebook.downloader',
        'wikidich_ebook.epub_builder',
        'wikidich_ebook.workflow',
        'wikidich_ebook.updater',
        'selenium',
        'webdriver_manager',
        'packaging',
        'packaging.version',
        'packaging.specifiers',
        'packaging.requirements',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'PIL',
        'tkinter',
        'numpy',
        'scipy',
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
    name='WikidichEbookCreator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WikidichEbookCreator',
)

app = BUNDLE(
    coll,
    name='Wikidich Ebook Creator.app',
    icon=None,  # Add your icon path here if you have one
    bundle_identifier='com.wikidich.ebookcreator',
    version='2.0.0',
    info_plist={
        'CFBundleName': 'Wikidich Ebook Creator',
        'CFBundleDisplayName': 'Wikidich Ebook Creator',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'CFBundleExecutable': 'WikidichEbookCreator',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
        'NSRequiresAquaSystemAppearance': False,
        'CFBundleDocumentTypes': [],
    },
)
