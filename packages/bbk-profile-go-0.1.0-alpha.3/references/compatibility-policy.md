# Go compatibility policy

Compatibility is directional and configuration-specific. Review these dimensions independently:

1. source API and exported declarations;
2. method sets, implicit interface satisfaction, and generic constraints;
3. module path, major-version suffix, import paths, and minimum Go version;
4. error identity, wrapping, sentinel and concrete error behavior;
5. build tags, target, CGO, and workspace-versus-standalone API;
6. wire and serialized representation;
7. persistent data and migrations;
8. configuration and environment;
9. CLI flags, exit status, streams, and output;
10. HTTP/RPC and operational behavior.

No single API-diff tool proves all dimensions. Public changes normally require exact exported-surface inspection, downstream compile fixtures, selected configuration matrices, and behavioral contract tests. A local `go.work` or `replace` directive must not hide what an external consumer receives.
