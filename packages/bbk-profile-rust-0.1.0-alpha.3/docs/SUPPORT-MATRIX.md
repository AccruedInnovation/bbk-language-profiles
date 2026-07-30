# Rust profile support matrix

| Subject | Status | Notes |
|---|---|---|
| Ordinary `std` library/binary/CLI | Supported | Repository commands remain authoritative |
| Cargo workspace and multi-crate topology | Supported | Structure projection and consumer slices available |
| Public crate API and SemVer-sensitive shape | Supported | Requires applicable consumer/compatibility evidence |
| Async service ownership/cancellation | Supported | Runtime behavior still needs execution evidence |
| Persistence/migration/idempotency | Supported | Migration and replay claims require runtime evidence |
| Unsafe/FFI/ABI | Conditional | Requires focused assurance and qualified environment |
| Publishable crate/package consumer | Supported | Clean-package and downstream evidence remain project-specific |
| Proc macro | Conditional | Expansion/build-time behavior needs project fixtures |
| Cross-target/WASM | Conditional | Exact targets and host behavior must be qualified |
| `no_std`/alloc-only | Partial | Profile may project bounded structure; full environment unqualified |
| Embedded/kernel/GPU | Unsupported or unqualified | Requires separate domain procedure and live target evidence |
| Planned-versus-actual private module changes | Supported | Harmless delegated divergence is not a material failure |
| Live Cargo/Miri/Loom/fuzz/mutest execution | Project-specific | Never run merely during resolution |

## Alpha.3 typed dispatch

State–Decision–Effect dispatch: **supported**. Review Assurance dispatch: **supported**. Live toolchain/native evidence remains separately qualified. The dispatch layer is read-only and cannot grant effects or generic assurance.
