---
name: quality-assurance
description: 'Perform quality assurance and exploratory testing by running scenarios against the CLI in an isolated temporary data directory. Use when: testing the application, finding bugs, verifying CLI commands, checking for unintended consequences, creating QA reports.'
argument-hint: 'Optional focus areas or specific CLI commands to test'
user-invocable: true
---

# Quality Assurance Workflow

## When to Use
- Validating the application after implementing new features.
- Running exploratory testing to find bugs or unintended consequences in the CLI.
- Verifying the application's behavior against specifications.
- Generating a comprehensive QA report with categorized bugs and issues.

## Important Constraints
- **Never use the user's existing `data/` directory.** You must use an isolated temporary directory for all testing.
- **Use the `tmp/` directory** for all temporary artifacts. Place your mock scripts (e.g., a fake `$EDITOR` script) and the temporary data directory under `tmp/` (which is gitignored) to keep the workspace clean.
- Rely on the CLI to generate data, rather than manually creating files, to properly test the tool's intended workflows.
- Use `uv run hm <command>` to execute the CLI.
- **Use here-strings (`<<< "input"`)** to efficiently bypass and test interactive CLI prompts (like `typer.prompt`) without hanging the terminal.

## Procedure

1. **Setup Isolated Environment:**
   - Run `source .agents/skills/quality-assurance/scripts/setup_env.sh` in the terminal to set `HM_DATA_DIR` and create a temporary data directory inside `tmp/`.

2. **Understand the Architecture and Specs:**
   - Use `uv run hm --help` and `uv run hm <command> --help` to discover available commands, options, and expected inputs directly from the CLI.
   - Read the `README.md` and `docs/ARCHITECTURE.md` to understand the system's design.
   - Review the implemented specs in `docs/specs/` to understand the expected behavior of the features being tested.
   - Briefly inspect the source code in `src/hermaeus_mora/` to see the actual implementation logic.

3. **Design and Execute Test Scenarios:**
   - Design scenarios that test standard usage, edge cases, and potential misuses of the CLI commands.
   - Execute the commands in the terminal.
   - Pay special attention to commands that might have unintended consequences, state mutations, or error handling issues.
   - Observe the output and side effects in the isolated data directory.

4. **Document Findings:**
   - Take note of any deviations from the specifications, crashes, unhandled errors, or UX issues.
   - Categorize each finding with a severity level (e.g., Critical, High, Medium, Low).

5. **Cleanup Isolated Environment:**
   - Run `source .agents/skills/quality-assurance/scripts/cleanup_env.sh` in the terminal to remove the temporary data directory and unset the environment variable.

6. **Generate QA Report:**
   - Produce a detailed report containing:
     - **Scenarios Tested:** Brief description of what was tested.
     - **Findings:** List of identified issues, bugs, and unintended consequences.
     - **Severity Levels:** Level assigned to each finding.
     - **Recommendations:** Suggestions for refinement or fixes.

## References
- [Setup Script](./scripts/setup_env.sh)
- [Cleanup Script](./scripts/cleanup_env.sh)
