# Hooks, purity and state

These rules apply to every detected React version. Version-specific APIs are handled by `references/version-detection.md`.

## Purity and immutability

- Components and hooks must be pure functions during render: same inputs produce the same output and no side effects escape the render.
- Never mutate props, state or module-level variables during render.
- Update objects and arrays by creating new references: spread, `map`, `filter`, `concat` or an immutable helper already used by the project.
- Do not write to the DOM during render; use refs or effects only when synchronization is required.

## Minimal and derived state

- Do not store a value in `useState` when it can be computed from props or existing state.
- Compute derived values directly in the component body.
- Use `useMemo` only when a real bottleneck is measured or when a stable reference is required by a dependency list.
- Prefer a key-based remount or an explicit reset action over effects that synchronize one state variable to another.

## Surgical `useEffect`

An effect is an escape hatch for external systems:

- DOM APIs, subscriptions, timers and third-party clients belong in effects.
- Return cleanup when the subscription or timer can outlive the render.
- Do not transform data for rendering in an effect; derive it instead.
- Do not react to a user event in an effect; use `onClick`, `onChange`, form actions or the existing event pattern.
- Do not set synchronous state in an effect just to initialize derived data.

## Composition

- Prefer composition via `children`, slots or component props over boolean-prop matrices.
- Pass data and callbacks explicitly; keep shared layout in wrapper components.
- Avoid inheritance and deeply nested configuration objects that hide responsibilities.

## Rules of hooks

- Call hooks only at the top level of components or other hooks.
- Never call hooks inside conditionals, loops or nested functions.
- Extract reusable logic into custom hooks named with `use`, such as `useDebouncedValue` or `useOrderQuery`.
- Keep effect dependencies complete and minimal; do not suppress linter rules without a recorded justification.

## Lists and keys

- Give every element in a dynamic list a stable and unique key based on domain data, usually an ID.
- Do not use the array index as a key when items can be reordered, inserted or removed.
- Use a stable compound key when no single ID exists and record the assumption.

## Conscious optimization

- Avoid premature `useMemo`, `useCallback` and `React.memo`.
- Memoize only with a proven need: expensive computation, reference-sensitive dependency or a measured heavy child.
- When React Compiler is already configured, prefer plain functions and let the compiler handle memoization unless a measurement proves otherwise.
- Never enable React Compiler as part of an unrelated change.
