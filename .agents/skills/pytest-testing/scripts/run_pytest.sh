#!/usr/bin/env bash

show_help() {
    cat << EOF
Usage: scripts/run_pytest.sh [OPTIONS] [TARGETS...]

Run pytest with strict configurations for agentic use.

Options:
  --fail-fast    Exit instantly on first error or failed test (-x).
  --quiet        Decrease verbosity (-q).
  --help         Show this message and exit.

Examples:
  bash scripts/run_pytest.sh tests/
  bash scripts/run_pytest.sh --fail-fast --quiet tests/test_api.py
EOF
}

ARGS=()
FAIL_FAST=false
QUIET=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --help|-h) show_help; exit 0 ;;
        --fail-fast) FAIL_FAST=true; shift ;;
        --quiet) QUIET=true; shift ;;
        *) ARGS+=("$1"); shift ;;
    esac
done

if [ ${#ARGS[@]} -eq 0 ]; then
    ARGS=(".")
fi

CMD=("uv" "run" "pytest" "--strict-markers" "--tb=short")

if [ "$FAIL_FAST" = true ]; then
    CMD+=("-x")
fi

if [ "$QUIET" = true ]; then
    CMD+=("-q")
else
    CMD+=("-v")
fi

CMD+=("${ARGS[@]}")

# Separate diagnostics (stderr) from test output (stdout)
echo "Diagnostics: Executing ${CMD[*]}" >&2

# Check if uv exists
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' command not found. Ensure uv is installed." >&2
    exit 1
fi

"${CMD[@]}"
