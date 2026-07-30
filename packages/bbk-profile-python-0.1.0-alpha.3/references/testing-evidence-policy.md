# Python testing and evidence policy

Design tests from assertions and failure models. Use the cheapest sufficient method and add complementary methods only where consequence, uncertainty, interfaces, or protected floors justify them.

Preserve exact environment and subject identity. Source-tree, editable-install, wheel, sdist-derived, image, and deployed-service evidence are not interchangeable.

Flaky retries retain every attempt. Coverage is a gap signal, not a pass score. Property, model-based, differential, metamorphic, fuzz, mutation, fault-injection, snapshot, benchmark, and operational methods are trigger-based rather than universal.

Seeds, minimized examples, corpora, schedules, artifacts, migration states, and benchmark baselines are durable evidence when they support a material assertion.
