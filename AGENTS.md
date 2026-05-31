# Agent Instructions & Project Guidelines

You are an expert AI Python developer operating within the `hermaeus-mora` repository. Follow these guidelines rigorously to ensure code quality and project consistency.

## 1. Project Structure & Architecture
- **`src/hermaeus_mora/`**: Main application source code.
- **`tests/`**: Unit and integration tests.
- **`docs/`**: Project documentation.
- **`data/`**: Static data assets and configurations.
- **`pyproject.toml`**: Source of truth for all tooling configurations (`uv`, `ruff`, `pytest`).

## 2. Environment & Dependencies
- **Package Manager**: Use `uv` exclusively for dependency management and environment isolation.
- **Install Environment**: `uv sync`
- **Add Dependencies**: `uv add <package>` (Use `uv add --dev <package>` for development tools).
- **Run Scripts**: Always execute scripts and CLI tools within the `uv` environment using `uv run <command>`.
- **Python Target**: `>=3.14`.

## 3. Code Style & Quality
- **Linter/Formatter**: The project uses **Ruff**. It enforces a max line length of 88, double quotes, and strict rules including Isort (`I`), Bugbear (`B`), and Pyupgrade (`UP`).
- **Type Hinting**: All public functions, classes, and methods **must** have strict Python type hints.
- **Pre-commit**: Formatting and lint checks are managed via pre-commit. To run checks: `uv run pre-commit run --all-files`.

## 4. Testing Protocols
- **Framework**: `pytest` combined with `pytest-cov`. Tests must target the `hermaeus_mora` module.
- **Execution**: **Always** use the `pytest-testing` skill and execute the bundled script rather than running pytest directly:
  `bash .agents/skills/pytest-testing/scripts/run_pytest.sh <target>`
- **Expectations**: Write rigorous tests handling edge cases, and utilize pytest fixtures properly.

## 5. Agent Workflow & Execution Rules
- **Context Gathering**: Always search the codebase (`grep_search`, `file_search`) to align with existing patterns before generating new code.
- **Small, Iterative Steps**: When writing complex features, break them down. Verify intermediate steps using linters or tests before moving on.
- **Commit Messages**: When asked to commit, use the `git-commits` skill for generating high-quality, standardized commit messages.
