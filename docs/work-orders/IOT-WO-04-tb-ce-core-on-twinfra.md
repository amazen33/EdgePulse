# IOT-WO-04: ThingsBoard CE core on Twinfra (spike and first deployment)

**Status:** Draft, **gated**. Do not start until all of these hold:
- Twinfra WO-31 is accepted;
- WO-08 (OpenBao) is merged and live;
- WO-34 is merged;
- IOT-WO-01 and IOT-WO-02 are merged.

**Kafka is not needed here (owner question, 2026-10-14).**
- A single-node TB CE uses its in-memory queue (`TB_QUEUE_TYPE=in-memory`), which ThingsBoard ships as the default.
- Kafka is needed later for two things: IOT-EE's event path (milestone MS5) and TB's cluster mode (MS7). It arrives as a Twinfra platform service.
- The in-memory queue loses in-flight messages on a restart. That is acceptable for this dev milestone and is recorded in the receipt.

**Author:** Claude · **Implementer:** Codex · **Repositories:** IOT-EE (chart, values, tests, receipt) and Twinfra (only the Argo CD Application and image-lock entries, through Twinfra's own generators).
**Decisions:** ADR 0020, ADR 0021 and ADR 0022 (MR-2, MR-3, MR-8 and MR-9 checks). Twinfra ADR-0048 and ADR-0049.

## Goal

This produces IOT-EE's first level-R evidence: TB CE 4.3.1.x running on `cairo-1`, with the facts that ADR 0020 and ADR 0022 depend on checked against the real system.

## Scope

1. **Deploy, dev profile, single replica.**
   - Namespace `edgepulse-dev`, with default-deny ingress.
   - TB CE monolith at the newest 4.3.1.x patch that is at least 14 days old, digest-pinned, staged, licence-registered and passing the WO-32 gate.
   - **PostgreSQL comes from CNPG, not from ThingsBoard's bundled setups.** ThingsBoard's quick-start installs include a PostgreSQL container or expect a local PostgreSQL. On Twinfra, CNPG provides backups, point-in-time recovery, monitoring and later HA.
     - Check that the pinned TB release supports Twinfra's PostgreSQL 18, using ThingsBoard's own requirements for that release.
     - If it doesn't, run a **separate** CNPG cluster on the newest PostgreSQL major version that TB supports, pinned and staged the same way. Never downgrade the platform cluster.
     - The queue stays in-memory.
     - Valkey only if TB needs it.
   - Access is by laptop port-forward only: no NodePort, LoadBalancer, `hostNetwork` or `hostPort`.
   - **Memory budget:** TB at most 4 GiB and its PostgreSQL at most 2 GiB. Check this against the host budget left by the platform and WO-22, and stop and report if it doesn't fit.
2. **Identity.**
   - Log in to CE through OAuth2 with Keycloak. Use a separate realm `edgepulse` (ADR 0023), or a client in `twinfra`; recommend one.
   - Record the claim mapping and whether CE can map Keycloak roles to TB authorities.
   - Create a service-account API key and store it in OpenBao.
3. **Facts to verify (ADR 0020 and ADR 0022). Answer each with evidence:**
   - **a. Outbound Kafka.** Moved to MS5, which brings Kafka on Twinfra. Here, record only that the stock Kafka action node is present and accepted by the validator at this version.
   - **b. Import-safe chain.** IOT-WO-03's chain is accepted by `RuleChainDataValidator`.
   - **c. Rule-engine triggering.** Does posting telemetry and attributes through the tenant REST API trigger the rule engine? Test with and without the import-safe chain.
   - **d. Credentials at rest.** Which device-credential fields are stored in plain text in the database at this version? Read the schema; never print values.
   - **e. Upgrade rehearsal (Mode W).**
     1. Install an **older** TB CE release on a disposable CNPG database. Use the oldest release still downloadable from ThingsBoard's GitHub releases on the 3.x line, and record which.
     2. Load the synthetic dataset.
     3. Upgrade it to the pinned 4.3.1.x following ThingsBoard's documented upgrade steps, stepwise if they require it.
     4. Record the duration, each step, and the per-class counts and digests before and after (MR-7 digest spec).
   - **f. Backup and restore.** Run a CNPG backup and restore of the TB database, then reconcile counts.
   - **g. Throughput.** Record the historical telemetry import rate through the REST API under the import-safe chain (MR-8): rows per second at 1, 4 and 8 parallel clients.
4. **Receipt:** `docs/acceptance/tb-ce-core-on-twinfra-<date>.md`, with one section per fact (a–g), commands, results and the tester sign-off Pending.

## Out of scope

- High availability and cluster mode.
- The ingestion adapter and `ThingsBoardPort` (next work orders).
- Any real legacy data.
- Any public exposure.

## Owner actions

- Approve the namespace and memory budget.
- Approve the image digests.
- Run the live steps if Codex has no cluster access.
- Sign off as tester.

## Amendment 1 (owner, 2026-10-16): OpenShift-compatible packaging (ADR 0021 Amendment 1)

- The TB CE and EdgePulse charts follow ADR 0021 Amendment 1 from the start: arbitrary-UID-safe images and security contexts, portable Ingress and Service, a configurable storage class,
  and a `values-openshift.yaml` profile next to the default Twinfra profile.
- Add a CI job that renders the chart with the OpenShift profile and fails on any `restricted-v2` violation (fixed UID, host access, missing capability drop, missing seccomp).
- If the upstream ThingsBoard CE image cannot run under an arbitrary UID, record it as a finding with the minimal derived-image fix (group-0 permissions only, no functional change), and do not hard-code a UID.
- No live OKD run in this work order; that belongs to MS7.

## Amendment 2 (owner, 2026-10-16): hosting first — gates relaxed for the dev milestone

The owner made hosting EdgePulse on Twinfra the first target and postponed the other Twinfra work (Twinfra WO-39 enables it). The start gates of this work order become:
- **Required:** Twinfra WO-39 merged and applied; the day-one admission spike accepted by the owner; EdgePulse `main` contains this work order's chart location (see item 3).
- **Waived for this dev milestone:** Twinfra WO-31 owner acceptance, WO-08 (OpenBao live), the merge of every WO-34 part, and IOT-WO-02 (gates and Java baseline).
- **Changed items:**
  1. The API key from item 2 goes into a Kubernetes Secret `edgepulse-tb-api-key` (created by the owner through standard input, never in Git), not OpenBao. Moving it to OpenBao is part of Twinfra's postponed WO-08.
  2. Item 3f (backup and restore through CNPG) is replaced by a **manual `pg_dump` and restore** of the TB database to the laptop, recorded in the receipt. The CNPG scheduled backup arrives with WO-09 later.
  3. **Minimal IOT-WO-01 first:** push the decision records (ADR 0014 and 0020 to 0023), `MILESTONES.md` and these work orders to EdgePulse `main` through one small docs PR, so the repository states what it hosts. Do not merge the WIP snapshot branch.
  4. The image is `thingsboard/tb-node` (monolith service type) with an external CNPG PostgreSQL. Not `tb-postgres`.
  5. Everything else (facts a to g, the OpenShift-compatible packaging of Amendment 1, the receipt, the tester sign-off) stands.
- **No production claims.** Nothing here makes EdgePulse or Twinfra production-ready. The unrelated Foundation 1.0 rows resume after hosting.

## Amendment 3 (architect, 2026-10-18): local kind rehearsal before Twinfra v0.1.0

**Status:** Approved (owner, 2026-10-18, text as written). Container-engine change approved by the owner on 2026-10-18: Rancher Desktop is preferred, Docker Desktop is the alternative.
**Container engine:** kind needs a Docker-compatible engine. Use exactly one of these at a time; never run both.
- **Preferred: Rancher Desktop** (Apache-2.0) with the `dockerd (moby)` engine, not containerd, and its built-in Kubernetes (k3s) **off**.
- **Alternative: Docker Desktop** with its built-in Kubernetes **off**. It is a proprietary development tool, never shipped.
- **Fallback: Podman Desktop** (Apache-2.0).
- The built-in Kubernetes of any of them is never the test target: its distribution, CNI and ingress differ from `cairo-1`.
**Why:** Twinfra freezes `main` after WO-40b (about 10-31) and ships v0.1.0 around 11-09. WO-39 cannot merge before then, so EdgePulse can't be hosted yet. This amendment lets the chart and most of the facts be built and rehearsed now on a disposable local cluster that behaves like `cairo-1`, so that MS3 on Twinfra is mostly wiring plus the live run.
**Start gate:** IOT-WO-05 merged. It does not need any Twinfra work order. If IOT-WO-02 has merged first, its gates apply.

### What this is and isn't

- It is a **test harness**, not a deployment target and not EdgePulse-owned infrastructure. ADR 0021 still holds: Twinfra provides deployment. Nothing goes under the frozen `deploy/`.
- **Evidence level T (local).** A local run never becomes a milestone receipt and never answers an MS3 fact for the receipt. The MS3 receipt (`docs/acceptance/tb-ce-core-on-twinfra-<date>.md`) still needs `cairo-1`.
- **Off limits, unchanged:** the Hyper-V lab, its WSL controller, Twinfra (`E:/vCloud` may be **read** only, to copy versions and policies) and EdgeMig.

### Layout

| Path | Content |
| --- | --- |
| `charts/edgepulse-thingsboard/` | The TB CE chart. It is the one chart that Twinfra's Argo CD Application will track later (this is the "chart location" Amendment 2 refers to). It is namespaced only: no Namespace, no cluster-scoped resources, no CRDs (WO-39's AppProject forbids them). It holds the `tb-node` workload, its Service, the CNPG `Cluster` resource for the TB database, values for the Twinfra profile, `values-openshift.yaml` (Amendment 1) and `values-kind.yaml`. |
| `dev/kind/` | The harness: the kind cluster configuration, the pinned versions, the namespace baseline, and the scripts `up`, `install`, `smoke`, `down`. A README says "test harness only, not a deployment target, evidence level T". |
| `docs/rehearsals/` | Dated local rehearsal records, `tb-ce-kind-<date>.md`, each marked "Evidence level T (local kind). Not a receipt." |

### The cluster has to match `cairo-1`

1. **kind** pinned to an exact release at least 14 days old, its binary checked against the published SHA-256. The node image is pinned by digest to the Kubernetes minor version of Twinfra's kubeadm (v1.36.5 in WO-31). Use the closest 1.36 patch kind publishes, and record any difference.
2. **One control-plane node**, like `cairo-1`. Disable kind's default CNI, and install **Cilium** at the version and mode in Twinfra's lock and values (kube-proxy replacement or not), read from `E:/vCloud`.
3. **Namespace `edgepulse-dev`**, made by the harness, never by the chart, mirroring WO-39 item 3:
   - Pod Security `restricted` (enforce);
   - ResourceQuota and LimitRange inside WO-39's budget: TB at most 4 GiB, PostgreSQL at most 2 GiB;
   - default-deny ingress and egress, with exact allows for DNS, the TB database, and egress needed only for the install;
   - no NodePort, LoadBalancer, `hostNetwork` or `hostPort`.
4. **CNPG operator** pinned and installed by the harness, because on Twinfra it is a platform service. The chart's `Cluster` uses a configurable storage class: kind's `standard` locally, WO-39's Local PV on Twinfra. Check that the pinned TB release supports the PostgreSQL major version used, as item 1 says.
5. **Image** `thingsboard/tb-node`, the newest 4.3.1.x patch at least 14 days old, by digest. Not `tb-postgres`. Queue `in-memory`. Record the digest and the licence at the pinned tag. Scanning and admission remain WO-39's day-one spike on Twinfra; locally, the record says "not scanned" unless IOT-WO-02's gates exist.
6. **Access** through `kubectl port-forward` only.
7. **Secrets:** the database credentials come from CNPG's generated Secret. Any other Secret is created through standard input and never printed, committed or written to the record. ThingsBoard's default system-administrator login is changed after install, and the new value is never recorded.

### Safety rules for the scripts

- Every script refuses to run unless the current kube context is exactly `kind-edgepulse-dev`. `down` deletes only the kind cluster named `edgepulse-dev`.
- No script calls `wsl`, `Hyper-V` cmdlets, `docker system prune`, or anything outside that one cluster and its own containers.
- The engine's built-in Kubernetes stays **off**: Rancher Desktop's k3s, or Docker Desktop's Kubernetes. `up` refuses if the Docker context isn't the one engine in use, or if a second engine is running.

### What the rehearsal covers

| IOT-WO-04 item | Locally |
| --- | --- |
| 1 Deploy (dev profile, single replica, budget) | Yes |
| Amendment 1: arbitrary UID, `restricted-v2` render | Yes. Also run the chart with a random UID on kind |
| 2 Keycloak login, API key | No: needs Twinfra's Keycloak |
| 3a Kafka action node present and accepted | Yes |
| 3b Import-safe chain accepted | Only after IOT-WO-03 merges |
| 3c REST triggers the rule engine | Yes |
| 3d Credential fields at rest (schema only, never values) | Yes |
| 3e Upgrade rehearsal from the oldest downloadable 3.x | Yes, on a disposable database |
| 3f `pg_dump` and restore, count reconciliation | Yes |
| 3g Import throughput | Not recorded as a fact. Laptop numbers don't size `cairo-1` |

### CI

- Add a `kind-smoke` job that runs on changes to `charts/**` or `dev/kind/**`. It creates the cluster, installs CNPG and the chart, waits for TB to be ready, calls its health endpoint through a port-forward, and tears the cluster down. Actions are pinned by SHA (ADR 0014).
- It is not a required check yet. The owner decides after it is stable.
- Keep the Amendment 1 job that renders the chart with the OpenShift profile.

### Owner actions

1. Before the first `up`:
   - name the engine in use: Rancher Desktop (preferred) or Docker Desktop;
   - confirm it runs in its own WSL 2 distros (`rancher-desktop` or `docker-desktop`) with no link to the lab's WSL controller (`wsl -l -v`, read only), and that the other engine isn't running;
   - for Rancher Desktop, confirm the engine is `dockerd (moby)`;
   - confirm its built-in Kubernetes is off;
   - confirm about 10 GiB of memory is assigned;
   - for Docker Desktop only, confirm its subscription terms cover your use. No engine gets a licence-register entry, because none is shipped.
2. Approve each `up`, upgrade rehearsal and `down` (local, but a live action).
3. Review the rehearsal record. It isn't signed as a receipt.

### Out of scope

Argo CD (WO-39 wires it on Twinfra), Keycloak, OpenBao, Kafka, the ingestion adapter, LAN or device exposure, any real or legacy data, and any production or MS3 completion claim.
