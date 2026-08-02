#!/usr/bin/env bash
# Reproduce the CI "current" lane: latest Home Assistant on a throwaway venv.
#
# The devcontainer itself matches the CI "minimum" lane (Python 3.12, the
# oldest supported Home Assistant), because that is the floor every change has
# to clear. The "current" lane tracks the latest Home Assistant, which pulls
# newer transitive dependencies and type stubs, so it can fail on code the
# minimum lane accepts. Run this before pushing anything that touches the
# shared framework, and after a long gap between contributions.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
VENV="${TMPDIR:-/tmp}/wcs-current-lane"

echo "==> Building throwaway venv at ${VENV}"
rm -rf "${VENV}"
python3 -m venv "${VENV}"
# shellcheck disable=SC1091
source "${VENV}/bin/activate"

python -m pip install --upgrade pip >/dev/null
echo "==> Installing latest Home Assistant and project requirements"
python -m pip install ruff pytest -r requirements.txt homeassistant josepy

echo "==> pytest"
pytest

echo "==> pre-commit (all files, all hooks)"
python -m pip install pre-commit >/dev/null
pre-commit run --all-files

deactivate
echo "==> Current lane clean"
