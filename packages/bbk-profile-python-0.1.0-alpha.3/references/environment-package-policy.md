# Python environment and package policy

The repository owns its interpreter range, environment manager, build backend, lock or range policy, indexes, extras, commands, and supported artifacts.

BBK distinguishes:

```text
source tree
editable install
installed wheel
sdist-derived wheel
container/image
deployed service
```

Evidence may be reused only for the exact subject and environment closure it proves. The profile never creates an environment, installs packages, upgrades Python, changes a backend, or resolves dependencies without separate effect authority.

Libraries normally declare compatible ranges and test selected lower/current combinations. Applications normally bind a complete environment. Exceptions require an explicit project policy.
