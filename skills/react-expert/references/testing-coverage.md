# Testing and coverage

Keep the configured runner. The detector distinguishes Jest and Vitest; do not convert one to the other without an explicit request.

## Runner setup

- **Jest**: reuse existing `jest.config.*`, transforms and setup files. Add jsdom environment and Testing Library helpers only when the project already uses them or after approval.
- **Vitest**: reuse existing `vitest.config.*`, environment and setup files. Keep coverage provider configuration aligned with the installed packages.
- **Component rendering**: use the project's existing Testing Library helpers or renderer. Do not introduce a new renderer into an established suite.
- **Mocking**: mock at the same boundary as neighboring tests: network client, query client, store or framework action.

## What to test

For every behavioral change, cover:

1. The success path with realistic props or state.
2. Validation or boundary input when the component accepts user data.
3. The error path using the project's error channel.
4. The loading state when the data flow is asynchronous.
5. The empty state when a collection or result can be empty.
6. Accessibility contract: accessible name, label association, keyboard action or status announcement when relevant.

## Test quality

- Query by accessible role or label before using test IDs; follow local conventions when test IDs are standard.
- Assert user-visible behavior instead of implementation details such as internal state shape.
- Keep tests isolated: reset mocks, query caches and stores between cases.
- Avoid snapshots for behavior that can be asserted explicitly.
- Do not add a suppression such as `@ts-ignore` or `eslint-disable` without a recorded false positive and approval in the artifact.

## Coverage gate

- Enforce at least 80% coverage with the runner configured in the project.
- Report the exact command and measured result in the artifact.
- If coverage is below 80%, add tests for uncovered branches; never lower the threshold or exclude the changed files.
- Run the type check and build commands when available and record their exit status.
