# React Expert

[![skills.sh](https://skills.sh/b/rmsaitam/skill-react-expert)](https://skills.sh/rmsaitam/skill-react-expert)

A version-aware React implementation skill for coding agents. Before suggesting any dependency, API or configuration, the skill inspects `package.json`, `tsconfig.json` and the framework descriptors to identify the exact React version, TypeScript version, framework, rendering mode, build tool and installed packages. If no manifest is available, it stops and asks for the manifest or the versions instead of guessing.

The skill follows the conventions already present in the codebase and the official react.dev guidance. It gates React 19 APIs such as `useActionState`, `use()` and `useOptimistic`, respects Server Actions only when the framework supports them, preserves the existing state, data fetching and styling choices, writes semantic accessible components, and adds unit tests under an 80% coverage gate. TypeScript projects keep `strict` settings unchanged and avoid `any`.

## Supported agents

| Agent | Manifest |
| --- | --- |
| Claude Code | `.claude-plugin/plugin.json` |
| Codex | `.codex-plugin/plugin.json` |
| Cursor | `.cursor-plugin/plugin.json` |
| GitHub Copilot CLI | `.github/plugin/marketplace.json` |
| Antigravity | `plugin.json` |
| skills.sh / generic Agent Skills | `skills/react-expert/SKILL.md` |

## Install

```bash
npx skills add rmsaitam/skill-react-expert
npx skills add rmsaitam/skill-react-expert -g -y
npx skills add rmsaitam/skill-react-expert --list
```

Claude Code:

```text
/plugin marketplace add rmsaitam/skill-react-expert
/plugin install react-expert
```

Manual install for generic Agent Skills:

```bash
mkdir -p ~/.agents/skills
cp -R skills/react-expert ~/.agents/skills/react-expert
python3 scripts/validate_plugin.py .
```

## What it does

1. Runs `detect_stack.py` to produce a normalized stack report: React version, TypeScript version, framework, rendering mode, build tool, test runner, strict flag, React Compiler and installed state or styling libraries.
2. Loads repository standards and mirrors existing folder, component, hook, state, styling and test patterns.
3. Implements the change with version-safe APIs, minimal derived state, surgical effects, stable keys, accessible markup and the project's state and data fetching approach.
4. Adds unit tests with the configured Jest or Vitest runner and checks coverage against the 80% gate.
5. Writes and validates a traceable `REACT-EXPERT-IMPL.md` artifact with `validate_report.py`.

The final answer always follows this format: **Brief Analysis**, **Clean and Complete Code**, **Configuration**.

## Artifact markers

```markdown
<!-- react-expert:artifact type=implementation version=1 -->
<!-- react-expert:section id=analysis -->
<!-- react-expert:section id=stack -->
<!-- react-expert:section id=design -->
<!-- react-expert:section id=implementation -->
<!-- react-expert:section id=tests -->
<!-- react-expert:section id=validation -->
<!-- react-expert:section id=configurations -->
<!-- react-expert:section id=evidence -->
<!-- react-expert:section id=assumptions -->
<!-- react-expert:section id=traceability -->
<!-- react-expert:stack react=19.0.0 typescript=5.7.2 build=pnpm framework=next rendering=ssr test-runner=vitest strict=true -->
<!-- react-expert:coverage value=88 gate=80 tool=vitest -->
<!-- react-expert:change id=CHG-001 status=implemented -->
<!-- react-expert:test id=T-001 framework=vitest context=unit -->
```

## Development

```bash
make test        # run the test suite
make coverage    # run tests with an 80% coverage gate
make validate    # validate the plugin structure
make check       # coverage plus plugin validation
```

The executable test suite of this plugin uses pytest and covers `detect_stack.py`, `validate_report.py` and `validate_plugin.py`. The generated React code contract requires unit tests with the configured runner and 80% coverage in the target codebase.

## Official documentation

The `references/official-docs.md` file maps each rule to the official react.dev guides for components, hooks, effects, state, forms, rendering, testing and compiler support.

## License

MIT
