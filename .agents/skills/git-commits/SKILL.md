---
name: git-commits
description: Writing of high quality commit messages.
---

# Git Commits Skill

Use this skill whenever the user asks to generate, review, or format a git commit message.

## Rules and Guidelines

You must strictly follow the **Conventional Commits** specification to ensure a consistent, readable, and machine-parsable commit history.

### Atomic Commits (What to Commit)
Before writing the message, ensure the commit itself represents a high-quality, logical unit of work:
- **Single Responsibility**: A commit should contain exactly one logical change. Do not bundle unrelated changes (e.g., adding a feature, fixing an unrelated bug, and formatting code) into a single "kitchen sink" commit.
- **Independent**: Each commit should ideally build successfully and pass tests on its own. This ensures that history remains clean and tools like `git bisect` and `git revert` are reliable.
- **Small and Focused**: Break large features down into smaller, easily reviewable steps. Keep commits as small as possible while still making logical sense.
- **Separate Refactoring**: Keep structural or formatting changes (e.g., `style` or `refactor`) in separate commits from behavioral changes (e.g., `feat` or `fix`) to make code reviews much easier.

### Format
Every commit message must follow this exact structure:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 1. Type
Must be one of the following:
- `feat`: A new feature for the user, not a new feature for build script
- `fix`: A bug fix for the user, not a fix to a build script
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies (e.g., uv, pip, npm)
- `ci`: Changes to our CI configuration files and scripts (e.g., GitHub Actions)
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

### 2. Scope (Optional)
A scope may be provided to a commit's type, to provide additional contextual information and is contained within parenthesis, e.g., `feat(parser): add ability to parse arrays`.
- It should be a short noun reflecting the section of the codebase changed.

### 3. Description
A short summary of the code changes.
- Use the **imperative, present tense**: "change" not "changed" nor "changes"
- **Do not** capitalize the first letter
- **Do not** place a period `.` at the end

### 4. Body (Optional)
The body should include the motivation for the change and contrast this with previous behavior.
- Use the imperative, present tense.
- Wrap lines at 72 characters.
- Separate from the description by a single blank line.

### 5. Footer (Optional)
The footer should contain any information about **Breaking Changes** and is also the place to reference GitHub issues that this commit **Closes**.
- **Breaking Changes** should start with the word `BREAKING CHANGE:` followed by a space or two newlines. The rest of the commit message is then used to describe the breaking change.
- Referencing issues should follow conventions like `Closes #123` or `Fixes #456`.

## Examples

**Feature commit with scope:**
```
feat(api): add user authentication endpoint

Implement JWT-based authentication for the main API routes.
This allows users to securely log in and obtain a token for
subsequent requests.
```

**Bug fix with issue reference:**
```
fix(ui): resolve overlap in navigation menu

Adjust CSS flex properties on the header component to prevent
the navigation items from overflowing into the logo space on
smaller screens.

Closes #42
```

**Refactor with breaking change:**
```
refactor: redesign configuration loading

BREAKING CHANGE: The `load_config` function no longer accepts
a raw dictionary. It now requires a `ConfigOptions` object to
ensure type safety and proper validation.
```

**Chore commit:**
```
chore: update dependency versions in pyproject.toml
```