# ADR numbering convention

ADR numbers are assigned when the ADR merges to `main`, not when a
branch is created. Drafts live at `docs/adr/XXXX-proposed-<slug>.md`
using a placeholder number; the final number is assigned and the file
renamed at merge time. If two in-flight branches both draft an ADR, the
one that merges first takes the next free number; the other renumbers
at its own merge. This avoids the parallel-branch collision that
produced ADR 0011 (renumbered from a requested 0009, because 0009 and
0010 were already taken by an already-merged ADR and a still-unmerged
sibling branch respectively).

## Current numbers and supersession map

Records **0024–0026** define the EdgePulse licence-gate extensions. The next
free number is **0027**. Other drafts retain XXXX until accepted and numbered
at merge.

| Record | Current authority |
| --- | --- |
| [0024 build-tool licences and Maven ecosystem](0024-build-tool-licences-and-maven-ecosystem.md) | Accepted; build-tool licence scope amended by 0026 |
| [0025 test-only modules and Jakarta annotation exception](0025-test-only-modules-and-jakarta-annotation-exception.md) | Accepted; clarifies 0024 Decision 2 and names the Jakarta runtime exception |
| [0026 build-tool licence families](0026-build-tool-licence-families.md) | Accepted; supersedes 0024 Decision 1 for build-tool only |
| 0014 supply-chain scanning | Accepted; CI implementation is IOT-WO-02 |
| 0019 Decision 4 (TB downstream) | **Superseded by 0020**: TB CE is the operational core and ingress owner |
| 0019 Decision 3 (data path) | Amended by 0020 Decision 7: TB outbound Kafka → ingestion adapter → canonical topics |
| 0011 Decision 3 infrastructure stack; 0015 Layer 3 installation | Superseded in the scope stated by 0021: Twinfra hosting and observability |
| 0018 broker conformance | 0021 drops the alternate broker target; Apache Kafka only |
| M1/M9 Migration Studio | Moved to EdgeMig by 0022; EdgePulse owns MR-1 to MR-14 |
| Product names | 0023 accepted; IOT-WO-05 rename is complete when its PR merges; MS0 still requires the owner receipt and release tag |

Accepted ADRs are not edited in place. Read historical text through the
later superseding/amending record, including 0021 Amendment 1.

## Withdrawn drafts (kept in tag `archive/reconcile-snapshot-2026-09-26`)

These files are absent from the Part B merge tree and remain reachable
through the snapshot tag.

| Draft | Disposition authority |
| --- | --- |
| `XXXX-proposed-tb-ce-kafka-bridge.md` | Withdrawn by 0020 |
| `XXXX-proposed-pre-tb-ce-anomaly-review.md` | Withdrawn by 0020 |
| `XXXX-proposed-mqtt-broker-and-cross-region-recovery.md` | Withdrawn by 0020 |
| `XXXX-proposed-private-cloud-infrastructure.md` | Withdrawn by 0021; removed from main by Part B |
| `XXXX-proposed-private-cloud-platform-options.md` | Withdrawn by 0021 |
| `XXXX-proposed-kubernetes-options-and-platform-tool-roles.md` | Withdrawn by 0021 |
| `XXXX-proposed-deployment-layers-tool-catalog-and-profiles.md` | Withdrawn by 0021 |
| `XXXX-proposed-cilium-network-and-workload-security.md` | Withdrawn by 0021 |
| `XXXX-proposed-observability-installation-sequence.md` | Withdrawn by 0021 |
| `XXXX-proposed-milestone-naming-and-roadmap.md` | Replaced by root MILESTONES.md; stays in tag |

## Retained application drafts and migration inputs

Unchanged application drafts: identity-authorization-and-privileged-access
(already on main), end-to-end-identity-and-entity-traceability,
platform-communication-direction, service-api-and-payment-provider-boundaries,
and resilience-and-workflow-patterns. They remain proposed; historical
references to withdrawn drafts do not reinstate those decisions.

Migration-studio-cdc-and-tenant-rules and
`docs/legacy-migration-execution-plan.md` carry the ADR 0022 EdgeMig
input banner. Ai-and-device-adapter-boundaries and
device-adapter-contract-and-capability-negotiation carry the ADR 0020 revision
banner. Config-studio, ai-integration-port-and-controls,
tenant-device-map-and-location, workflow-engine-selection and
roles-and-privileged-environment-access carry the deferral banner. None is
accepted or implemented by being retained here.
