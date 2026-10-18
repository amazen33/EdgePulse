# ADR 0021: IOT-EE runs on Twinfra, under Twinfra's licence gate

**Status:** Accepted (owner).
- The owner directive "IOT-EE on Twinfra" was given on 2026-10-12.
- Decision D-2 was taken on 2026-10-14: Twinfra's licence gate applies to IOT-EE.
- Ordering follows the architect's recommendation, which the owner delegated on 2026-10-14: hosting starts after Twinfra WO-08.

The number is confirmed at merge.

**Author:** Claude (architecture). **Implementer:** Codex (IOT-WO-01, IOT-WO-02).

**Supersedes:**
- ADR 0011 Decision 3: the mandatory infrastructure stack, with its OpenTofu, Ansible and RKE2 parts.
- ADR 0015's Layer 3 LGTM installation: the trace and log authority moves to Twinfra's observability baseline.

**Withdraws (unmerged drafts):**
- `XXXX-proposed-private-cloud-infrastructure.md`
- `XXXX-proposed-private-cloud-platform-options.md`
- `XXXX-proposed-kubernetes-options-and-platform-tool-roles.md`
- `XXXX-proposed-deployment-layers-tool-catalog-and-profiles.md`
- `XXXX-proposed-cilium-network-and-workload-security.md`
- `XXXX-proposed-observability-installation-sequence.md`

## Context

IOT-EE planned its own five infrastructure layers:
- OpenTofu Hyper-V VMs;
- RKE2 through Ansible, with kube-vip;
- add-ons;
- LGTM;
- Helm and Argo CD.

That duplicates Twinfra, which already runs on `cairo-1`:
- kubeadm and Cilium;
- CNPG PostgreSQL 18 with pgvector;
- Keycloak, OpenBao, APISIX and Argo CD;
- the Prometheus, OpenTelemetry and Perses observability baseline (ADR-0034);
- the supply-chain gate (ADR-0049).

Several of IOT-EE's defaults also fail Twinfra's licence gate (Twinfra ADR-0030 and ADR-0044). That gate allows permissive licences, plus unmodified MPL-2.0 as a recorded weak-copyleft class.

## Decision

1. **Twinfra is IOT-EE's platform.**
   - IOT-EE ships application artifacts only: images, Helm charts and Argo CD Applications.
   - Twinfra's Argo CD deploys them into IOT-EE namespaces with default-deny ingress.
   - Development runs on `cairo-1`. Production high availability follows Twinfra's multi-node plan (Twinfra ADR-0050 and WO-33).
2. **IOT-EE's own infrastructure is frozen, not extended.**
   - `deploy/00-infra`, `deploy/01-k8s-engine`, `deploy/02-cluster-addons` and `deploy/03-observability`, together with the catalog and profiles, are tagged `archive/iot-ee-own-infra` and marked frozen.
   - They are deleted only by a later work order, after IOT-EE runs on Twinfra.
   - The pCloud copy of that infrastructure is a separate matter and is not touched.
   - `deploy/04-apps` (Helm and Argo CD) stays and is the only deployment path.
3. **The licence gate applies to everything IOT-EE runs, ships or builds with.**
   - The rules are Twinfra ADR-0030, ADR-0042 and ADR-0044: classes, SPDX evaluation, the baseline and ratchet, and evidence from the exact pinned version.
   - IOT-EE keeps its own register, `security/licence-register.*`, with the same schema and checker. Its CI fails on unregistered or blocked components.
   - The ThingsBoard CE image and its bundled dependencies are registered at image level, like Twinfra's third-party images.
4. **Replacements:**

   | Was | Licence | Becomes |
   | --- | --- | --- |
   | OpenTofu, Ansible, RKE2, kube-vip | MPL-2.0, GPL-3.0, Apache-2.0 | Twinfra's kubeadm platform; not used by IOT-EE |
   | Grafana, Loki, Tempo, Mimir | AGPL-3.0 | Twinfra ADR-0034: Prometheus, OpenTelemetry Collector, Jaeger and Perses |
   | HashiCorp Vault | BUSL-1.1 | OpenBao (MPL-2.0, unmodified, as on Twinfra) |
   | MinIO | AGPL-3.0, archived | S3 through Twinfra's SeaweedFS (Twinfra WO-22). WORM still needs an Object Lock conformance run (IOT-EE ADR 0010) |
   | EMQX | BUSL-1.1 | Not used. TB CE's MQTT transport is the device endpoint (ADR 0020) |
   | Mosquitto | EPL-2.0 | Not used. If legacy devices need a separate broker, candidates such as HiveMQ CE and NanoMQ go through the gate first |
   | Redpanda (conformance target) | BUSL-1.1 | Dropped. Broker conformance runs on Apache Kafka only |
   | Trivy | Apache-2.0, but compromised (CVE-2026-33634) | Grype, Syft and OSV-Scanner (ADR 0014) |
   | Kafka | Apache-2.0 | Apache Kafka on Twinfra through Strimzi (Twinfra ADR-0014 and ADR-0015). They must be Accepted and implemented before IOT-EE needs Kafka |

5. **The runtime baseline**, applied by IOT-WO-02:
   - Java 21 LTS, matching TB CE 4.3's runtime, so there is one JDK line to patch.
   - The newest Spring Boot and Spring Cloud release train that is in open-source support and at least 14 days old. Its support dates are checked at pin time.
   - Build and quality tools go through the gate like runtime components.
6. **Secrets.**
   - OpenBao on Twinfra (Twinfra WO-08) holds every IOT-EE secret, including TB CE API keys and migration-run credentials (ADR 0022).
   - Workload identity follows Twinfra's pattern. No secret goes into Git, events, logs or evidence; `CLAUDE.md` is unchanged on this.

## Consequences

- About half of IOT-EE's 22 draft ADRs are withdrawn. IOT-EE's decisions become application-level only.
- IOT-EE depends on Twinfra delivering several things:
  - **OpenBao** (WO-08) before the first deployment;
  - **Kafka through Strimzi** before the ingestion adapter;
  - **SeaweedFS** (WO-22) before evidence and object storage.

  These are now on Twinfra's critical path for IOT-EE.
- IOT-EE's Hyper-V lab and its WSL controller are no longer IOT-EE's target. They are left untouched, and their retirement is a separate owner decision.
- `CLAUDE.md`'s stage checklist changes:
  - "Deployment artifacts (OpenTofu, Ansible …)" becomes "Helm chart and Argo CD Application for Twinfra".
  - The Trivy paragraph is replaced by ADR 0014.

## Cross-references

- IOT-EE ADRs 0011, 0014, 0015 and 0020.
- Twinfra ADR-0030, ADR-0034, ADR-0044, ADR-0048, ADR-0049 and ADR-0050, ADR-0014 and ADR-0015 (Kafka and Strimzi), and WO-08 and WO-22.
- The review `E:\vcloud-handoff\reviews\iot-ee-review-2026-10-14.md`, section 3.3.

## Amendment 1 (owner, 2026-10-16): OpenShift-compatible packaging

**Principle.** EdgePulse is hosted on Twinfra, but it is **packaged to run unchanged on OpenShift and OKD** as well, because many enterprise customers run them.
Twinfra stays the hosting platform; OpenShift is a **compatibility target**, not a host (the architect's assessment of 2026-10-16:
- a single-node OKD cluster cannot later become HA;
- OKD has community support only;
- moving would discard the Twinfra evidence).

Rules for every EdgePulse workload and chart:
1. **Security context passes OpenShift `restricted-v2` and Kubernetes Pod Security `restricted`:**
   - non-root, and **no fixed UID or GID** (it runs under any arbitrary UID with group 0);
   - no host paths, host network, host ports or privilege escalation;
   - all capabilities dropped; `seccompProfile: RuntimeDefault`.
   Images make writable paths group-0 writable (`chgrp 0` and `chmod g=u`).
2. **Portable networking and storage:**
   - standard `Ingress` and `Service` only (Gateway API optional); no OpenShift-only `Route` objects in the base, though an optional OpenShift overlay may add them;
   - storage through a configurable `storageClassName`, with no node-local assumptions in the base chart.
3. **Packaging.** One Helm chart (and later, optionally, an operator) with a values profile per platform: `twinfra` (default) and `openshift`. No platform conditionals in application code.
4. **Dependencies through standard interfaces:** PostgreSQL by connection Secret (CNPG on Twinfra; any compatible operator or service elsewhere), OIDC by issuer URL (Keycloak on Twinfra), secrets by Kubernetes Secret or External Secrets.
5. **Evidence:**
   - CI renders the chart with the `openshift` profile and checks it against the `restricted-v2` rules statically on every PR;
   - a live compatibility run on a local OKD (CodeReady Containers with the OKD preset; no Red Hat account needed) is part of MS7 (production readiness) and records a receipt.
   - Nothing is claimed about OpenShift support until that receipt is Accepted.
