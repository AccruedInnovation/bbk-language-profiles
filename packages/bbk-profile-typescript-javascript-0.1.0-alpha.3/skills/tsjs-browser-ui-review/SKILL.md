---
name: tsjs-browser-ui-review
description: Review browser-specific TypeScript/JavaScript UI behavior, accessibility, DOM trust boundaries, CSP/XSS, SSR/hydration, routing, storage, service workers, performance, and browser compatibility.
---

# TS/JS Browser and UI Review

Apply only when a browser or browser-like runtime is part of the declared subject. Do not presume one framework or rendering model.

## Bind the browser contract

Record:

- supported browsers, versions and devices;
- client-only, SSR, static, server-driven, or hybrid rendering;
- bundler, CSS/asset pipeline and source maps;
- hydration and server/client data boundary;
- routing/history model;
- storage, cookies and service workers;
- accessibility requirements;
- CSP, Trusted Types and security posture;
- performance and bundle budgets;
- real-browser test coverage.

## Correctness and state

Review:

- ownership of server, URL, global, component and derived state;
- stale async results and request cancellation;
- optimistic updates and rollback;
- race conditions between navigation, hydration and data loading;
- focus, selection and scroll preservation;
- error, empty, loading and offline states;
- event listener and observer cleanup;
- browser storage versioning and corruption;
- service-worker update and cache invalidation.

## Accessibility

Inspect applicable:

- semantic HTML and landmark structure;
- accessible names and descriptions;
- keyboard navigation and visible focus;
- focus movement for dialogs, errors and route changes;
- screen-reader announcements;
- form labels, validation and error recovery;
- contrast, motion and reduced-motion behavior;
- zoom/reflow and responsive layout;
- pointer alternatives;
- automated versus manual coverage.

Accessibility is behavior, not only lint output.

## Security and privacy

Review:

- unsafe DOM/HTML sinks;
- URL and navigation construction;
- CSP and Trusted Types integration;
- `postMessage` origin/source/payload validation;
- cookies, storage and cross-origin credentials;
- CSRF/CORS assumptions;
- secrets and private data in bundles;
- source-map exposure;
- third-party scripts and analytics;
- service-worker scope and cache poisoning;
- SSR/hydration injection boundaries.

## Performance

Use measured evidence for:

- bundle and route chunk size;
- startup and interaction latency;
- main-thread blocking;
- rendering and layout work;
- network waterfalls and caching;
- image/font/asset behavior;
- memory retention and detached DOM;
- long tasks and event-loop delay;
- server-render and hydration cost.

Do not recommend a framework rewrite, code splitting, memoization, workers, or server-driven UI without a demonstrated requirement and cost model.

## Testing

Use real browsers for claims involving:

- layout, accessibility tree or focus;
- navigation/history;
- service workers and cache;
- CSP/security policy;
- browser APIs and scheduling;
- SSR hydration;
- supported-browser compatibility.

DOM emulation remains useful for fast component logic but is not sufficient evidence for every browser assertion.

## Output

Classify findings as browser correctness, accessibility, security/privacy, hydration, routing/storage, service-worker/cache, performance, compatibility, or evidence gap. State browsers and artifacts tested, what was emulated, and what remains unqualified.
