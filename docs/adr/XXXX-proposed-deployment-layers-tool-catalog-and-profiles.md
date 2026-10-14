# ADR XXXX (proposed) -- Deployment layers, tool catalog and deployment profiles: five separately validated layers, OpenTofu by default, approved tools only, explicit vault and storage profiles

Status: proposed. Unnumbered draft per `docs/adr/README.md`; the number
is assigned at merge. Encodes deployment direction given by the repository
owner on 2026-09-26. Default tool choices are **proposed** and need the
owner's confirmation; none is approved yet because no tool has passed all
four catalog checks.

Extends ADR 0009 (Deployment Studio): its profile fields (environment,
provider, region, tier) are reused, and ADR 0011 Decision 7's topology is
added. ADR 0009 treated profile capabilities as declarative labels with no
validation; this ADR validates them against a curated catalog. Refines the
draft `XXXX-proposed-private-cloud-infrastructure.md`, which now describes
the lab/development profile only. ADR 0009 is not edited.

## Context

- `deploy/` had three layers (VMs, RKE2, add-ons) and no place for
  observability or application releases. **No Helm chart exists** in the
  repository.
- The only deployment target is one Windows Hyper-V host with one control
  plane VM. It was not labelled as a lab profile, and nothing said that
  cloud targets are untested.
- Layer 1 committed its real inventory (private node addresses) and used
  `-e` extra vars for a privileged confirmation (`heal_confirm=yes`) and for
  site overrides. Extra vars have the highest precedence in Ansible and
  silently override every reviewed default.
- Licences: HashiCorp moved Terraform and Vault to BSL 1.1 for all releases
  after 2023-08-10 (HashiCorp press release); EMQX moved to BSL 1.1 from 5.9;
  the `minio/minio` repository was archived on 2026-04-25 and is no longer
  maintained. OpenBao (a Vault fork, MPL-2.0 per its repository) joined the
  OpenSSF as a sandbox project in 2025-06; it added namespaces in 2.3 (beta
  2025-05-28). Vault's automated integrated-storage snapshots require an
  Enterprise licence.
- The vault profile named a backend, edition and required capabilities
  only. It did not say how the backend stores data, how it is unsealed and
  by which key, how it is backed up, or what is lost when any of those
  fail -- the same questions the storage profile already had to answer.
- Spring Vault is a Java client library for the Vault HTTP API. Earlier
  wording could be read as if it were a secrets backend.

## Decision

1. **Five layers, each separately validated.** Each consumes only the
   previous layer's outputs and has its own static CI check
   (`.github/workflows/infra.yml`); none is applied by CI.

   | Layer | Path | Tool (proposed default) | Owns | Static check | State |
   | --- | --- | --- | --- | --- | --- |
   | 0 Infrastructure provisioning | `deploy/00-infra/<target>` | OpenTofu | Machines/VMs, disks, networks, node inventory output | `tofu fmt`, `tofu validate`, PowerShell parse | Lab target (`private-hyperv`) implemented; bare-metal and cloud targets planned |
   | 1 OS hardening + Kubernetes engine | `deploy/01-k8s-engine/<distribution>-ansible` | Ansible (`ansible.builtin` only) | OS settings, RKE2 with CIS profile, restricted PSS, secrets encryption | syntax check, builtin-only rule, inventory validation with negative fixtures | Implemented, never run against real hosts |
   | 2 Cluster add-ons | `deploy/02-cluster-addons` | Kustomize (today) | LoadBalancer (kube-vip), later storage, backup, ingress plumbing | kustomize render + kubeconform | Implemented, never applied |
   | 3 Observability | `deploy/03-observability` | LGTM + OTel Collector | Logs, traces, metrics | none yet | Planned; nothing exists |
   | 4 Application release | `deploy/04-apps` | Helm charts + Argo CD (current named controller) | Service charts and GitOps sync | none yet | Planned; **no chart exists** |

2. **OpenTofu is the default provisioning tool** (MPL-2.0). Terraform is an
   **optional compatibility choice**, not an open-source default: Layer 0
   code stays within syntax both accept, but Terraform may be used only
   after the owner records acceptance of its BSL licence in the catalog.
3. **Ansible inventory and variables.**
   - A checked-in *example* inventory (`inventory/hosts.example.ini`) uses
     RFC 5737 documentation addresses only. The real inventory
     (`inventory/hosts.ini`) is generated from Layer 0's output or written
     locally, and is git-ignored, as are `inventory/host_vars/` and
     `inventory/group_vars/all/local.yml`.
   - Node addresses and groups live only in inventory, `group_vars` and
     `host_vars` (or an approved dynamic inventory plugin, none approved
     yet) -- never in `ansible.cfg`.
   - `validate-inventory.yml` checks group shape (1/3/5 servers, at least
     one agent, no overlap), host names, IPv4 addresses, uniqueness and a
     non-root user before any host is contacted; `site-rke2.yml` runs the
     same checks first and additionally rejects documentation addresses.
   - No `-e` extra vars for privileged switches or site overrides. Site
     values go in the git-ignored override files. `heal.yml` takes its
     action as a tag and needs the operator to type the node name.
     Security-critical values (the Pod Security exemption list) are
     asserted against the reviewed value, so an override fails the run.
4. **Profiles and their status.** A deployment profile
   (`deploy/profiles/*.yaml`, schema `contracts/deploy/deployment-profile.schema.json`)
   has a status: `lab`, `planned`, `validated`, `approved` or `retired`.
   - The single-host Hyper-V target is the **lab/development profile**
     `lab-hyperv-single-host`: environment `dev`, not production, not HA,
     not evidence of a scalable private cloud.
   - Cloud profiles (EKS, AKS, GKE) are **planned** until verified against
     real, isolated accounts and clusters; a cloud profile cannot be `lab`.
   - `applications-only` is a distinct planned cloud scope for an existing
     EKS/AKS environment. Layers 0-3 have no installation paths; Layer 4
     consumes externally managed Kubernetes, identity, secrets, relational
     database, event stream, object storage, ingress, observability and
     GitOps capabilities. Each binding is a configuration reference, not a
     credential or command. The validator requires every role exactly once,
     external ownership of vault and storage, and passed evidence for every
     dependency before the profile can be validated or approved. The AWS
     and Azure examples remain planned; they do not prove compatibility or
     authorize any cloud action.
   - `validated`/`approved` need approved, pinned tools and at least one
     passed real-environment verification. `production_use` needs
     `approved`, `high_availability`, at least three control-plane nodes and
   host redundancy.

   OpenStack is a candidate **additional Layer 0 provider profile** for
   a multi-host private cloud or a provider-operated OpenStack cloud.
   Its compute, network and storage APIs can provision the Kubernetes
   nodes; Layer 1 and later layers should consume the same versioned
   inventory/capability outputs as other providers. It is not selected
   or deployed by this ADR. A self-managed OpenStack cloud still depends
   on our physical hosts, networking, storage, power and operations;
   a provider-operated cloud transfers some infrastructure operations
   to that provider under an explicit SLA. Neither choice makes the
   application itself highly available without separate Kubernetes,
   data, backup and disaster-recovery proofs. Evaluate OpenStack only
   against a concrete need for shared multi-host capacity, API-driven
   VM/network/storage provisioning, isolation or self-service. Compare
   staffing, lifecycle upgrades, support, cost, failure domains,
   storage/network design and recovery with a simpler multi-host
   Kubernetes deployment before approval. Preserve the single-host
   Hyper-V profile for lab work; it is no production baseline. See
   [OpenStack's software overview](https://www.openstack.org/software/)
   and [Kolla Ansible's deployment guide](https://docs.openstack.org/project-deploy-guide/kolla-ansible/latest/index.html)
   for the infrastructure scope and operating surface.
   The target common CAPI management plane evaluates CloudStack, OpenStack
   and Metal3 bare-metal infrastructure providers for separate workload
   Kubernetes clusters. Harvester/Rancher/RKE2 and OKD/Machine API/OCM are
   independent candidate profiles. RKE2 on CAPI requires a verified
   bootstrap/control-plane provider. See the
   [private-cloud platform options ADR](XXXX-proposed-private-cloud-platform-options.md)
   for boundaries, recommendation and evidence gates.
5. **Curated, versioned tool catalog** (`deploy/catalog/tools.yaml`, schema
   `contracts/deploy/tool-catalog.schema.json`). Each tool records category,
   licence and licence class, role (default, alternative,
   optional-compatibility, lab-only, test-only, rejected), versions pinned
   in the repository, capabilities (per edition where editions differ),
   commercial alternatives, and four checks: compatibility, support,
   licence, security. A default must be OSI open source; `approved` needs
   all four checks passed. Proposed defaults: Ubuntu Server LTS, RKE2,
   OpenTofu, Ansible, Helm, Argo CD, APISIX, Apache Kafka, Mosquitto, LGTM +
   OTel Collector, OpenBao, Longhorn, Velero, kube-vip.
6. **Selection is plan-and-review, by system admins only.** Only a system
   admin (ADR 0016 `PRODUCT_ADMIN`) may approve a profile, and the approver
   must differ from its author (ADR 0009 plan lifecycle; proposed roles
   ADR). Profiles select catalog tools by id and version; they cannot carry
   commands, scripts or free text that is executed (the schema forbids
   additional properties). Deployment Studio and any GUI **never** translate
   natural-language input into Ansible tasks or shell commands and never
   expose unrestricted infrastructure commands: they may only run reviewed,
   versioned artifacts from Git with parameters defined by these schemas.
7. **Vault profile.** A profile names a secrets **backend** and its
   **edition**, the capabilities it requires, an optional **client**, and
   the reference scheme for secrets. It also states:
   - **storage backend** (`integrated-raft` or `provider-managed`) and
     **topology** (1, 3 or 5 replicas; node or zone spread when more than
     one; production needs at least 3);
   - **unseal**: the method (`shamir`, cloud-KMS, transit, PKCS#11, KMIP or
     provider-managed), a **key reference** for every auto-unseal method
     (the profile's own provider KMS for cloud KMS, never key material, and
     none for Shamir), and who has custody of the key shares or key;
   - **backup**: method (manual or automated raft snapshots, or
     provider-managed), schedule, retention, a target reference and
     whether a restore was tested; usable profiles need backups and a
     tested restore;
   - an explicit **data-loss effect**, which must cover losing the unseal
     keys or KMS key, a single replica, manual-only snapshots, a missing
     backup and an untested restore.

   The storage backend, unseal method, backup method and every required
   capability must be declared by that **edition** in the catalog, so
   nothing is assumed from the product name. Only references are stored,
   never secret values.
   - OpenBao (MPL-2.0) is the proposed open-source default. Its community
     edition declares integrated raft storage, manual raft snapshots,
     Shamir, cloud-KMS, transit, PKCS#11 and KMIP unseal, and namespaces
     (2.3+; a profile relying on them must pin >= 2.3 and verify). No
     automated snapshot capability is declared.
   - HashiCorp Vault is BSL 1.1 for current releases, so it is not
     universally open source: it is an optional-compatibility choice with
     explicit editions. Community: no namespaces, replication, automated
     snapshots or PKCS#11 seal. Enterprise adds them. HCP is
     vendor-managed storage, unseal and snapshots.
   - Spring Vault is a Java client integration for the Vault HTTP API, not
     a secrets server, and cannot be selected as a backend.
   - Declared capabilities come from upstream documentation and are
     unverified until the catalog's compatibility check passes.
8. **Storage and volume profile.** Each storage class in a profile states:
   the provider tool and its required capabilities (validated against the
   catalog), quotas (total and per claim), encryption at rest with a key
   **reference**, backup tool, schedule, retention and whether restore was
   tested, topology (replicas and spread), reclaim policy, retention, and
   an explicit **data-loss effect**. `Delete` reclaim must say data is
   deleted; a missing backup must say "no backup"; an untested restore
   must be stated; usable profiles need a tested restore. In a cloud
   profile the key reference may be the profile's own provider KMS
   (`awskms://`, `azurekeyvault://`, `gcpckms://`); a key from another
   provider is rejected.
9. **Repository guards.** `deploy/checks/static_guards.py` fails CI when
   `ansible.cfg` holds node addresses, groups or an inline host list; when a
   committed Layer 1 inventory or variable file holds a non-RFC 5737
   address; when a documented or scripted `ansible-playbook` command uses
   `-e`/`--extra-vars`; or when a README or profile claims a Helm chart or
   an implemented layer that the repository does not contain. A CI step
   also proves that a live run (`site-rke2.yml`'s preflight) rejects the
   example inventory.

## Consequences

- `deploy/k8s` moves to `deploy/02-cluster-addons`; `deploy/03-observability`
  and `deploy/04-apps` exist as READMEs only, saying nothing is implemented.
- CI adds inventory validation with negative fixtures (including the
  live-run rejection of the example inventory), a `catalog` job
  (`deploy/catalog/validate.py` plus 49 unit tests covering valid profiles
  and planted violations) and a `guards` job (`deploy/checks/static_guards.py` plus 15
  unit tests). All checks are static.
- Every profile's vault block now needs storage, topology, unseal, backup
  and data-loss fields; the planned cloud profiles carry planned values
  (three zone-spread replicas, cloud-KMS auto-unseal, manual snapshots,
  untested restore) for review, not a tested configuration.
- Existing Layer 1 users must generate `inventory/hosts.ini` locally before
  the next run; the committed file is now an example.
- No tool is `approved`, so no profile can be `validated` or `approved`
  until checks are done and recorded. That is intended.
- The lab profile's Layer 0 defaults (the `10.20.0.0/24` NAT subnet) and the
  Layer 2 LoadBalancer pool remain in Git as lab defaults, not site data.

## Alternatives rejected

- **Terraform as the default.** BSL 1.1 is not OSI open source.
- **HashiCorp Vault as the open-source default.** Same reason; kept as an
  optional choice with explicit editions.
- **Free-form commands in profiles or the GUI** (including natural language
  turned into Ansible tasks). Unreviewable and bypasses plan-and-review.
- **Committed real inventory.** Leaks private addressing and invites drift
  between Git and reality.

## Open questions for the owner

- Confirm the proposed defaults, and the secrets default (OpenBao) given
  that `docs/requirements-addendum.md` names HashiCorp Vault as the initial
  backend.
- How OpenBao snapshots are scheduled (a reviewed CronJob is assumed) and
  where they are kept off-host for the lab profile.
- On-prem WORM object storage now that MinIO's open-source repository is
  archived (Ceph RGW listed as an unverified candidate).
- Pin the OpenTofu and ansible-core versions CI installs (both unpinned).
- Keep Layer 2 on Kustomize or move add-ons to Helm; whether Argo CD also
  owns add-ons.
- Whether lab-default subnets may stay in Git.
- A bare-metal Layer 0 (no hypervisor) target.
- Whether production needs a self-managed or provider-operated OpenStack
  profile, or a simpler multi-host Kubernetes substrate; decide from
  capacity, support and recovery requirements before implementing it.
