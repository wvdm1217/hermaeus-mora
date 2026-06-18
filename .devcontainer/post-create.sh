#!/usr/bin/env bash
set -euo pipefail

# Ensure we run from the repository root.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Install uv only when it is not already available.
if ! command -v uv >/dev/null 2>&1; then
	curl -LsSf https://astral.sh/uv/install.sh | sh
	export PATH="$HOME/.local/bin:$PATH"
fi

# Install project dependencies including the dev group.
uv sync --dev

# Install pre-commit hooks for this repository.
uv run pre-commit install

# Install speckit
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.11.2

# Ensure zsh auto-activates the repository virtual environment.
ZSHRC="$HOME/.zshrc"
AUTO_VENV_MARKER="# >>> hermaeus-mora auto-venv >>>"

if [[ ! -f "$ZSHRC" ]]; then
	touch "$ZSHRC"
fi

if ! grep -Fq "$AUTO_VENV_MARKER" "$ZSHRC"; then
	{
		echo ""
		echo "$AUTO_VENV_MARKER"
		echo "if [[ \"\$PWD\" == \"$REPO_ROOT\"* ]] && [[ -f \"$REPO_ROOT/.venv/bin/activate\" ]] && [[ -z \"\${VIRTUAL_ENV:-}\" ]]; then"
		echo "  source \"$REPO_ROOT/.venv/bin/activate\""
		echo "fi"
		echo "# <<< hermaeus-mora auto-venv <<<"
	} >>"$ZSHRC"
fi
