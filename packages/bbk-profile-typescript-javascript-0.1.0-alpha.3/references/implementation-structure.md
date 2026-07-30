# TypeScript/JavaScript implementation structure

The generic `ImplementationStructureContract` remains authoritative. This profile projects it into:

- workspace and package topology;
- modules, entry points, export maps, declarations and generated artifacts;
- browser bundles, server runtimes, CLIs, plugins and host extensions;
- exported types, runtime schemas, events/messages and package consumers;
- mutable state and async-resource ownership;
- network, filesystem, process, package-install, browser-storage and host effect boundaries;
- test seams, observability and migration touchpoints;
- fixed decisions, delegated freedom and prohibited shortcuts.

Use `none` for routine private work, `inline` for compact local structure guidance and `contract` for material public/shared, stateful, multi-package, migration, security/effect or hard-to-reverse work.

A planned/actual comparison is material when it changes a fixed decision, public/shared contract, runtime schema, source of truth, resource/cancellation owner, effect boundary, package consumer, migration path or required touchpoint. Exact private helper-tree equality is not required.
