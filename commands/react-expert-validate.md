---
description: Validate a REACT-EXPERT-IMPL.md artifact against the implementation report contract and its 80% coverage gate.
argument-hint: "[path/to/REACT-EXPERT-IMPL.md]"
---

# Validate React Expert Report

Validate an existing `REACT-EXPERT-IMPL.md` produced by the `react-expert` skill.

## Instructions

- Default to `REACT-EXPERT-IMPL.md` at the repository root when no path is provided.
- Run:

  ```bash
  python3 skills/react-expert/scripts/validate_report.py REACT-EXPERT-IMPL.md
  ```

- From an installed skill directory, adjust the script path to match the local layout.
- Use `--strict` to treat warnings as failures, `--json` for machine-readable output and `--min-coverage N` to change the default 80% gate.
- Check that the detected React version, framework, rendering mode and configured Jest or Vitest runner match the report.
- Do not modify the report unless the user explicitly asks for fixes. If fixes are requested, preserve the artifact markers and re-run the validator.
