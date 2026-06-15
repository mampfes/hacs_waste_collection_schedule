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

# yamlfmt is provided by the jumanjihouse pre-commit hook (a bundled Ruby
# script, not a standalone package). Install a thin `yamlfmt` wrapper on PATH
# that drives that exact hook, so terminal runs match CI behaviour.
echo "==> Installing yamlfmt wrapper"
mkdir -p "$HOME/.local/bin"
cat >"$HOME/.local/bin/yamlfmt" <<'WRAPPER'
#!/usr/bin/env bash
# Run the project's yamlfmt pre-commit hook directly.
# Usage: yamlfmt [files...]   (no args -> all files)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
if [ "$#" -eq 0 ]; then
	exec pre-commit run yamlfmt --all-files
else
	exec pre-commit run yamlfmt --files "$@"
fi
WRAPPER
chmod +x "$HOME/.local/bin/yamlfmt"

# Install the pre-commit git hooks, unless the container manages git hooks via
# core.hooksPath (pre-commit refuses to install in that case).
echo "==> Installing pre-commit git hooks"
if [ -n "$(git config --get core.hooksPath || true)" ]; then
	echo "    Skipped: core.hooksPath is set by the container."
	echo "    Run checks manually with 'pre-commit run --all-files'."
else
	pre-commit install || true
fi

echo "==> Development environment ready"
