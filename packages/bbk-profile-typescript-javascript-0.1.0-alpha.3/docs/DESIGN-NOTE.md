# Alpha.4 TypeScript/JavaScript structure design note

## 1. Meaningful type concepts

The profile treats identity, closed state/result variants, external boundary schemas, package/export/declaration contracts, mutable/resource ownership, caller-relevant failure classes and evidence dispositions as meaningful types. TypeScript/JSDoc notation is only one representation; runtime validation, emitted declarations, package consumers, browsers and hosts remain separate evidence surfaces.

## 2. Inline versus contract triggers

Use `inline` for a bounded local change with one owner and already constrained shape. Use `contract` for public/shared APIs, declarations, export maps, runtime schemas, persistence/migration, state/resource ownership, async cancellation/recovery, multi-package/module/host work, security/effect boundaries, packaging/consumer shape or hard-to-reverse topology.

## 3. Touchpoint vocabulary

CLI execution, API exchange, UI/browser interaction, packed package consumer, protocol/host trace, report, document, simulation, procedure and another explicitly described inspectable observation.

## 4. Material planned/actual differences

Public/shared export or runtime shape, declarations, package conditions, schema ownership, state/effect/resource owner, cancellation/cleanup contract, fixed decision, prohibited shortcut, migration or required touchpoint. Private helper location, local algorithm and private test-utility placement are normally delegated.

## 5. Evidence authority

- deterministic: JSON/schema/digest checks, path/package inventory, profile projections;
- agent-reviewed: responsibility, abstraction depth, behavior/failure paths, delegated freedom;
- tool-authoritative: checker, build, declaration, package consumer, browser and host results;
- human-reviewed: architecture/change authority and consequential divergence disposition;
- operational: deployed/runtime outcome and recovery evidence.

## 6. Unsupported or unqualified

The profile does not establish hostile-code sandboxing, all runtimes/frameworks, React Native, embedded hosts, native-addon internals or universal cross-runtime package behavior. Mixed non-software obligations are returned as adjacent obligations rather than claimed by the profile.
