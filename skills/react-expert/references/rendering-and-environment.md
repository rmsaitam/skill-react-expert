# Rendering and environment

The detector reports both `framework` and `rendering`. The report must preserve the detected model instead of silently moving work between client and server.

## Client-Side Rendering

Vite, CRA and similar setups render the application in the browser. Keep browser-only APIs such as `window`, `document` and `localStorage` inside event handlers or effects with cleanup. Do not rely on server-only packages in modules imported by the client entry point.

## Full-Stack and SSR

Next.js and Remix may render on the server, stream content or use Server Components. Respect the framework's boundary:

- Keep interactive state, browser APIs and event handlers in Client Components.
- Keep secrets, direct database access and server-only modules on the server.
- Do not convert a Server Component into a Client Component only to reuse a helper; pass serializable data or composition children instead.
- Use Server Actions only when React 19 and the detected framework support them natively.

## Hybrid apps

An SSR framework can still contain client islands. Record `hybrid` when both server-rendered routes and client-only flows are evident. Do not assume that every file is server-only or that every component needs `"use client"`.

## Version and framework interaction

| Detected environment | Safe behavior |
| --- | --- |
| React 18 with CSR | Use React 18 APIs and the existing data fetching pattern |
| React 18 with SSR | Preserve framework loaders and do not introduce React 19 Actions |
| React 19 with CSR | Use React 19 APIs supported by the client build |
| React 19 with SSR | Use Actions only with native framework support and keep server boundaries intact |
| React 17 or earlier | Preserve legacy patterns and record the constraint |

## Decision checklist

- Identify where the changed component is imported and rendered.
- Confirm whether its props are serializable across a server boundary.
- Confirm whether the data source is server-only, client-only or shared.
- Keep loading, empty and error states in the layer that owns the data flow.
- Record any new framework configuration in the artifact.
