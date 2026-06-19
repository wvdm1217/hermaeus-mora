---
name: create-spec
description: "Use this skill to create a new specification document for spec-driven development. Use when: generating a spec, planning a new feature, writing a technical specification, or starting a new project requirement."
---

# Create Spec Workflow

This skill guides the creation of high-quality, comprehensive specification documents for spec-driven development. Specs act as a blueprint for implementation, testing, observability, and architecture, reflecting the mindset of a Principal Software Engineer.

## Process

1. **Gather Initial Information**
   - If the user hasn't provided them, ask for:
     - The title of the feature/spec.
     - The author's name (the human, not the AI).
     - The current project version number.
     - A brief description of the feature.

2. **Load Template**
   - Read the template from `docs/specs/_template.md`.
   - Read the architecture from `docs/specs/ARCHITECTURE.md`.
   - Never overwrite the `_template.md` file itself.

3. **Draft the Specification**
   - Adopt the persona of a Principal Software Engineer. Ensure you consider:
     - Edge cases and failure modes.
     - Comprehensive testing strategies (unit, integration, regression).
     - Observability (logging, metrics, alerting).
     - Clean architectural design and maintainability.
   - Fill out all sections of the template based on the provided details. Be thoroughly analytical.
   - Set the `date` to the current date.

4. **Determine Filename**
   - Format the filename using a datetime stamp: `YYYY-MM-DD_HH-MM-SS-<normalized-title>.md`.
   - (e.g., `2024-03-14_15-30-00-user-auth-flow.md`).
   - The directory must be `docs/specs/`.

5. **Create the Spec File**
   - Write the generated specification to the new file in `docs/specs/`.

6. **Review and Iterate**
   - Present the created spec to the user and ask if any sections (like Architecture, Edge Cases, or Observability) need deeper elaboration or adjustments.
