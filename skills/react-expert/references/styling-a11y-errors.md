# Styling, accessibility and errors

## Styling

Use only the solution already detected in the project:

- **Tailwind CSS**: reuse the configured theme, utilities and responsive breakpoints.
- **CSS Modules**: co-locate `.module.css` files and keep class names local.
- **Styled Components**: follow existing theme providers and component naming.
- **Shadcn/UI and Radix**: reuse installed primitives, variants and token conventions instead of recreating widgets.
- **Plain CSS**: respect the existing global and component stylesheet split.

Never introduce a new styling library, design system or icon set without an explicit request. Do not restyle unrelated elements to make a change fit.

## Semantic HTML

- Use `<button>` for actions, `<a>` for navigation, `<form>` for submissions, `<nav>` for navigation regions and `<main>` for the primary content.
- Keep heading levels in a logical order.
- Label form controls with visible `<label>` elements and connect them with `htmlFor` and `id`.
- Avoid clickable `div` or `span` elements that lack keyboard behavior; if unavoidable, add the correct role, tab order and key handlers.

## ARIA and keyboard

- Use ARIA only when native HTML cannot express the state or relationship.
- Keep focus visible, move focus predictably after dialogs or route changes, and return focus when overlays close.
- Provide accessible names for icon-only buttons.
- Announce pending, empty and error states with the project's live-region or status pattern when appropriate.
- Do not hide focusable elements from assistive technology unless they are truly inactive.

## Error and UI states

- Render loading, empty and error states explicitly for asynchronous flows.
- Keep error messages specific enough to support recovery and avoid exposing internal details.
- Preserve the user's input when a validation error is shown.
- Handle form validation with native constraints or the project's schema library; do not duplicate validation rules in unrelated layers.
- Keep error boundaries where the project already uses them and record any new boundary in the artifact.

## Decision checklist

- Does the markup use the correct native element?
- Is every interactive element reachable and operable by keyboard?
- Are labels, names and status messages available to screen readers?
- Are loading, empty and error states covered by tests?
- Is the existing styling solution used without adding a parallel system?
