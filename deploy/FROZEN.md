# Frozen IOT-EE infrastructure

The retained infrastructure under deploy/ is frozen by
[ADR 0021](../docs/adr/0021-twinfra-platform-and-licence-gate.md) and **must not
be extended**. Keep it until a separately authorized deletion work order.

Its history is preserved in the annotated tag
[archive/iot-ee-own-infra](https://github.com/amazen33/EdgePulse/tree/archive/iot-ee-own-infra),
on PR #37 merge commit `ca1f6d72835b8e38ef7f4a92381f87e108a4fd9a`.
Existing static infrastructure checks remain in place. No deployment or
real-environment run is authorized or claimed by this freeze.
