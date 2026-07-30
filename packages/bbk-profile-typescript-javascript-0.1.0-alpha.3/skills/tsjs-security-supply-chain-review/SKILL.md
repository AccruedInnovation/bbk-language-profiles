---
name: tsjs-security-supply-chain-review
description: Review TypeScript/JavaScript trust boundaries, injection, filesystem/network/process effects, browser sinks, secrets, dependencies, package-manager lifecycle scripts, registries, native addons, build tools, and release provenance.
---

# TS/JS Security and Supply-Chain Review

Review exact threat surfaces and supported environments. Do not reduce security to dependency-vulnerability counts.

## Trust-boundary inventory

Identify:

- external input and runtime validation;
- authentication, authorization and tenant boundaries;
- filesystem paths and archives;
- commands, arguments, shells and subprocesses;
- URLs, redirects, fetches and SSRF surfaces;
- browser DOM and message boundaries;
- secrets, cookies, tokens, environment and logs;
- plugins, extensions, workers, native addons and WASM;
- package installation, generation, build and publication;
- registries, Git/URL dependencies, mirrors and proxies.

## Server, CLI and build surfaces

Review:

- path traversal, symlinks, temporary files and archive extraction;
- command injection and shell interpolation;
- untrusted URLs, DNS/redirect behavior and internal-network access;
- regex/resource denial of service;
- prototype pollution and object-merging behavior;
- unsafe deserialization or dynamic code execution;
- environment-variable trust and configuration injection;
- log injection and secret leakage;
- child-process, worker and native-addon privileges;
- cleanup after partial failure.

## Browser surfaces

When applicable inspect:

- `innerHTML`, `outerHTML`, `insertAdjacentHTML`, unsafe template sinks, and equivalent framework escapes;
- URL construction and navigation;
- CSP and Trusted Types posture;
- `postMessage` origin, source and payload validation;
- CORS, CSRF and credential assumptions;
- cookie attributes and browser storage;
- secrets or private data included in bundles;
- source-map exposure;
- service worker scope and cache poisoning;
- SSR/hydration trust boundaries.

## Dependency and package-manager review

Capture:

- package manager and exact version;
- lockfile and frozen-install behavior;
- direct, transitive, peer, optional and bundled dependencies;
- Git, URL, local path and patched sources;
- overrides/resolutions and registry configuration;
- `preinstall`, `install`, `postinstall`, `prepare`, publish and other lifecycle scripts;
- downloaded executables and native builds;
- package-manager plugins;
- dynamic `npx`, `npm exec`, or equivalent use;
- dependency review, licence and provenance policy.

Installing dependencies is an effect. Do not run lifecycle scripts, update the lockfile, switch package managers, or add an audit tool without the applicable work-unit authority.

## Build and release chain

Review:

- code generators and canonical inputs;
- transpiler/bundler plugins and loaders;
- minification and source maps;
- CI action pinning and credentials;
- publication identity and two-factor/OIDC policy;
- package contents and secret scanning;
- provenance, signatures or attestations where claimed;
- native artifacts by target;
- rollback, revocation and compromised-release response.

## Runtime containment

A runtime permission model may reduce accidental effects, but do not treat it as protection from hostile code unless the runtime explicitly provides and the project qualifies that security boundary. Prefer OS/container isolation for untrusted execution.

## Testing

Use applicable adversarial evidence:

- malformed, oversized and nested input;
- path/symlink/archive attacks;
- command and URL injection;
- redirect and DNS behavior;
- DOM/message origin attacks;
- secret-redaction fixtures;
- install-script denial or allow-list behavior;
- frozen install and lock drift;
- hostile package contents;
- compromised or missing registry/provenance information;
- extension or plugin effect fencing.

## Output

Separate:

```text
confirmed vulnerability
credible exploit path
hardening opportunity
supply-chain exposure
policy/configuration gap
missing evidence
unsupported threat model
```

Tie severity to the actual reachable impact, authority, data, and deployment—not merely to a tool label. Return exact evidence and containment or remediation ownership.
