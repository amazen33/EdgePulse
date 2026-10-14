# ADR XXXX (proposed) -- Private-cloud lab profile: layered IaC, RKE2 on a single Hyper-V host behind NAT

Status: proposed. Unnumbered draft per `docs/adr/README.md`; the number is
assigned at merge. Records the decisions the `deploy/` tree encodes for the
**lab/development profile** `lab-hyperv-single-host`
(`deploy/profiles/lab-hyperv-single-host.yaml`). This is not a production,
highly available or scalable private cloud, and nothing here has been
applied past Layer 0 host preparation. Layering, the tool catalog, profiles
and vault/storage rules are governed by
`XXXX-proposed-deployment-layers-tool-catalog-and-profiles.md`.

Related: ADR 0011 (platform architecture), ADR 0013 (microservice autonomy),
ADR 0015 (observability authority), ADR 0019 (streaming and RAG).

## Context

The private cloud runs on a Windows machine with Hyper-V. The platform brief
places K3s on test/demo/edge and RKE2/OpenShift on the private cloud, and
asks for IaC-driven, vendor-neutral deployment in decoupled layers. CLAUDE.md
reserves `deploy/` for infrastructure code, and its development contract
forbids infrastructure, deploy or destructive actions without explicit human
approval.

A first version (PR #23) spread VMs across two hosts on bridged switches. It
is replaced by the layered, single-host design below.

## Decision

1. **Layers, each consuming only the previous layer's outputs** (the full
   five-layer model is in the deployment-layers ADR):
   - Layer 0 `deploy/00-infra/private-hyperv`: raw VMs (OpenTofu).
   - Layer 1 `deploy/01-k8s-engine/rke2-ansible`: OS preparation and the
     raw Kubernetes engine only (no meshes, messaging or workloads).
   - Layer 2 `deploy/02-cluster-addons`: cluster add-ons.
   - Layer 3 `deploy/03-observability` and Layer 4 `deploy/04-apps`:
     planned; nothing exists yet.

   Layer 0 publishes the node list as JSON and as an Ansible inventory
   (OpenTofu outputs), written to Layer 1's git-ignored
   `inventory/hosts.ini`, so nothing is copied by hand and no real
   inventory is committed.
2. **Layer 0 scope is raw VMs:** the host switch, NAT and template, then per
   VM a differencing OS disk over a read-only golden image, an empty data
   disk, and a Gen-2 VM with a static MAC. The only in-guest configuration is
   a cloud-init NoCloud seed with the hostname, the static IP and one SSH
   public key. That minimum is forced by the platform: Hyper-V cannot set a
   Linux guest's IP, and Windows NAT has no DHCP. No packages or commands run
   in Layer 0.
3. **Network: one host, Internal vSwitch + Windows NAT** (default
   10.20.0.0/24, host gateway .1). The VMs reach out through NAT. Inbound
   access is by explicit NAT static mappings only.
4. **Topology: 1 control-plane node + 2 workers** (`rke2-master-01`,
   `rke2-worker-01/02`). The node list is a keyed map. The Layer 0
   configuration (OpenTofu) accepts 1, 3 or 5 control-plane nodes, so
   control-plane HA *on one host* is a variable change; host-level HA is
   not (see Consequences).
5. **Distribution: RKE2** with embedded etcd, hardened in Layer 1:
   `profile: "cis"` on every node, the restricted Pod Security Standard
   enforced cluster-wide (system namespaces exempt), secrets encryption at
   rest, and a `CriticalAddonsOnly` taint on the server. Agents join with the
   node token extracted from the first server, which pins the cluster CA.
   Clients reach the API on the server's own address; there is no API VIP.
   **kube-vip** runs in Layer 2 as a services-only DaemonSet (ARP) for
   LoadBalancer Services, with addresses from kube-vip-cloud-provider.
6. **Hypervisor automation: the community `taliesins/hyperv` provider** over
   WinRM/HTTPS. VM checkpoints are disabled.
7. **Scaling is declared and human-applied, not autoscaled** (the node map
   lives in the git-ignored `terraform.tfvars`; only its example is in Git). The Kubernetes Cluster
   Autoscaler has no Hyper-V provider.
8. **Healing is tiered by risk.** systemd restarts RKE2. Restart, drain and
   uncordon need explicit confirmation. Node replacement is a documented
   manual procedure.
9. **Secrets never enter Git or state:** Hyper-V credentials via `TF_VAR_*`,
   the RKE2 join token via the environment and a vault. Only the SSH *public*
   key is read.
10. **Versions are pinned:** RKE2 stable channel, kube-vip, the cloud-provider
    manifest, the OpenTofu provider (`taliesins/hyperv`).

## Consequences

- **Lab/development only.** No control-plane HA and no host-level HA: one
  control-plane VM on one physical host. Losing either stops the API
  (running workloads continue). Accepted for lab and development; this
  profile must not be presented as production or as proof of a scalable
  private cloud.
- **Reachability is host-only by default.** LAN access to the API or a
  service needs a NAT static mapping, and the API certificate needs the
  host's name in Layer 1's `rke2_tls_san`.
- **No API VIP:** growing to 3 servers later means re-pointing clients (or
  adding a VIP/DNS name then). Accepted to keep Layer 1 free of add-ons.
- **Restricted PSS everywhere:** Layer 2+ components that need host access
  must run in an exempt system namespace or carry an explicit, reviewed
  namespace label.
- **Single server holds etcd alone:** recovery is an etcd snapshot restore
  with the same `RKE2_TOKEN`; snapshots must be copied off the VM.
- **Windows allows one NAT per host,** so this cannot coexist with another
  NAT (for example Docker Desktop's) on the same host without sharing its
  prefix.
- The IaC is outside the Maven build and has its own static CI gate
  (`.github/workflows/infra.yml`). Nothing in CI can reach the host.
- A community provider carries maintenance risk. Layer 0 is self-contained,
  so replacing the hypervisor or provider touches no other layer as long as
  the output contract is kept.

## Open items (not decided here)

- Multi-host layout (bridged/External switch or an overlay) and control-plane HA.
- Remote OpenTofu state with locking, once more than one operator applies.
- Argo CD installation and the chart layout: now Layer 4
  (`deploy/04-apps`), planned; no chart exists.
- Public-cloud (EKS/GKE/AKS) and OpenShift profiles as sibling Layer 0s
  (e.g. `deploy/00-infra/aws-eks`) behind the same output contract.
- Observability (ADR 0015's LGTM stack): now its own Layer 3
  (`deploy/03-observability`), planned.
- A bare-metal Layer 0 (servers without a hypervisor).

## Alternatives rejected

- **External (bridged) switch across two hosts** (PR #23's first version):
  replaced by the single-host NAT design. It returns under the multi-host
  open item.
- **DHCP instead of static IPs:** Windows NAT has no DHCP server, and running
  one adds a component; static addresses from a declared map are simpler and
  reproducible.
- **Per-VM baked images:** three images to maintain, and addresses not driven
  by variables.
- **Cluster Autoscaler with a custom provider for Hyper-V:** a bespoke
  component creating VMs without human approval, which conflicts with the
  development contract.
- **VM checkpoints for rollback:** rewinding an etcd member corrupts the
  cluster; rebuild instead.
- **`count`-based node list:** removing one node renumbers and rebuilds the
  others.
- **kube-vip static pod for an API VIP in Layer 1:** puts an add-on into the
  engine layer; the single server's address suffices for now.
