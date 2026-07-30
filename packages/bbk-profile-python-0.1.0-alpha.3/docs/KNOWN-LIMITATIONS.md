# Known limitations and next live qualification

- Package qualification covers the `0.1.0-alpha.4` structure/slice contract dialect and typed integration with BBK `0.1.0-alpha.8` or compatible successors. Live project-specific toolchain and runtime behavior remains separately qualified.
- Static actual inventory cannot prove runtime validation, state ownership, task/process lifecycle, persistence, native ABI, package contents, or operations. Supply evidence-backed inventory or run applicable project gates.
- The OMP extension is statically parsed, mock-registered, and invoked against the installed CLI. Live command/tool payload compatibility remains environment-specific.
- Gate recipes are planned only; they do not execute during resolution or projection.
- The profile does not install `build`, pytest, linters, type checkers, audit tools, package managers, native compilers, or other project tools.
- Structure review understands exact names and supplied evidence. Highly dynamic exports, generated modules, framework registries, monkeypatching, and custom import hooks require project-specific inventory.
- Free-threaded, alternative-interpreter, native-extension, platform-wheel, embedded, mobile, WASM, GPU, and OS-vendor packaging support is not globally qualified.

Next live qualification should install the current BBK core and this profile side by side in a disposable OMP environment, run all six OMP tools, write a profile lock containing contract/slice/projection digests, and exercise one real public-package structure review and one async or package execution slice.
