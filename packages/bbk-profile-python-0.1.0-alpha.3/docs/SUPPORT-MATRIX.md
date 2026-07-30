# Support matrix

| Area | Status | Notes |
|---|---|---|
| Pure-Python library | Primary | Public runtime and typing surfaces, package/import and consumer touchpoints |
| CLI application | Primary | Installed console entry points, exit/stdout/stderr and package subjects |
| Ordinary application/service | Primary | Runtime state, resources, configuration, startup/shutdown and operations |
| asyncio | Primary/conditional | Task ownership, cancellation, cleanup, result and fault paths |
| pyproject.toml sdist/wheel | Primary | Clean build, artifact inspection, install and consumer evidence |
| Static typing | Primary | Repository checker; static and runtime claims remain distinct |
| Runtime JSON/schema validation | Primary | External and persistence trust boundaries |
| Multiprocessing/process pools | Conditional | Start method, serialization, worker lifecycle and duplicate-work policy |
| Plugin/entry-point systems | Conditional | Installed distribution and consumer discovery required |
| Database migrations | Conditional | Representative data, forward/rollback/recovery and compatibility |
| Free-threaded CPython | Conditional/unqualified by default | Only when explicitly claimed and tested |
| CPython native extensions/Cython/cffi/ctypes/PyO3 | Conditional | Requires native-extension pack and platform evidence |
| Alternative interpreters | Partial | Only exact declared and tested implementations |
| Scientific binary-wheel ecosystems | Partial | Complex native stack and platform qualification remain project-specific |
| Embedded/mobile/WASM/GPU | Unqualified | Profile returns bounded unsupported or partial guidance |
| OS-vendor packaging | Unqualified | Separate platform/domain profile required |

## Alpha.3 typed dispatch

State–Decision–Effect dispatch: **supported**. Review Assurance dispatch: **supported**. Live toolchain/native evidence remains separately qualified. The dispatch layer is read-only and cannot grant effects or generic assurance.
