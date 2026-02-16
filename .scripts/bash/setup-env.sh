#!/usr/bin/env bash
set -u

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR" || fail "cannot change directory to repository root"

if [ ! -f ".dev/env/bin/activate" ]; then
  fail ".dev/env not found. Run the design phase setup to create the scaffolding environment"
fi

if ! command -v python >/dev/null 2>&1; then
  fail "python not found in PATH. Install Python 3.10 or higher"
fi

python -c "import sys; print(sys.version); raise SystemExit(0 if sys.version_info >= (3,10) else 1)" \
  || fail "Python 3.10 or higher is required"

if [ ! -f "requirements.txt" ]; then
  fail "requirements.txt not found in repository root"
fi

if [ -d "env" ]; then
  echo "Main environment already exists. Skipping creation."
else
  echo "Creating main environment at env"
  python -m venv env || fail "failed to create env"
fi

# shellcheck disable=SC1091
. "env/bin/activate" || fail "failed to activate env"

python -m pip install --upgrade pip || fail "failed to upgrade pip"
python -m pip install -r requirements.txt || fail "failed to install dependencies"
python -m pip install build setuptools wheel || fail "failed to install build tools"

echo "Setup complete."
