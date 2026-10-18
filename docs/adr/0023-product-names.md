# ADR 0023: Product names, EdgePulse and EdgeMig

**Status:** Accepted (owner, 2026-10-14). The number is confirmed at merge.
- **Revisions before merge, the same day.** The owner's choices went in this order:
  1. SphinxStudio for the IoT platform and SphinxMig for the migration product;
  2. EdgePulse and SphinxStudio;
  3. EdgeSuite, rejected because aicas already sells EdgeSuite for edge and IoT fleets, and Akamai has filed EDGESUITE as a trademark;
  4. the names below.

  Nothing had been merged or renamed.

**Author:** Claude (architecture). **Implementer:** Codex (IOT-WO-05).

## Context

- The working name "IOT-EE" describes a category, not a product.
- ADR 0022 created a second product, called "migration-manager" so far.
- The names must be fixed **before** the migration contract v1 is published (IOT-WO-03, milestone MS2), because the contract's namespaces carry them.
- Renaming is cheapest now: one service exists and nothing is deployed.

**Name check** (web search, 2026-10-14; this is not a trademark clearance):

| Name | Finding | Risk |
| --- | --- | --- |
| **EdgePulse** (IoT platform) | No product by that exact name found. It sounds similar to **Edge Impulse** (edge machine learning for IoT devices, now part of Qualcomm), which is in a neighbouring field. VMware Pulse IoT Center and Sony's "Pulse Edge" headphones were also seen | Moderate: a sound-alike in IoT |
| **EdgeMig** (migration product) | No software product by that name found. The only matches were MIG welding equipment ("Warrior Edge") and CAM software (Edgecam) | Low |

## Decision

1. **EdgePulse** is the enterprise IoT platform formerly called IOT-EE: ThingsBoard CE core plus enterprise services (ADR 0020).
   - Identifiers use `edgepulse`.
   - The Maven groupId and Java packages use `com.edgepulse.platform`, and proto packages use `com.edgepulse.platform.contracts.*`.
   - The Kubernetes namespace prefix is `edgepulse-` and the Keycloak realm is `edgepulse`.
   - The repository is `amazen33/EdgePulse`, which is IOT-EE renamed so it keeps its history, PRs and redirects. It is public. A public repository with no licence file is "all rights reserved", so the owner chooses a licence before accepting outside contributions.
2. **EdgeMig** is the migration product that ADR 0022 calls "migration-manager".
   - Identifiers use `edgemig`.
   - Its private repository is `amazen33/edgeMig`, created by the owner on 2026-10-14.
   - It uses the same licence and supply-chain gates (ADR 0014 and 0021).
3. **Spelling.** In prose, write EdgePulse and EdgeMig. In identifiers, use all lowercase.
4. **ThingsBoard references.** Describing compatibility is allowed, for example "built on ThingsBoard CE". "ThingsBoard" and "TB" never appear in product names or logos, because ThingsBoard is a trademark of ThingsBoard, Inc.
5. **History stays as written.** Accepted ADRs, work orders, receipts, reviews and spike reports keep "IOT-EE" and "migration-manager". This ADR maps the old names to the new ones.

## Consequences

- IOT-WO-05 renames the repository, Maven coordinates, Java and proto packages, application names and documents, and adds a naming gate.
  - The proto package rename changes gRPC wire names. That is allowed **only** because nothing is deployed or consumed yet.
  - From the first published contract on, packages are frozen within each major version.
- **Residual risk.** Before any public launch, marketing or domain purchase, the owner checks trademark registries (EUIPO, WIPO, USPTO and Egypt's ITDA) for EdgePulse and EdgeMig in classes 9 and 42. Check EdgePulse against Edge Impulse in particular. If there is a conflict, a rename ADR changes only the names.
