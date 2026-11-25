# Stack detection

This gate is mandatory and blocking. Run it before reading source code for the purpose of proposing or applying a change.

```bash
python3 scripts/detect_stack.py <project-root> --output stack.json
```

The detector output is authoritative. Convert it into the artifact stack marker without adding values from memory.

## What the detector reads

| Source | Extracted values |
| --- | --- |
| `package.json` | `react`, `react-dom`, `typescript`, Node-oriented build tools, framework packages, test runners, React Compiler and installed state or styling libraries |
| `tsconfig.json` | `compilerOptions.strict`, `baseUrl` and path aliases; JSON comments are tolerated |
| `vite.config.*`, `next.config.*`, `remix.config.*`, `babel.config.*` and `.babelrc` | Framework and React Compiler indicators, plus configuration keys only |
| `components.json` | Presence of a Shadcn/UI setup |
| `turbo.json` or `nx.json` | Monorepo build tool |
| `packageManager` field | npm, yarn, pnpm or bun package manager |
| Source files | CSS Modules usage and framework directory evidence |

`package.json` is the preferred and required descriptor. `tsconfig.json` is optional; a missing strict flag is recorded as `strict=false` and must not be silently changed.

A detected dependency name alone does not enable an API. Cross-check the React major version, the framework and the official guide for that version before using a version-gated feature.

## Emitted JSON fields

- `projectRoot`, `descriptor` and `buildTool`: the detected root, `package.json` and one of `npm`, `yarn`, `pnpm`, `bun`, `turbo` or `nx`.
- `react.version` and `react.major`: declared React version and major line.
- `reactDom.version`: declared `react-dom` version when available.
- `typescript.version`: declared TypeScript version when available.
- `framework`: `next`, `remix`, `vite`, `cra`, `expo`, `mixed` or `unknown`.
- `rendering`: `ssr`, `csr`, `hybrid`, `mixed` or `unknown`.
- `testRunner`: `jest`, `vitest`, `mixed` or `unknown`.
- `strict`: boolean from `compilerOptions.strict`.
- `capabilities`: booleans for React 19 APIs, Server Actions, React Compiler, TypeScript, Testing Library and detected libraries.
- `stateLibraries` and `stylingLibraries`: sorted names inferred from installed packages and local files.
- `configKeys`: sorted, unique configuration keys without values.
- `warnings` and `blockers`: objects with `code`, `message` and `source`.

These fields map directly to the artifact marker: `react`, `typescript`, `build`, `framework`, `rendering`, `test-runner` and `strict`.

## Stop conditions

1. No `package.json`: ask the user for the descriptor or the exact React and TypeScript versions. Do not continue in the same turn.
2. Missing or unparseable React version: report the exact file and field that is missing. Do not guess.
3. Conflicting React versions across dependencies: ask which source is authoritative before proposing code.
4. Missing strict flag: ask before applying strictness changes; never silently flip `strict`.
5. React 17 or earlier: record the legacy constraint; do not propose an upgrade unless the user asks.

## Version and API gate

| React major | Allowed guidance |
| --- | --- |
| 17 or earlier | Preserve legacy patterns; never use React 18 or React 19 APIs |
| 18 | Use React 18 APIs only; block `useActionState`, `use()` and `useOptimistic` |
| 19 or newer | Gate `useActionState`, `use()` and `useOptimistic` by official docs; Server Actions also need framework support |

## Exit codes

`0` on success, `1` in `--strict` mode when warnings exist, `2` for a configuration error or blockers, and `3` for a parse error. Use `--json` to print the report to stdout and `--output PATH` to write it to a file.

## Security boundary

The detector reads configuration keys only. It never emits values that look like passwords, tokens, API keys or URLs with embedded credentials. Feed its JSON into the report; never paste raw configuration files into the artifact. Redact accidental values as `[REDACTED]`.
