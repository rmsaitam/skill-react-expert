# Validation checklist

Use this checklist when the validator cannot be executed. Every box must be checked before handoff.

## 1. Artifact contract

- [ ] The `<!-- react-expert:artifact type=implementation version=1 -->` marker appears once.
- [ ] All ten section markers appear once: analysis, stack, design, implementation, tests, validation, configurations, evidence, assumptions, traceability.
- [ ] The stack marker uses the detected React version, TypeScript version, build tool, framework, rendering mode, test runner and strict flag.
- [ ] The coverage marker uses `gate=80` and the detected runner as `tool` with the measured `value`.
- [ ] `CHG-NNN`, `T-NNN`, `CFG-NNN` and `EV-NNN` IDs are unique and stable; every change links to a test and evidence row.
- [ ] No unfinished marker, blank section, dummy text or approval verdict remains.

## 2. Summary and stack

- [ ] All 14 metadata fields are present: Status, Date, Reviewer, Artifact, React Version, TypeScript Version, Build Tool, Framework, Rendering Mode, Test Runner, Changes Applied, Tests Run, Coverage and Coverage Tool.
- [ ] Versions and modes match `stack.json`, `package.json`, `tsconfig.json` and the framework descriptors.
- [ ] Changes Applied equals the number of `CHG-NNN` entries.
- [ ] React 17 or earlier constraints are recorded without proposing a migration.

## 3. Implementation

- [ ] Components and hooks are pure during render and props, state and external variables are not mutated.
- [ ] Derived values are computed in render; `useMemo` is used only with a proven need.
- [ ] `useEffect` is limited to external synchronization with cleanup where needed.
- [ ] Composition, custom hooks and stable keys are used where applicable.
- [ ] Version-gated APIs are justified by the detected React major and framework.
- [ ] The existing state, data fetching, styling and UI conventions are preserved.
- [ ] HTML is semantic, accessibility is preserved and loading, empty and error states are handled.
- [ ] No credentials, tokens or fixed environment values are hardcoded.

## 4. Tests and coverage

- [ ] Jest or Vitest matches the detected runner and the existing configuration.
- [ ] Test entries use the detected runner and `context=unit`.
- [ ] Success, validation, loading, empty and error paths are covered where applicable.
- [ ] Runner coverage thresholds are at least 80% and the measured value is recorded.
- [ ] Every command in the report was actually executed.

## 5. Configurations and evidence

- [ ] New configuration keys are shown exactly with file and key, or the section says `No changes.`
- [ ] Each evidence row has a command and an observed result.
- [ ] Traceability links every change to at least one test and one evidence row.
- [ ] Sensitive values are redacted as `[REDACTED]`; only keys are reported.

## 6. Manual commands

```bash
python3 scripts/detect_stack.py . --output stack.json
pnpm test -- --coverage
python3 scripts/validate_report.py REACT-EXPERT-IMPL.md
```

The detector and report validator must exit with status 0. When the validator cannot run, state that the manual checklist was applied instead.
