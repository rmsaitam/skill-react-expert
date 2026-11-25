# State and data fetching

Follow the state and data fetching pattern already installed in the codebase. `package.json` and the detector report are the authority; do not pick a library from memory.

## Existing patterns

| Detected library | Required behavior |
| --- | --- |
| TanStack Query | Keep query keys, cache invalidation and query client boundaries consistent with existing files |
| Zustand | Keep stores small, use selectors, and avoid storing derivable values |
| Redux Toolkit | Use slices, typed hooks and existing serializability conventions |
| SWR | Reuse the configured fetcher, revalidation and error conventions |
| Context API | Split value and setter contexts when re-render cost matters and memoize the provider value with a proven need |
| Framework loaders or Server Actions | Respect the detected Next.js or Remix data flow and server boundaries |

## State ownership

- Keep server data in the data fetching layer, not duplicated in component state.
- Keep UI-only state as close as possible to the component that owns it.
- Lift state only when two siblings truly need the same value; otherwise use composition.
- Keep updates immutable and typed; use `unknown` with narrowing at external boundaries in TypeScript.
- Never store tokens, credentials or personal data in component state or artifacts.

## Asynchronous UI states

Every asynchronous flow must account for:

- **loading**: an accessible pending indicator that does not hide the whole page without reason.
- **empty**: an explicit empty state with the next useful action when the collection has no items.
- **error**: a recoverable message using the project's error boundary, toast or inline pattern.

## Fetching rules

- Cancel or ignore stale async work with the framework's supported mechanism when the component unmounts.
- Do not use an effect solely to fetch data when the project already provides a query loader, route loader or action.
- If an effect must call an API, include cleanup and avoid synchronous state writes that duplicate derived data.
- Keep DTO mapping in the layer already used by the project; do not introduce a mapper layer silently.

## Verification

- Test success, validation and error branches of the changed flow.
- Assert loading and empty states when the UI exposes them.
- Mock at the same boundary used by existing tests.
- Keep coverage at or above 80% without lowering the gate.
