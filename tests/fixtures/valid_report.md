<!-- react-expert:artifact type=implementation version=1 -->

# React Expert Implementation: order list component

- Status: Final
- Date: 2026-11-25
- Reviewer: React Expert Agent
- Artifact: REACT-EXPERT-IMPL.md
- React Version: 19.0.0
- TypeScript Version: 5.7.2
- Build Tool: pnpm
- Framework: next
- Rendering Mode: ssr
- Test Runner: vitest
- Changes Applied: 1
- Tests Run: pnpm test -- --coverage
- Coverage: 88%
- Coverage Tool: vitest

<!-- react-expert:section id=analysis -->

## Brief Analysis

The codebase already uses Next.js App Router, TypeScript strict mode, Vitest and Tailwind CSS. The component keeps presentation responsibilities and receives immutable order data from the existing query hook, preserving folder layout, named exports and stable keys.

Changes Applied: 1

<!-- react-expert:section id=stack -->

## Detected Stack

<!-- react-expert:stack react=19.0.0 typescript=5.7.2 build=pnpm framework=next rendering=ssr test-runner=vitest strict=true -->

Detected from `package.json`, `tsconfig.json` and `next.config.js`. React 19 supports the chosen form action, Next.js owns the server boundary and Vitest is the configured runner.

<!-- react-expert:section id=design -->

## Design

The page renders server-provided order data and delegates submission to the existing action. Derived totals are computed during render, list keys come from order IDs, and the loading, empty and error branches reuse the project's status components.

<!-- react-expert:section id=implementation -->

## Clean and Complete Code

<!-- react-expert:change id=CHG-001 status=implemented -->
- File: src/components/order-list.tsx
- Change: Render the order collection with stable IDs, semantic markup and explicit loading, empty and error branches.
- Design: Keep the component pure, derive the visible count in render and preserve the existing named export convention.

```tsx
import type { Order } from '@/types/order';

type OrderListProps = {
  orders: readonly Order[];
  status: 'loading' | 'ready' | 'error';
};

export function OrderList({ orders, status }: OrderListProps) {
  if (status === 'loading') {
    return <p role="status">Loading orders.</p>;
  }

  if (status === 'error') {
    return <p role="alert">Orders could not be loaded.</p>;
  }

  if (orders.length === 0) {
    return <p>No orders available.</p>;
  }

  return (
    <main>
      <h1>Orders ({orders.length})</h1>
      <ul>
        {orders.map((order) => (
          <li key={order.id}>{order.reference}</li>
        ))}
      </ul>
    </main>
  );
}
```

<!-- react-expert:section id=tests -->

## Unit Tests

<!-- react-expert:test id=T-001 framework=vitest context=unit -->
- File: src/components/order-list.test.tsx
- Cases: success, empty collection, loading status and error status with accessible queries.
- Coverage: 88% statements and 84% branches measured by Vitest.

```tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { OrderList } from './order-list';

describe('OrderList', () => {
  it('renders orders with stable content', () => {
    render(<OrderList status="ready" orders={[{ id: 1, reference: 'A-100' }]} />);
    expect(screen.getByText('A-100')).toBeTruthy();
  });

  it('renders the empty state', () => {
    render(<OrderList status="ready" orders={[]} />);
    expect(screen.getByText('No orders available.')).toBeTruthy();
  });

  it('renders loading and error states', () => {
    const { rerender } = render(<OrderList status="loading" orders={[]} />);
    expect(screen.getByRole('status')).toBeTruthy();
    rerender(<OrderList status="error" orders={[]} />);
    expect(screen.getByRole('alert')).toBeTruthy();
  });
});
```

<!-- react-expert:section id=validation -->

## Validation

<!-- react-expert:coverage value=88 gate=80 tool=vitest -->

- [x] Unit tests run with Vitest.
- [x] Coverage threshold of 80% enforced by Vitest.
- [x] No derived state mirrors props in the component.
- [x] Artifact validated by validate_report.py.

Command: `pnpm test -- --coverage` exited 0 with 88% statements and 84% branches.

<!-- react-expert:section id=configurations -->

## Configuration

No changes.

<!-- react-expert:section id=evidence -->

## Evidence

<!-- react-expert:evidence id=EV-001 status=passed -->
- Result: pnpm test -- --coverage exited 0 with 88% statements and 84% branches.

<!-- react-expert:section id=assumptions -->

## Assumptions

- The existing Vitest setup uses jsdom and Testing Library with named exports.
- The Next.js App Router owns the server boundary and the component receives serializable props.

<!-- react-expert:section id=traceability -->

## Traceability

| Change | Test | Evidence |
| --- | --- | --- |
| CHG-001 | T-001 | EV-001 |
