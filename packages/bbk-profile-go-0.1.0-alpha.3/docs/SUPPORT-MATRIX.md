# Support matrix

| Subject | Status |
|---|---|
| Ordinary Go modules and workspaces | Primary |
| Libraries, public packages, commands, HTTP/RPC services | Primary |
| Concurrency, cancellation, generated code | Primary with applicable review/evidence |
| Public module release, migration, platform variants, PGO | Conditional |
| Unsafe, CGO, assembly, ABI | Conditional; focused review and exact toolchain evidence required |
| Mixed socio-technical slices | Partial Go projection with adjacent obligations |
| Plugins, mobile, TinyGo, embedded, eBPF, specialized WASM | Partial or unqualified |
| Custom compiler forks and unusual shared-library modes | Unqualified |

Static projection does not establish runtime input validity, race freedom, goroutine termination, persistence durability, CGO pointer lifetime, deployment correctness, or operational recovery.

## Alpha.3 typed dispatch

State–Decision–Effect dispatch: **supported**. Review Assurance dispatch: **supported**. Live toolchain/native evidence remains separately qualified. The dispatch layer is read-only and cannot grant effects or generic assurance.
