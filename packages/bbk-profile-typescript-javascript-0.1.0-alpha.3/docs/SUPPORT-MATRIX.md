# Support matrix

The detailed runtime matrix is maintained in [`../references/support-matrix.md`](../references/support-matrix.md).

Alpha.4 implementation-structure support is **supported** for Node applications/CLIs, ESM packages, browser applications/libraries, checked JavaScript, mixed TS/JS workspaces and OMP extensions subject to exact-host qualification. Dual packages, alternative runtimes, Workers, Electron, native addons and WASM remain conditional. Non-software adjacent obligations are bounded and returned explicitly.

## Alpha.3 typed dispatch

State–Decision–Effect dispatch: **supported**. Review Assurance dispatch: **supported**. Live toolchain/native evidence remains separately qualified. The dispatch layer is read-only and cannot grant effects or generic assurance.
