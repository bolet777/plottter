#!/usr/bin/env bash
# Rebuild dist/Plottter.app for macOS Apple Silicon (arm64).
# Uses packaging/.venv so the development environment keeps opencv-python.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script builds a macOS .app and must run on Darwin." >&2
  exit 1
fi

if [[ "$(uname -m)" != "arm64" ]]; then
  echo "This build targets Apple Silicon arm64 (this machine is $(uname -m))." >&2
  exit 1
fi

if [[ -n "${PYTHON:-}" ]]; then
  PY="$PYTHON"
elif command -v python3.12 >/dev/null 2>&1; then
  PY="$(command -v python3.12)"
else
  echo "Python 3.12 is required. Install it or set PYTHON=/path/to/python3.12." >&2
  exit 1
fi

"$PY" - <<'PY'
import platform
import struct
import sys

if sys.version_info < (3, 12):
    raise SystemExit(f"Python 3.12+ required, got {sys.version}")
if platform.machine() != "arm64" or struct.calcsize("P") != 8:
    raise SystemExit(f"arm64 Python required, got {platform.machine()}")
print(f"Using {sys.executable} ({sys.version.split()[0]}, {platform.machine()})")
PY

VENV="$ROOT/packaging/.venv"
if [[ ! -x "$VENV/bin/python" ]]; then
  "$PY" -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "$ROOT"

# opencv-python bundles Qt libraries that crash PyQt6's cocoa plugin inside
# a frozen app. The project dependency stays opencv-python for development;
# only this build venv replaces it with the headless wheel.
python -m pip uninstall -y opencv-python opencv-contrib-python >/dev/null 2>&1 || true
python -m pip install "opencv-python-headless>=4.9"
python -m pip install "pyinstaller>=6.11"

python - <<'PY'
import cv2

print(f"cv2 {cv2.__version__} from {cv2.__file__}")
if "qt/plugins" in cv2.__file__.lower():
    raise SystemExit("cv2 path looks like a Qt-enabled OpenCV build")
PY

python -m PyInstaller --noconfirm --clean "$ROOT/packaging/plottter.spec"

APP="$ROOT/dist/Plottter.app"
if [[ ! -d "$APP" ]]; then
  echo "Expected bundle was not produced: $APP" >&2
  exit 1
fi

missing=0
check() {
  local label="$1"
  local pattern="$2"
  if ! find "$APP" -path "$pattern" -print -quit | grep -q .; then
    echo "Missing from bundle: $label" >&2
    missing=1
  fi
}
check "Hershey SVG" "*/plottter/fonts/hershey/data/ems/EMSReadability.svg"
check "Google Fonts catalog" "*/google_fonts_catalog.json"
check "calligraphy plugin" "*/plugins/calligraphy.py"
check "turtletoy plugin" "*/plugins/turtletoy.py"
check "vectorize_trace plugin" "*/plugins/vectorize_trace.py"
check "Qt cocoa plugin" "*/platforms/libqcocoa.dylib"
if [[ "$missing" -ne 0 ]]; then
  exit 1
fi

codesign --force --deep --sign - "$APP"
echo "Built and ad-hoc signed: $APP"
