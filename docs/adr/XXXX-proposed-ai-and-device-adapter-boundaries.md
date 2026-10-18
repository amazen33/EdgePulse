# Proposed ADR — Provider-neutral AI and device integration boundaries

> Needs revision for ADR 0020: devices connect to TB CE transports.

Status: proposed; this is a design direction, not an implementation or
claim of device/protocol coverage. Number at merge per
`docs/adr/README.md`.

## Proposed decisions

1. **AI providers are outbound adapters.** AI-assisted capabilities
   depend on Java-owned ports and provider-neutral request/result
   types. Spring AI and vendor SDKs may be used only within a selected
   adapter; domain and application code depend on Java APIs, not Spring
   abstractions. Select providers by deployment profile and tenant data
   policy. The initial assistant is read-only; any later action/tool
   call requires an allowlisted operation, fresh authorization and an
   auditable human-approved command path. AI failure cannot block core
   telemetry, alarms, rules or device commands.
2. **Do not assume one AI environment.** Provider capabilities,
   model/version, data residency, retention, egress and availability are
   declared per profile. An unavailable or disallowed provider fails
   closed for AI features, while the core product remains operational.
   No device secrets or unredacted sensitive data are sent to a model by
   default.
3. **Devices integrate through protocol adapters.** Device identity,
   tenant scope, normalized telemetry, commands and acknowledgements
   are provider-neutral contracts. MQTT is the initial supported
   transport. HTTP/CoAP and legacy ThingsBoard integration are separate
   adapters only after protocol/version inventory and compatibility
   fixtures exist; do not claim generic legacy compatibility from an
   adapter interface alone.
4. **TB CE is both upgradeable and replaceable.** Preserve the no-fork,
   thin-customization model and isolate version-specific APIs, payloads
   and extensions in its adapter. The platform domain must not depend on
   TB implementation classes. A newer CE release is supported only
   after its adapter/customization migration and compatibility suite
   pass. Another platform may replace TB CE only by implementing the
   owned device, rule and integration contracts and passing behavioral
   conformance tests; this can require a planned parity/migration effort
   and is not claimed to be drop-in. This supersedes ADR 0011 Decision
   2's “not replaceable” wording while retaining its upgrade and no-fork
   constraints.

## Acceptance criteria

Architecture tests prevent Spring/vendor AI SDK imports outside their
adapter packages. Provider contract tests prove profile selection,
residency rejection and degraded operation. Protocol fixtures cover
each explicitly supported device path, including authentication,
normalization, command acknowledgement, replay and reconnect behavior.
The compatibility matrix names tested TB CE versions and supported
features; unknown combinations are reported unsupported rather than
silently accepted.

## Refinements (2026-09-26)

Decisions 1-2 are detailed in `XXXX-proposed-ai-integration-port-and-controls.md`
and Decision 3 in `XXXX-proposed-device-adapter-contract-and-capability-negotiation.md`.
Requirement-by-requirement status and acceptance tests are in
`docs/ai-device-traceability.md`.

## Related decisions

ADR 0011 (platform architecture), ADR 0017 (hexagonal conventions), ADR
0019 (streaming/RAG), and the requirements addendum.
