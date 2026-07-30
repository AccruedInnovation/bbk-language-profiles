# Known limitations and next live qualification

- No live BBK alpha.4 core executable was included in the update kit. The package qualifies direct alpha.4 profile entrypoints, schemas, locks, fixtures, and static/mock harness behavior; live core invocation remains to be tested.
- Static actual inventory cannot prove runtime validation, state ownership, task/process lifecycle, persistence, native ABI, package contents, or operations. Supply evidence-backed inventory or run applicable project gates.
- The OMP extension is statically parsed, mock-registered, and invoked against the installed CLI. Live command/tool payload compatibility remains environment-specific.
- Gate recipes are planned only; they do not execute during resolution or projection.
- The profile does not install `build`, pytest, linters, type checkers, audit tools, package managers, native compilers, or other project tools.
- Structure review understands exact names and supplied evidence. Highly dynamic exports, generated modules, framework registries, monkeypatching, and custom import hooks require project-specific inventory.
- Free-threaded, alternative-interpreter, native-extension, platform-wheel, embedded, mobile, WASM, GPU, and OS-vendor packaging support is not globally qualified.

Next live qualification should install BBK alpha.4 and this profile side by side in a disposable OMP environment, run all six OMP tools, write a profile lock containing contract/slice/projection digests, and exercise one real public-package structure review and one async or package execution slice.
