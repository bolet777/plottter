# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: macOS arm64, onedir, windowed → dist/Plottter.app.

Run via packaging/build_macos.sh (that script selects the arm64 build venv).
"""

from pathlib import Path

from PyInstaller.building.datastruct import TOC
from PyInstaller.utils.hooks import collect_submodules

# SPECPATH is the directory containing this spec (packaging/).
ROOT = Path(SPECPATH).resolve().parent

datas = [
    # Path(__file__) for hershey.catalog points at .../plottter/fonts/hershey/
    (
        str(ROOT / "src" / "plottter" / "fonts" / "hershey" / "data"),
        "plottter/fonts/hershey/data",
    ),
    # google_fonts.py: Path(__file__).parent / "google_fonts_catalog.json"
    (
        str(ROOT / "src" / "plottter" / "fonts" / "google_fonts_catalog.json"),
        "plottter/fonts",
    ),
    # Loaded only when sys.frozen: see plugin_loader._bundled_plugin_dir.
    (str(ROOT / "plugins"), "plugins"),
]

hiddenimports = [
    "noise",
    "cv2",
    "PIL",
    "shapely",
    "svgwrite",
    "fontTools",
    "fontTools.ttLib",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
]
# Generator and processing code imports many scipy submodules lazily.
hiddenimports += collect_submodules(
    "scipy",
    filter=lambda name: not any(
        part in {"tests", "testing", "_tests"} for part in name.split(".")
    ),
)


def _without_cv2_qt(entries):
    """Drop Qt files a non-headless cv2 wheel would ship next to PyQt6."""
    kept = []
    for entry in entries:
        dest = str(entry[0]).replace("\\", "/").lower()
        if "cv2" in dest and ("qt5" in dest or "qt6" in dest or "/qt/" in dest):
            continue
        kept.append(entry)
    return kept


a = Analysis(
    [str(ROOT / "src" / "plottter" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "numba",
        "llvmlite",
        "quickjs",
        "potrace",
        "pyaxidraw",
        "matplotlib",
        "tkinter",
        "pytest",
        "IPython",
    ],
    noarchive=False,
    optimize=0,
)
a.binaries = TOC(_without_cv2_qt(a.binaries))
a.datas = TOC(_without_cv2_qt(a.datas))

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Plottter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Plottter",
)
app = BUNDLE(
    coll,
    name="Plottter.app",
    icon=None,
    bundle_identifier="com.plottter.Plottter",
    info_plist={
        "CFBundleName": "Plottter",
        "CFBundleDisplayName": "Plottter",
        "CFBundleIdentifier": "com.plottter.Plottter",
        "NSHighResolutionCapable": True,
    },
)
