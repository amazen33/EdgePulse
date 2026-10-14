# Proposed TBMQ/Kafka/TB CE assurance evidence plan

Status: design plan only. TBMQ CE is a broker candidate, not the selected
product or a deployed pipeline. The Kafka-to-TB CE bridge is proposed and has
no end-to-end operational proof. This plan maps potential evidence for an
IOT-EE MQTT broker -> canonical Kafka -> external bridge -> TB CE path. The
organization's risk assessment, Statement of Applicability, business impact
analysis and independent audit determine certification scope and conclusions.

| Control area | Evidence to produce | Current gap |
| --- | --- | --- |
| ISO/IEC 27001 A.5.9, assets | Versioned register of broker, Kafka, CE, bridge, nodes, images, data classes, owners, regions and data flows | No selected broker or deployed asset inventory |
| A.5.19-5.22, suppliers | Pinned-release license, maintainer/security posture, advisory and support assessment for each project and hosted supplier; dated re-review | Candidate research only |
| A.5.15-5.18, access | Human/admin roles; MQTT client/topic ACLs; Kafka ACLs; CE permissions; service JWT/RBAC/ABAC and denial tests; access reviews | TBMQ CE offers MQTT ACLs but vendor lists advanced admin RBAC as PE-only; document and test external identity, restricted admin path, separation of duties or edition choice before selection |
| A.8.24, cryptography | TLS/mTLS flow inventory, device-certificate issuance, CA custody, rotation/revocation, expiration and negative handshake tests; key references only | No deployed certificates or rotation evidence |
| A.8.15-8.16, logging/monitoring | Defined audit events, broker/admin and Kafka/bridge/CE logs, centralized OTel pipeline, access-controlled retention, correlation IDs, lag/denial/failure alerts and response records | Vendor lists TBMQ audit logs as PE-only; CE requires a tested external audit source or edition decision. Metrics are not an admin audit trail |
| A.8.8, vulnerabilities | SBOM for source/dependencies/images, dated scan results, triage, remediation and patch/exception records | Supply-chain gate remains planned |
| A.8.25-8.28, secure development | SDLC policy, threat model, reviewed PRs, SAST/DAST and dependency findings for the actual bridge language and build, tests and release provenance | Bridge not implemented |
| ISO 22301 continuity | Impact analysis and approved RTO/RPO, regional state map, backup/restore and failover/failback runbooks, exercise results, corrective actions | No regional deployment or tested recovery |

For each evidence item retain an ID, system/edition/version, environment,
control mapping, UTC capture time, method, synthetic or redacted result,
owner, reviewer, classification, retention rule and content hash. Store
restricted records in the approved evidence store; Git holds templates and
links only. Use `planned`, `lab verified` or `operational evidence pending`
status, never infer compliance from a green build or design document.

The broker decision and region-recovery test matrix are in the proposed
[MQTT broker and cross-region recovery ADR](../adr/XXXX-proposed-mqtt-broker-and-cross-region-recovery.md).

Sources: [ISO/IEC 27001](https://www.iso.org/standard/27001),
[ISO 22301](https://www.iso.org/standard/75106.html),
[TBMQ architecture](https://tbmq.io/docs/architecture/),
[TBMQ edition matrix](https://tbmq.io/), and
[Kafka geo-replication](https://kafka.apache.org/35/operations/geo-replication-cross-cluster-data-mirroring/).
