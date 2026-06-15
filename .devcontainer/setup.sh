#!/usr/bin/env bash
# Provision the development environment for hacs_waste_collection_schedule.
# Runs automatically as the devcontainer "postCreateCommand" so the container
# is ready to use without any further manual steps.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Upgrading pip tooling"
python3 -m pip install --upgrade pip setuptools wheel

echo "==> Installing project requirements (requirements.txt)"
python3 -m pip install -r requirements.txt

echo "==> Installing development tooling (pre-commit, pytest)"
python3 -m pip install pre-commit pytest

echo "==> Installing pre-commit git hooks"
pre-commit install || true

echo "==> Development environment ready"
