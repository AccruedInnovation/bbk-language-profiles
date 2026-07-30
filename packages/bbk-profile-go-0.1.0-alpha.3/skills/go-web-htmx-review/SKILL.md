---
name: go-web-htmx-review
description: Review a Go application that intentionally uses HTMX, Alpine.js, html/template, and server-driven hypermedia for fragment contracts, state ownership, security, testability, and operational behavior.
---

# Go HTMX and Alpine Review

This is an optional stack profile. Apply it only when the project has deliberately selected server-driven hypermedia with HTMX/Alpine conventions.

## Contract inventory

Identify:

- full-page routes and fragment routes;
- HTMX request detection and response variants;
- stable fragment IDs, targets, swaps, OOB updates, events, and redirects;
- template ownership and domain view models;
- Alpine-owned ephemeral UI state;
- authorization and validation ownership;
- cache, CSRF, CSP, error, and retry behavior.

## Review concerns

- Do fragment handlers return only the contractually required fragment rather than accidental page chrome?
- Are full-page and fragment responses compatible with direct navigation and progressive enhancement?
- Are OOB swaps, selectors, IDs, and event names stable and documented?
- Does Alpine own only local transient UI behavior, or does it duplicate server domain state and authorization?
- Do `fetch`/XHR calls bypass the chosen HTMX flow without a deliberate boundary?
- Are templates limited to presentation composition rather than hidden domain logic?
- Are server validation and authorization authoritative?
- Are redirects, error fragments, focus, history, accessibility, and retry behavior explicit?
- Are user-controlled values safely escaped, and are any trusted HTML boundaries justified?

## Testing

Use handler tests for response selection and fragment contracts. Use real-server/browser or equivalent integration tests for history, swaps, streaming, cookies, CSRF, redirects, CSP, focus, and accessibility when those claims matter.

## Return

Return only deviations from the project's selected hypermedia architecture. Do not flag JSON endpoints, full pages, or Alpine network calls solely because they exist; explain the violated contract and evidence.
