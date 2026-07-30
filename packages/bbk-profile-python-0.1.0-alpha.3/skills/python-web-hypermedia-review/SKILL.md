---
name: python-web-hypermedia-review
description: Optionally review Python web and hypermedia applications for HTTP contracts, server/client responsibility, HTML fragment behavior, HTMX/Alpine integration, validation, authorization, caching, and compatibility. Load only when the project actually uses these patterns.
---

# Python Web and Hypermedia Review

This is an optional focused pack. Do not load it for a generic library, CLI, worker, pipeline, or non-web service.

## Bind the declared interaction style

Identify whether the system uses JSON APIs, server-rendered pages, HTML fragments, HTMX, Alpine, forms, WebSockets, events, or a mixture. Do not impose HATEOAS or hypermedia when the accepted architecture is a different style.

## Review

- route and method semantics;
- request parsing and boundary validation;
- authentication, authorization, CSRF, CORS, cookies, and trusted hosts;
- response media types, status codes, headers, redirects, caching, and errors;
- full-page versus fragment contracts;
- progressive enhancement and non-JavaScript behavior where promised;
- HTMX headers, target/swap behavior, history, out-of-band updates, and error fragments;
- Alpine/client state that duplicates server authority or couples to unstable internal data shapes;
- idempotency and duplicate submissions;
- streaming, disconnects, cancellation, and background work;
- accessibility and focus behavior;
- API/version compatibility and generated clients where applicable;
- observability and privacy of request data.

## Validation

Use contract tests, browser or fragment tests, authorization/CSRF fixtures, caching and conditional-request tests, disconnect/duplicate tests, and selected end-to-end flows according to the assurance contract.

Return only web-specific findings and route non-web architecture, package, runtime, security, or operations issues to the corresponding focused pack. Do not create a second comprehensive review.
