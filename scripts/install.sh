#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ARBOR_VENV_DIR:-$ROOT_DIR/.venv}"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "error: missing required command: $1" >&2
    exit 1
  fi
}

need git
need python3

cd "$ROOT_DIR"

echo "Installing Arbor in $ROOT_DIR"
echo "Using virtual environment: $VENV_DIR"

python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("error: Python >= 3.10 is required")
print(f"Python {sys.version.split()[0]}")
PY

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -e .

echo
python -m arbor.cli.app version
python -m arbor.cli.app doctor || true

echo
echo "Done. Next:"
echo "  source \"$VENV_DIR/bin/activate\""
echo "  arbor setup"
echo "  arbor demo"
