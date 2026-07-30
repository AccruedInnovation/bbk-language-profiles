# BBK Python profile OMP extension

This extension exposes the installed `bbk-profile-python` CLI through OMP.

Tools:

- `bbk_python_preflight`
- `bbk_python_resolve`
- `bbk_python_gate_plan`
- `bbk_python_structure`
- `bbk_python_slice`
- `bbk_python_structure_review`

Commands:

- `/bbk:python`
- `/bbk:python:preflight`
- `/bbk:python:gates`
- `/bbk:python:structure`
- `/bbk:python:slice`
- `/bbk:python:structure-review`

Structure and slice tools only project and compare JSON. They do not install tools, execute project gates, mutate repositories, change generic BBK objects, or declare verification, readiness, completion, or release.
