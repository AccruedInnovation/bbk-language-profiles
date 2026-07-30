# Support matrix

| Domain | Initial status | Notes |
|---|---|---|
| `std` library | Primary | Includes public API and clean package review |
| Binary / CLI | Primary | Includes release artifact, configuration, exit and cleanup behavior |
| Cargo workspace | Primary | Static workspace/member/default-member preflight |
| Async service | Primary | Runtime-specific conventions remain repository-owned |
| Persistence / migration | Primary | Requires fault/recovery and compatibility selection where material |
| Publishable crate | Primary | Clean `cargo package` and archive inspection |
| Unsafe Rust | Conditional | Requires explicit invariant and focused assurance |
| FFI / ABI | Conditional | Requires target, calling convention, layout, ownership, unwind, and binding evidence |
| Procedural macro | Conditional | Requires build-time, expansion, diagnostics, and supply-chain checks |
| Cross-target | Conditional | Only declared supported targets are planned |
| WASM | Partial | Host/runtime boundary requires project qualification |
| `no_std` / `alloc` | Partial | Generic rules available; target/runtime gates not comprehensive |
| Embedded | Unqualified | Requires a separate target/hardware profile |
| Kernel | Unqualified | Requires kernel-specific soundness and build profile |
| GPU | Unqualified | Requires target/toolchain-specific profile |
