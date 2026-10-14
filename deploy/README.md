# `deploy/`: infrastructure and releases, in five layers

Infrastructure-as-code for IOT-EE, split into five layers that are each
validated separately and applied separately by a human. Decisions:
`docs/adr/XXXX-proposed-deployment-layers-tool-catalog-and-profiles.md`
(layers, tool catalog, profiles, vault and storage) and
`docs/adr/XXXX-proposed-private-cloud-infrastructure.md` (the lab profile).

This tree is separate from the Java build: Maven never reads it. It has its
own static CI gate, `.github/workflows/infra.yml`, which cannot reach any
host, cluster or cloud account and never applies anything.

## The only implemented target is a lab

The code today targets **one** profile, `lab-hyperv-single-host`
(`profiles/lab-hyperv-single-host.yaml`): three Hyper-V VMs (one control
plane, two workers) on one Windows machine behind NAT. It is a
**lab/development profile**: not production, not highly available, not
bare metal, and not evidence of a scalable private cloud. Cloud profiles
(`profiles/cloud-*.yaml`) are **planned** until verified against real,
isolated accounts and clusters.

The planned `cloud-aws-eks-app-only` and `cloud-azure-aks-app-only` profiles
represent a second cloud deployment scope: release IOT-EE applications to an
**existing** cluster without installing our infrastructure, Kubernetes
engine, cluster add-ons, or observability stack. Layers 0-3 are explicitly
`not-applicable`; the cluster operator supplies them and the identity,
secrets, database, event stream, object storage, ingress, observability, and
GitOps capabilities. The profile records only configuration references and
pending readiness checks, never credentials. A profile cannot become
validated or approved until each external dependency has passed with
evidence, the vault/storage restore and tool checks pass, and Layer 4's
charts and release checks exist. These profiles are plans, not deployable
artifacts or proof of AWS/Azure compatibility.

Cilium with Hubble and Istio Ambient are candidate options awaiting a
profile-level decision (proposed Cilium/Ambient ADR). Neither is installed
or selected by a validated profile. They may coexist only after specific
compatibility and policy-ownership tests. The existing RKE2 CNI and kube-proxy settings,
LoadBalancer interaction, workload authentication and encryption need
separate review before a Layer 1/2 change. Application-only profiles do
not install a CNI; their external cluster must prove network policy,
service routing, peer authentication and transport encryption.

OKD is a proposed fully open-source Kubernetes alternative and Red Hat
OpenShift Container Platform an optional commercial/support profile in
`catalog/tools.yaml`. Neither has a deployment profile or installation
artifact here. They require separate infrastructure and application
conformance; Grafana/Tempo topology visualization works independently of
that choice. See
`docs/adr/XXXX-proposed-kubernetes-options-and-platform-tool-roles.md`.
The [private-cloud platform options ADR](../docs/adr/XXXX-proposed-private-cloud-platform-options.md)
sets the target common CAPI management plane over CloudStack, OpenStack
and Metal3 bare metal, with OKD/Machine API/OCM and
Harvester/Rancher/RKE2 as independent alternatives. None has a
deployable profile here.

## Layers

| Layer | Path | Tool (proposed default) | Owns | Hands over | Static check (CI) | State |
| --- | --- | --- | --- | --- | --- | --- |
| 0 Infrastructure provisioning | `00-infra/private-hyperv/` | OpenTofu (+ PowerShell host prep) | Hyper-V switch, NAT, template; VMs, disks, static IPs | `ansible_inventory_ini`, `nodes_json` outputs | `tofu fmt`, `tofu validate`, PowerShell parse | Lab target implemented (`windsorcli/hyperv` 0.4.0); 3 VMs created and checked on the lab host, 2026-09-27 |
| 1 OS hardening + Kubernetes | `01-k8s-engine/rke2-ansible/` | Ansible (`ansible.builtin` only) | OS settings, RKE2 (CIS profile, restricted PSS, secrets encryption), health, healing | admin kubeconfig | syntax check, builtin-only rule, inventory validation + negative fixtures | Implemented; run on the lab host 2026-09-27 (3/3 nodes Ready) |
| 2 Cluster add-ons | `02-cluster-addons/` | Kustomize | kube-vip services-only LoadBalancer + pool | LoadBalancer Services | kustomize render + kubeconform | Implemented; never applied |
| 3 Observability and topology | `03-observability/` | LGTM + OpenTelemetry Collector, Tempo Service Graph | Logs, traces, metrics, service dependencies | Synthetic OTLP ingest/query and service-graph edge before application instrumentation | none (no artifacts) | **Planned; nothing exists** |
| 4 Application release | `04-apps/` | Helm charts + Argo CD | Service releases via GitOps | -- | none (no artifacts) | **Planned; no Helm chart exists** |

Each layer knows only the previous layer's outputs: Layer 0 knows nothing
about Kubernetes, and Layer 1 knows nothing about Hyper-V beyond the
inventory.

**Provisioning tool.** OpenTofu (MPL-2.0) is the default. Terraform is an
optional compatibility choice only: HashiCorp moved it to BSL 1.1 for all
releases after 2023-08-10, which is not an OSI open-source licence. Layer 0
avoids syntax only one of them accepts, but CI runs OpenTofu only, and
Terraform may be used only after the owner records acceptance of its
licence in the tool catalog.

## Tool catalog and profiles

- `catalog/tools.yaml` -- the curated, versioned list of tools a profile may
  select: licence and licence class, role (default, alternative,
  optional-compatibility, lab-only, test-only, rejected), versions pinned in
  this repository, capabilities (per edition where editions differ),
  commercial alternatives, and four checks (compatibility, support,
  licence, security). Defaults must be OSI open source. **No tool is
  approved yet**: most checks are still pending.
- `profiles/*.yaml` -- deployment profiles (lab, planned, validated,
  approved, retired) selecting catalog tools by id and version, with a
  vault profile and storage classes.
- `catalog/validate.py` -- validates both against
  `contracts/deploy/*.schema.json` plus cross-field rules; 49 unit tests in
  `catalog/tests/` cover valid profiles and planted violations. Run locally with
  `python deploy/catalog/validate.py` (needs `pyyaml` and `jsonschema` >= 4.0).
- `checks/static_guards.py` -- repository guards (15 unit tests in
  `checks/tests/`): no node addresses, groups or inline host lists in
  `ansible.cfg`; only RFC 5737 documentation addresses in committed Layer 1
  inventory and variable files; no `ansible-playbook -e`/`--extra-vars` in
  documented or scripted commands; README and profile claims about Helm
  charts and implemented layers must match the files that exist.

Rules the validator enforces: profiles select only catalog tools; a
`validated` or `approved` profile needs approved, pinned tools and a passed
real-environment verification; `approved` needs a system-admin approver who
is not the author; cloud profiles cannot be `lab`; `production_use` needs
HA; the vault profile states its storage backend, replicas and spread,
unseal method with a key reference (never key material) and custody,
backup method, retention, target and restore status, and a data-loss
effect, and the selected edition must declare every one of those
capabilities (for example, HashiCorp Vault community has no namespaces,
automated snapshots or PKCS#11 seal; OpenBao declares namespaces only from
2.3); Spring Vault is a client and can never be a backend;
storage classes need quotas, key references (never key material), backup
and restore status, topology, reclaim policy, retention and an explicit
data-loss effect; a cloud profile may reference only its own provider's
KMS. Profiles cannot carry commands: the schema forbids extra
fields.
For `applications-only`, the validator also rejects Layer 0-3 installation
paths, infrastructure tool selection, missing external ownership of vault
and storage, incomplete dependency roles, and readiness claims without
evidence.

**Selection is plan-and-review.** A system admin selects approved tools and
profiles through Deployment Studio's plan lifecycle (ADR 0009); nothing in
this tree, the GUI or Deployment Studio turns natural-language input into
Ansible tasks or exposes unrestricted infrastructure commands. Only
reviewed, versioned artifacts from Git are run, with parameters defined by
the schemas.

## Sequence of operations (lab profile)

Nothing below is run by CI or by an agent: each step is a human action
with explicit approval.

### Layer 0: VMs

Follow `00-infra/private-hyperv/README.md`: prepare the host once
(`scripts/prep-hyperv-host.ps1`), `tofu plan` and `tofu apply`, then write
the inventory to Layer 1's **git-ignored** `inventory/hosts.ini`:

```powershell
cd deploy\00-infra\private-hyperv
tofu output -raw ansible_inventory_ini | Set-Content -Encoding utf8 ..\..\01-k8s-engine\rke2-ansible\inventory\hosts.ini
```

### Layer 1: OS hardening and the Kubernetes engine

Full guide: `01-k8s-engine/rke2-ansible/README.md`. From WSL 2 (Ubuntu) on
the Hyper-V host, in the repository:

```bash
cd deploy/01-k8s-engine/rke2-ansible
ansible-playbook -i inventory/hosts.ini validate-inventory.yml        # contacts no host
awk -F'ansible_host=' '/ansible_host=/{split($2,a," "); print a[1]}' inventory/hosts.ini \
  | xargs -n1 ssh-keyscan -H >> ~/.ssh/known_hosts                    # verify fingerprints on first use
export RKE2_TOKEN="$(openssl rand -hex 32)"                           # first run only; keep it in your vault
ansible-playbook -i inventory/hosts.ini site-rke2.yml
```

Site-specific values (for example `rke2_tls_san`) go in the git-ignored
`inventory/group_vars/all/local.yml` or `inventory/host_vars/`, never in
`-e` extra vars, which outrank every reviewed default.

### Layer 2: add-ons

```bash
kubectl apply -k deploy/02-cluster-addons
kubectl -n kube-system rollout status deploy/kube-vip-cloud-provider
kubectl -n kube-system rollout status ds/kube-vip-ds
```

Smoke test: `kubectl create deployment web --image=nginxinc/nginx-unprivileged`,
then `kubectl expose deployment web --port 80 --target-port 8080 --type LoadBalancer`.
`kubectl get svc web` should show an EXTERNAL-IP from the lab pool that
answers from the host. (The stock `nginx` image runs as root and is rejected
by the restricted Pod Security Standard, which is the point.)

### Layers 3 and 4

Not available: see `03-observability/README.md` and `04-apps/README.md`
for what must exist before either can run.

## Reaching services from the LAN (lab profile)

Everything sits behind the host's NAT. Publish what you need with a static
mapping (elevated PowerShell on the host):

- **Kubernetes API:** `.\scripts\prep-hyperv-host.ps1 -ApiServerForwardTo <control-plane address>`,
  then add the host's LAN name to `rke2_tls_san` in
  `inventory/group_vars/all/local.yml` and re-run `site-rke2.yml`.
- **A LoadBalancer service:** `Add-NetNatStaticMapping` from a host port to
  the service's EXTERNAL-IP, plus a matching inbound firewall rule.

## Day 2 (lab profile)

- **Scaling** is declared and reviewed, not autoscaled: add or remove an
  entry in Layer 0's `nodes` map (in the git-ignored `terraform.tfvars`), `tofu apply`, regenerate the inventory, validate it, then
  `ansible-playbook -i inventory/hosts.ini site-rke2.yml --limit <first server>,<new node>`.
  There is no Cluster Autoscaler (no Hyper-V provider).
- **Health** (read-only, safe to schedule):
  `ansible-playbook -i inventory/hosts.ini health.yml` writes a JSON report
  to `01-k8s-engine/rke2-ansible/reports/`.
- **Healing** needs `--limit <node>`, exactly one action tag
  (`--tags restart|drain|uncordon|replace`) and typing the node name at the
  prompt; `replace` only prints the rebuild steps. See the Layer 1 README.
- **Upgrades:** change `rke2_version` in
  `01-k8s-engine/rke2-ansible/inventory/group_vars/all/main.yml` and its
  catalog entry in one PR; run servers first, then agents; one minor
  version at a time.

## Verification status

CI (`infra.yml`, static only): `tofu fmt`/`validate` (Layer 0); Ansible
syntax check, builtin-only rule, example inventory accepted, five
negative fixtures rejected, and the example inventory rejected for a live
run (Layer 1); PowerShell parse; kustomize render + kubeconform (Layer 2);
catalog and profile validation plus unit tests; repository guards plus
unit tests. Layers 3 and 4 have no artifacts to check, and the guards fail
if anything claims they do.

Static checks re-run outside CI on 2026-09-26 (a Linux sandbox, no host,
cluster or cloud access): catalog/profile validation and 41 tests,
guards and 15 tests; `ansible-playbook --syntax-check` for all five
playbooks, example inventory accepted, five fixtures rejected for the
intended reason, example inventory rejected in live mode (ansible-core
2.18.9); `tofu fmt -check` (OpenTofu 1.10.6); kubeconform `-strict` on the
Layer 2 manifests and the pinned kube-vip-cloud-provider v0.0.12 manifest.
`tofu init`/`validate` could not run there (provider registry unreachable)
and remain covered by CI only.

Real-environment record (one layer at a time; add each run here):

| Step | Status | Evidence |
| --- | --- | --- |
| Layer 0 host preparation (`scripts/prep-hyperv-host.ps1`) | Run once, 2026-09-25, on the owner's Hyper-V host: completed after the fixes in PR #28 | Console output reported by the owner; the template's size and read-only flag were not independently checked |
| Layer 0 host preparation, E: volume | Run 2026-09-27 after the lab moved from D: (D: filled during the RKE2 install and Hyper-V paused, then turned off, the workers) | Owner-run; output reviewed in the session. Template on E: read-only, same size as the D: build |
| Layer 0 `tofu apply` (VMs), `windsorcli/hyperv` 0.4.0 | **Passed (lab)**, 2026-09-27: 15 added; 3 VMs running, checkpoints disabled, every disk on E:; SSH answered on all three | Owner-run; output reviewed in the session |
| Layer 1 `site-rke2.yml` (RKE2, CIS profile) | **Passed (lab)**, 2026-09-27: PLAY RECAP `failed=0` on all nodes; 3/3 nodes `Ready` on `v1.35.7+rke2r1`; no pods outside Running/Succeeded | Owner-run from WSL; output reviewed in the session. `health.yml` report and the hardening checks in the Layer 1 README not yet reviewed |
| Layer 2 add-ons (`kubectl apply -k deploy/02-cluster-addons`) | **Not run** (the cluster now exists) | -- |
| Layer 3 observability | **Planned**; no artifacts | -- |
| Layer 4 applications (Helm + Argo CD) | **Planned**; no chart exists | -- |
| Cloud profiles (EKS/AKS/GKE), including AWS/Azure application-only | **Planned**; no cloud deployment code, account or cluster | Static profile validation only |
| Bare-metal Layer 0 | **Planned**; no code | -- |

Nothing above is a production, HA or DR claim.
