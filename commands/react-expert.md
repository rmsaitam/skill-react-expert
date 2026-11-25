---
description: Implement React changes using detected versions and framework, react.dev guidance, codebase conventions, accessible UI and unit tests with an 80% coverage gate.
argument-hint: "[--project-root PATH] [--scope DESCRIPTION] [--output PATH]"
---

# React Expert

Invoke the `react-expert` skill. The detector runs first; no dependency, API or code suggestion is allowed before the stack gate is complete.

## Instructions

- Run `python3 skills/react-expert/scripts/detect_stack.py <project-root> --output stack.json` from the plugin repository root as the first action. If `package.json` is missing or the React version cannot be parsed, stop and ask for the descriptor or the exact React and TypeScript versions.
- Use the detected React major and framework to gate React 18 APIs, React 19 APIs such as `useActionState`, `use()`, `useOptimistic` and Server Actions, and the React Compiler. Do not mix APIs from different majors.
- Mirror the existing folder layout, export style, naming, state management, data fetching, styling and test conventions. Never introduce a new library without an explicit need.
- Keep components pure, derive state during render, use `useEffect` only for external synchronization, prefer composition, extract custom hooks and give dynamic lists stable keys.
- Preserve the detected CSR or SSR model and follow react.dev for the detected version. Use Server Actions only when React 19 and the framework support them natively.
- Keep semantic HTML and accessibility, and cover loading, empty and error states in asynchronous flows.
- Keep the configured Jest or Vitest runner and enforce at least 80% coverage; record the exact commands and measured result.
- Write only `REACT-EXPERT-IMPL.md` at the repository root unless the user supplies another path.
- Before finishing, validate the artifact:

  ```bash
  python3 skills/react-expert/scripts/validate_report.py REACT-EXPERT-IMPL.md
  ```

- Report the artifact path, detected React and TypeScript versions, framework, main changes, test commands, measured coverage and remaining risks.
