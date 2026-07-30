# Rust implementation-structure projection

The Rust profile is a view over BBK's generic `ImplementationStructureContract`; it is never a second source of truth.

Meaningful type concepts are newtype identities and units, closed enum states/outcomes, public and wire boundary types, ownership/lifetime and async-lifecycle contracts, classified error/failure types, and evidence dispositions. Static types constrain construction and use; runtime tests, consumers, Miri/Loom/fuzzing, persistence rehearsals, package tests, and operational evidence remain necessary where the compiler cannot establish the claim.

A separate contract is normally triggered by public/shared API or schema change, async/concurrency ownership, persistence or migration, unsafe/FFI/ABI, multi-crate topology, package-consumer shape, or difficult-to-reverse boundaries. Ordinary private refactors remain `none`; a compact local type/owner decision may be `inline`.

Planned/actual comparison is semantic. Public/shared contract, state owner, effect, persistence, unsafe, migration, and package-consumer divergence may be material. Private module placement and helper naming are delegated unless the generic contract fixed them for a consequential reason.
