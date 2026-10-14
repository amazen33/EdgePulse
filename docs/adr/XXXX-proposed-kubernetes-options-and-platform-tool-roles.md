# Proposed ADR -- Kubernetes options and platform tool responsibilities

Status: proposed. No OKD/OpenShift cluster or new security/analytics
tool has been installed or proven against IOT-EE. This proposal
clarifies the role of named tools while preserving replaceable ports,
service-owned data, the open-source-default rule and the existing RKE2
lab implementation.

## Kubernetes platform choice

Topology visualization is an observability need, not a reason by itself
to replace Kubernetes. Grafana/Tempo Service Graph is the default
service-dependency view on any supported cluster; Cilium/Hubble provides
the network-flow and connectivity map if the Cilium profile is selected (proposed Cilium/Ambient ADR).
OpenShift Container Platform and OKD
are **Kubernetes distributions/platform profiles**, not topology
viewers. Keep RKE2 as the current on-prem lab/default candidate. Add
OKD as an **open-source, community-supported alternative** for a
separate on-prem profile. Treat Red Hat OpenShift as an **optional
commercial/support profile**, outside the open-source default.

An OKD or OpenShift profile has its own Layer 0/1 installation plan,
capacity and host OS assumptions, storage/ingress/routing and security
configuration. It must not be presented as a flag that changes RKE2
into OKD. Reuse versioned application contracts and charts only after
conformance on restricted SCC/arbitrary UID, non-root images, service
accounts, networking, storage, operator dependencies, upgrade/rollback,
backup/restore, and LGTM/Collector/Service Graph ingestion. Validate
Cilium/Hubble and workload-authentication conformance separately for each
profile that selects them. OKD's
community support alone does not prove a 24/7 production support SLA;
the deployment owner must supply an operations/support model.

## Tool responsibility matrix

The [private-cloud platform options ADR](XXXX-proposed-private-cloud-platform-options.md)
compares OKD/Machine API/OCM with Harvester/Rancher/RKE2 and
CloudStack/OpenStack with upstream CAPI. These are separate infrastructure
and cluster-lifecycle profiles; no cross-profile installation is implied.

| Tool | Intended role and boundary | Selection/verification state |
| --- | --- | --- |
| Keycloak | Initial OIDC/SSO identity provider, including separate admin/operator clients and MFA policy. Each service verifies JWT issuer, signature, audience, expiry and tenant claims itself; it never trusts only gateway headers. | Planned behind OIDC standards; provider swap needs conformance. |
| Cilium + Hubble | Candidate CNI, pod reachability policy and network-flow map. Cilium mutual authentication is beta and must not be treated as production workload mTLS proof. | No installation or policy proof. See proposed Cilium/Ambient ADR. |
| Istio Ambient | Candidate workload identity, mTLS and in-mesh L4/L7 policy alongside Cilium; waypoint required for L7. Services still authorize tenant actions. | No installation or Cilium coexistence proof. See proposed Cilium/Ambient ADR. |
| OPA | Candidate replaceable policy evaluator for versioned RBAC/ABAC rules. A service owns the enforcement point and resource/tenant checks even when it calls OPA. | Proposed, not mandatory until a policy-engine ADR and outage/latency proof. |
| OpenBao / HashiCorp Vault | OpenBao is the proposed fully open-source secrets backend; current HashiCorp Vault releases are source-available BSL and remain an explicitly licensed optional provider. Spring Vault is a Java client, not a secrets server. Services access only scoped secret references/workload identities. | OpenBao/Vault compatibility, backup/restore and rotation tests pending. The earlier requirement naming HashiCorp Vault first needs reconciliation. |
| Falco | Linux/Kubernetes **runtime detection and alerting** feeding the security/observability response workflow; it does not enforce access or replace service authorization. | Candidate, installed only after kernel/driver, privilege, performance and alert-routing review. |
| Trivy | CI/deployment supply-chain scanning for dependencies, images, IaC, secrets and SBOM-related evidence; findings flow through a reviewed triage/gate policy. | Planned by ADR 0014; no claim that CI currently enforces the full gate. |
| SonarQube Community Build | Optional code-quality/static-analysis server. The specific Community Build is open source; paid Server/Cloud capabilities must not be assumed present. | Candidate, after CI integration and edition/version/license review; not a security substitute for Trivy or tests. |
| Ceph RGW / MinIO | S3-compatible object-storage adapters for evidence and possible analytics storage. Ceph RGW is a candidate but WORM/Object Lock conformance is unproven. The archived MinIO open-source repository is rejected as a new default. | No on-prem WORM default is approved until real retention/legal-hold and recovery tests pass. |
| Apache Iceberg | Optional **analytic table format** on approved object storage/catalog, not an OLTP database or device-ingestion authority. | Introduce only with a data-lake use case, tenant isolation, retention and catalog governance. |
| Apache Spark | Optional distributed batch/SQL processing engine for historical reprocessing, migration analysis or Iceberg analytics; not a replacement for Flink's planned streaming synthesis or core telemetry path. | Introduce only when measured workload justifies it; run as isolated jobs with quotas and evidence. |
| Kubernetes Jobs/CronJobs | Portable default candidate for bounded background or scheduled work; service-owned workers remain appropriate for event-driven work. Neither mechanism is the durable business-workflow authority by itself. | Select per workload with retry, idempotency, tenant isolation, quotas, progress and recovery tests. |
| AWS Lambda | Optional AWS-only execution adapter for short, stateless event handlers or jobs. It is not the default for on-prem/other clouds and does not replace a durable workflow coordinator. Business decisions remain in service-owned use cases behind a job-execution port. | No Lambda adapter selected; require an AWS profile, cost/timeout/security review and cross-profile conformance before use. |
| Flowable Open Source | Provisional Apache-2.0 BPMN/CMMN/DMN and human-task pilot for complex alarm resolution or anomaly review; start with a service-owned durable state machine for simpler flows. | No production engine selected. Compare CIB seven, EximeeBPMS and FINOS Fluxnova through the [workflow selection ADR](XXXX-proposed-workflow-engine-selection.md); prove tenant isolation and operations. |
| Camunda 8 Self-Managed | Optional commercially licensed workflow-engine provider behind the same service-owned workflow boundary. It cannot be the fully open-source production default because Camunda requires an Enterprise license for production self-managed use. | Not selected; require owner licensing decision and edition/version-specific review before any profile. |
| Nextcloud Server | Candidate tenant-scoped document collaboration for manuals, work-order attachments and technician file exchange; core server is AGPL-3.0-or-later. | Optional candidate; assess edition, apps, identity integration, isolation, backup and support. |
| ownCloud Infinite Scale (oCIS) | Candidate file sync/share provider for the same collaboration boundary. Repository source is Apache-2.0, but ownCloud says some stable builds it distributes have an EULA. | Optional candidate; pin and review the exact source/build, edition and distribution terms before treating it as an open-source default. |
| Seafile / Pydio Cells / CryptPad | Alternative candidates: Seafile for file sync/share, Pydio Cells for content collaboration, CryptPad for encrypted collaborative editing. Their published server/project licenses include AGPL; capabilities and operating models differ. | Optional candidates only; compare the exact version, edition, license, security model and supported integration before selection. |

Install placement follows responsibility, not the order in which a tool
was named: Cilium, secret infrastructure and Falco are separately
reviewed cluster/platform components after the Kubernetes engine;
Keycloak requires its own protected persistence and backup profile;
OPA is installed only when a policy-engine design selects it;
LGTM/Service Graph remains Layer 3; Trivy and SonarQube Community Build
belong to the build/security pipeline (with any server deployment
isolated from runtime traffic); Iceberg/Spark are optional analytics
capabilities outside the operational IoT request path. The tool catalog
currently includes some but not all of these candidates. Before any
new tool is selected by a deployable profile, add its edition, pinned
version, license, capabilities and four conformance checks to
`deploy/catalog/tools.yaml`; this ADR alone does not approve or install
it.

Job execution and business-workflow coordination are separate choices.
Payment-to-entitlement, firmware rollout and M9 migration cutover need
durable state, idempotency, audit and recovery; a function invocation or
Kubernetes Job alone is insufficient. A selected engine may coordinate
these processes through ports, while the owning services retain
authorization, invariants and source-of-truth state. Keep telemetry,
device commands and CDC on their existing paths rather than routing
every event through a BPMN engine.

Document collaboration is a separate optional capability. The work-order
service owns attachment metadata, tenant/resource authorization and
retention policy; a selected collaboration provider stores or presents
user documents behind a replaceable integration port. Technician access
must be scoped, time-limited where appropriate, audited and revoked on
role or assignment change. Collaboration shares are not the immutable
M6 evidence authority, firmware-artifact delivery path, device telemetry
store or backup system. If a document becomes regulated evidence, copy
it through the approved evidence ingestion path and verify retention and
integrity there. No collaboration provider is selected or installed.

## Every service enforces its own boundary

Every externally reachable service authenticates the caller at its own
trust boundary and authorizes each action against the authenticated
principal, tenant, resource and policy version. Internal service calls
also authenticate the workload (peer-authenticated TLS/mTLS under the
proposed Cilium ADR's independent proof gate)
and authorize the service action; network location or a successful
TLS handshake alone grants no business permission. REST, gRPC, events,
jobs and device-command adapters apply the same domain authorization
rules where relevant. A missing/invalid token, tenant mismatch,
unavailable required policy or secret, and forged gateway headers fail
closed. OPA can evaluate policy through a port, but cannot move the
service's enforcement responsibility to an untrusted edge.

## Required proofs before a tool/profile is called supported

Pin actual edition and version, verify license and support status,
exercise installation/upgrade/rollback and removal, and run its
behavioral/security conformance suite in an isolated target profile.
For OKD/OpenShift, prove the same service/API/tenant tests as RKE2 and
the SCC/storage/network/observability differences. For identity and
policy, test token rejection, cross-tenant access, mTLS peer identity,
policy outage and audit. For Falco/Trivy/SonarQube, distinguish detect,
scan and code-quality evidence; none is an authorization control. For
Iceberg/Spark, prove source lineage, tenant-isolated analytic reads,
backfill idempotency, resource limits and that failures cannot block
telemetry or commands.

## Primary references

- [OKD project](https://okd.io/docs/project/about/) and [community support](https://okd.io/docs/community/help/).
- [Hubble service map](https://docs.cilium.io/en/stable/observability/hubble/hubble-ui/) and [Grafana Tempo service graphs](https://grafana.com/docs/tempo/latest/metrics-from-traces/service_graphs/).
- [SonarQube Community Build repository](https://github.com/SonarSource/sonarqube), [Falco repository](https://github.com/falcosecurity/falco), [Apache Iceberg specification](https://iceberg.apache.org/spec/) and [Apache Spark](https://spark.apache.org/).
- [MinIO archived repository](https://github.com/minio/minio) and [OpenBao repository](https://github.com/openbao/openbao).
- [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/), [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/), [Flowable repository and license](https://github.com/flowable/flowable-engine), and [Camunda Self-Managed production licensing](https://camunda.com/pricing/).
- [Nextcloud Server licensing](https://github.com/nextcloud/server/blob/master/COPYING-README), [ownCloud Infinite Scale repository and build caveat](https://github.com/owncloud/ocis), [Seafile server license](https://github.com/haiwen/seafile-server/blob/master/LICENSE.txt), [Pydio Cells](https://github.com/pydio/cells), and [CryptPad](https://github.com/cryptpad/cryptpad).
