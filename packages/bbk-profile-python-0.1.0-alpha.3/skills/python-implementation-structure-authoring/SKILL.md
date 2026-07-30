---
name: python-implementation-structure-authoring
description: Project a BBK ImplementationStructureContract into Python distribution, package, module, import, type, runtime-validation, state, resource, failure, packaging, and test-seam vocabulary without changing the generic contract or freezing harmless private choices.
---

# Python Implementation Structure Authoring

Use this skill only when BBK has selected `inline` or `contract` implementation structure. The generic `ImplementationStructureContract` remains authoritative; this skill produces a Python projection and authoring guidance.

## Authoring sequence

1. Bind the exact generic contract ID, revision, digest, baseline, subject, scope, interfaces, assurance tier, fixed decisions, delegated freedom, prohibited shortcuts, and review policy.
2. Run or consume the static `bbk-python preflight`. Do not import the application, create an environment, install tools, or execute project commands during projection.
3. Map the realization using the repository's actual packaging and import model:
   - distribution, wheel, sdist, application, service, or internal-only repository;
   - package, namespace package, module, entry point, plugin group, generated artifact, migration, native extension, test, and fixture topology;
   - source-tree, editable-install, wheel, sdist-derived-wheel, and deployed subjects where materially different.
4. Make consequential Python contracts explicit:
   - public runtime import/export surface;
   - public typing surface, stubs, `py.typed`, overloads, and checker expectations;
   - runtime schemas and validation at external or persistence trust boundaries;
   - exception taxonomy and stable caller handling;
   - serialization, persistence, configuration, CLI, plugin, and process-message contracts;
   - resource, context-manager, task, process, queue, transaction, and cancellation ownership.
5. Apply the type-depth test. Recommend a type or abstraction only when it prevents a material invalid combination, localizes an invariant, clarifies ownership, stabilizes a boundary, improves change locality, creates a meaningful test seam, or hides consequential complexity.
6. Distinguish three different claims:
   - static annotation or type-checker evidence;
   - runtime construction and validation evidence;
   - operational or consumer evidence in the supported environment.
7. Record fixed decisions narrowly. Suitable fixed decisions include public import names, distribution metadata, state ownership, runtime validation location, process-message schema, task/cancellation ownership, persistence or migration sequencing, effect ownership, and supported package subjects.
8. Preserve delegated freedom for private helper names, local iteration, equivalent private module placement, internal representation choices that preserve the fixed contracts, and test utility layout.
9. Define test seams and touchpoints before independent work begins. Prefer consumer-visible imports, installed-wheel behavior, CLI entry points, plugin discovery, runtime validation, async cancellation, process handoff, migration rehearsal, and package inspection over private-tree equality.
10. Return unsupported or uncertain areas explicitly. Do not invent support for native extensions, free-threaded execution, alternative interpreters, platform packaging, or deployment environments that the repository does not claim and the profile has not qualified.

## Python type vocabulary

Use the least powerful form that protects the actual contract:

- domain-specific identity values instead of interchangeable strings or integers where confusion is material;
- `Enum` or closed literal/discriminated forms for closed states and outcomes;
- frozen dataclasses or ordinary value objects for stable immutable value semantics;
- `TypedDict` for dictionary-shaped static contracts without implying runtime validation;
- `Protocol` at genuine consumer-defined substitution and test seams;
- abstract bases only when runtime nominal behavior or registration is required;
- runtime validation models or explicit parsing at untrusted boundaries;
- exception classes or result dispositions when callers need stable failure classification;
- context managers and async context managers for resource lifetime;
- explicit task, cancellation, process, queue, transaction, and retry ownership.
- evidence dispositions that keep `NOT_RUN`, `BLOCKED`, `ERROR`, `INCONCLUSIVE`, `PASS`, and `FAIL` distinct rather than collapsing availability or infrastructure failure into a test result.

Do not introduce deep inheritance, a protocol for every class, duplicate DTO/model layers without distinct semantics, or framework-specific schemas in the stable domain without a real boundary need.

## Return

Return the Python structure projection, selected profile skills and planned gates, unsupported or uncertain areas, advisories, blockers, and the no-authority boundary. Never claim that the projection changes the generic contract, grants tools/effects, or proves conformance.
