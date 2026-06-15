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

# Standalone linters/formatters so they can be run directly from the terminal
# (e.g. `ruff check .`, `bandit -c tests/bandit.yaml -r .`, `mypy ...`).
# Versions are pinned to match the hooks in .pre-commit-config.yaml so local
# runs agree with CI.
echo "==> Installing standalone linters (ruff, bandit, mypy)"
python3 -m pip install \
	"ruff==0.15.17" \
	"bandit==1.9.4" \
	"mypy==2.1.0"

# yamlfmt (jumanjihouse hook) is the Ruby gem of the same name. Install it if a
# Ruby toolchain is available; don't fail the whole setup if it isn't.
echo "==> Installing yamlfmt (Ruby gem)"
if command -v gem >/dev/null 2>&1; then
	gem install yamlfmt || echo "WARN: 'gem install yamlfmt' failed; use 'pre-commit run yamlfmt' instead"
else
	echo "WARN: Ruby/gem not found; run yaml formatting via 'pre-commit run yamlfmt --all-files'"
fi

echo "==> Installing pre-commit git hooks"
pre-commit install || true

echo "==> Development environment ready"
