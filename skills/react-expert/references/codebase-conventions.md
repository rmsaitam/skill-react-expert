# Codebase conventions

The detected stack defines what is legal; the codebase defines what is idiomatic. Read the following before designing a change:

- `CONTRIBUTING.md`, `CODING_STANDARDS.md`, `SECURITY.md` and `ARCHITECTURE.md`.
- ADRs under `docs/adr/`.
- ESLint, Prettier, Stylelint and TypeScript configuration, including `strict` and path aliases.
- `package.json` scripts, framework configuration and the closest existing test setup.
- The closest existing component, hook, page, store, query and test files for the area being changed.
- Recent approved commits touching the same folders.

## Capture these facts

| Topic | Question to answer |
| --- | --- |
| Folder layout | Where do components, hooks, pages, routes, stores, models and tests live? |
| Naming | Are files kebab-case or PascalCase? Which suffixes are used for components, hooks and tests? |
| Exports | Are components exported as `named` or `default`? Are barrels used? |
| Rendering | Is the app CSR, SSR or hybrid? Where are client and server boundaries declared? |
| State management | Are values held in `useState`, Context API, Zustand, Redux Toolkit, Jotai or another store? |
| Data fetching | Is data read with TanStack Query, SWR, framework loaders, Server Actions or plain effects? |
| Styling | Is the project using Tailwind CSS, CSS Modules, Styled Components, Shadcn/UI, Radix or plain CSS? |
| Error handling | Are errors mapped at the boundary, in a query client, in a route or in the component? |
| Tests | Which runner, naming convention, render helpers and mocking style are used? |
| Accessibility | Which semantic elements, labels and ARIA conventions are already applied? |

## Rules

- Copy the local style before introducing anything new.
- Keep the established folder layout, naming and export style; do not reformat unrelated code.
- Do not introduce a state library, UI library, CSS framework or test runner unless the project already uses it or the user explicitly requests it.
- If the project exposes API shapes directly, do not silently add a mapper layer; mention it as a design option instead.
- If no local example exists, prefer the smallest official React pattern compatible with the detected version and record the assumption in the artifact.
