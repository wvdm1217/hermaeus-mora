---
name: review-branch
description: 'Review a branch or pull request to check if it is ready to merge into main. Use when: asked to review code, check branch readiness, perform code review, find bugs, or assess code maintainability.'
---

# Branch Review & Readiness Check

## When to Use
- You are asked to review a branch or pull request.
- The user wants to know if their changes are ready to merge into `main`.
- Checking for bugs, architectural issues, and clean code practices before merging.

## Procedure

Follow these steps to conduct a thorough code review:

### 1. Gather Context & Changes
- Determine the changes by comparing the current branch against `main` (e.g., using terminal `git diff main...HEAD` or GitHub PR tools if a PR exists).
- Review any newly added or modified files using the read tools or grep.
- Read `docs/ARCHITECTURE.md` and `AGENTS.md` if you need to verify structural alignment.

### 2. Run Quality Checks
- Run linters and formatters: `uv run pre-commit run --all-files` (or check for existing pre-commit issues).
- Run tests: execute `.agents/skills/pytest-testing/scripts/run_pytest.sh tests/` to ensure nothing is broken.

### 3. Deep Code Review
Critically analyze the code changes. Look for issues and categorize them:
- **Critical Bugs**: Issues that will crash the application, cause data loss, or create severe security vulnerabilities.
- **High Bugs**: Major feature breakages, incorrect logic for core paths, or significant performance degradation.
- **Medium Bugs**: Edge case failures, improper error handling, or minor functional bugs.
- **Low Bugs**: Typos, minor UI/UX issues, or non-disruptive bugs.
- **Maintainability & Clean Code**:
  - Adherence to Python type hinting (`>=3.14`).
  - Readability, DRY violations, SOLID principles.
  - Test coverage for new features.

### 4. Provide the Review Report
Generate a clear markdown report for the user containing:
- **Summary**: A brief overview of what changed and the overall quality.
- **Automated Checks**: Status of linters and tests.
- **Issues Found**: Grouped by severity (Critical, High, Medium, Low) and Maintainability/Clean Code. For each issue, provide:
  - File name and line number (if applicable).
  - Description of the issue.
  - **Suggested Fix**: Provide code snippets or actionable advice to resolve it.
- **Final Verdict**: State clearly whether the branch is **Ready to Merge**, **Needs Minor Fixes**, or **Needs Major Rework**.
