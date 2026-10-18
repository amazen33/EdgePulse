# IOT-WO-05: Rename IOT-EE to EdgePulse

**Status:** Approved (owner, 2026-10-14, ADR 0023). **Milestone:** MS0, the last step. Start after IOT-WO-01 Parts B and C have merged, and before IOT-WO-02 and IOT-WO-03.
**Author:** Claude · **Implementer:** Codex · **Branch:** `codex/iot-wo-05-rename` · **Decision:** ADR 0023

## Owner action first (done on 2026-10-14: `edgeImpulse` deleted, `IOT-EE` renamed to `EdgePulse`)

1. Delete the empty repository `amazen33/edgeImpulse`. It holds one empty "Initial commit" from 2026-10-06, and its name is Qualcomm's product, Edge Impulse.
2. Rename `amazen33/IOT-EE` to `amazen33/EdgePulse` in its settings. Renaming keeps the history, PR #29, CI runs and redirects from the old URLs. The repository stays public.
3. Then Codex updates the local remote URL.

## Name map

| Old | New |
| --- | --- |
| IOT-EE (prose) | EdgePulse |
| migration-manager (prose, outside history) | EdgeMig |
| groupId `com.iotee.platform`, `iotee-platform-parent` and other `iotee-*` artifactIds | `com.edgepulse.platform`, `edgepulse-platform-parent`, `edgepulse-*` |
| Java packages `com.iotee.platform.*` | `com.edgepulse.platform.*` |
| Proto `package` and `java_package` `com.iotee.platform.contracts.*` | `com.edgepulse.platform.contracts.*` |
| Spring application names such as `iotee-service-identity` | `edgepulse-service-identity` |
| Other `iotee` and `iot-ee` identifiers in code, configuration, CI and documents | `edgepulse` |

## Rules

1. **Never rewrite history.** Leave `docs/adr/` (except `README.md`), `docs/work-orders/`, `docs/acceptance/`, `docs/reviews/`, `docs/spikes/`, tags and Git history alone.
2. **Leave frozen material alone.** The `deploy/` layers frozen by ADR 0021 keep their names; they are deleted later.
3. **ArchUnit rules:**
   - Update every package pattern to the new root.
   - Every planted-violation fixture must **still fail** for the right reason. Prove it with the existing negative tests.
   - The fake vendor packages (`com.stripe`, `org.keycloak`, `com.openai` and the others) stay as they are.
4. **Proto packages.** Renaming them changes gRPC full names. It is allowed here only because nothing is deployed or consumed (ADR 0023). Regenerate the stubs and keep the transport-equivalence and round-trip tests green.
5. **Naming gate.** Add a CI check that fails on `iotee` or `iot-ee` (case-insensitive) in paths or contents outside the history paths and frozen layers in rules 1 and 2. Start it as blocking.

## Acceptance

- `mvn -B -f pom.xml verify` passes, with the same test count as before the rename or a higher one.
- CI is green, including the new naming gate.
- The PR lists every remaining `iotee` or `iot-ee` hit with its reason. Each should be history or a frozen layer.
- `README.md` names the product once at the top: "EdgePulse (formerly IOT-EE)".

## Out of scope

- Renaming the local folder `D:\project\IOT-EE`. The owner may do it later, when no branch has uncommitted work.
- The EdgeMig repository (`amazen33/edgeMig`, private, created by the owner on 2026-10-14). Its bootstrap work order comes separately.
