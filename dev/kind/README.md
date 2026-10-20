# Local kind rehearsal

**Test harness only, not a deployment target, evidence level T.** Nothing here
proves an MS3 fact or creates a milestone receipt. The authoritative scope is
[IOT-WO-04, all amendments](../../docs/work-orders/IOT-WO-04-tb-ce-core-on-twinfra.md).
Local operations need separate owner approvals for up, install, upgrade and down.
No lab, other project, controller or distro is inspected or changed by a script.

## Static gate

PowerShell 7, an existing kubectl for local kubeconfig parsing, Python and
PyYAML 6.0.3 (MIT) are prerequisites. Downloads are public artifacts only.
Helm 3.19.0 must be checked against the checksums in pins.json before use.

```powershell
python dev/kind/tests/render_check.py --helm target/kind-tools/helm.exe
pwsh -NoProfile -File dev/kind/tests/guards.ps1
mvn -B -f pom.xml verify
```

The render test lints three profiles and validates their application and
initialization renders. Eleven tests plant forbidden identities, host access,
external exposure, missing restrictions, cluster-scoped objects and missing CNPG
version metadata. Guard tests
parse only the committed credential-free seed, then mock the clients: all four entry points must reject a wrong context before any
engine call. CI renders on every PR; kind-smoke runs for chart/harness changes
on a disposable GitHub-hosted runner. It is not a required ruleset check.

## Before the first up

Stop for the owner's confirmation of the engine (Rancher Desktop preferred,
Docker Desktop alternative), its own isolated engine distros with no lab link,
only one running engine, moby for Rancher Desktop, built-in Kubernetes off,
about 10 GiB memory and applicable Docker Desktop subscription terms.
The agent never enumerates distros. The owner performs any needed check.
The container engine is a development tool, not shipped or licence-registered.
The scripts require Windows for these desktop-engine selections. CI selection
is available only with GitHub-hosted-runner environment markers.

After confirmation and approval, prepare an isolated inert context. This file
has no credentials and cannot reach an API. It satisfies the first-up context
guard without changing the user's normal kubeconfig. Never point KUBECONFIG at
a pre-existing lab or desktop-engine kubeconfig.

```powershell
New-Item -ItemType Directory -Force target/kind | Out-Null
$env:KUBECONFIG = Join-Path (Get-Location).Path 'target/kind/kubeconfig'
Copy-Item dev/kind/kubeconfig.seed.yaml $env:KUBECONFIG
```

All four scripts require this exact isolated path and current context
`kind-edgepulse-dev`. Engine checks reject a second desktop engine, the wrong
Docker context, a remote endpoint, enabled built-in Kubernetes, or insufficient
memory. There is no automatic engine change or cleanup. After a failure, stop
and report; never bypass a guard. State and downloaded binaries live under the
ignored target/kind directory. The kind binary, kubectl, Helm archive, Cilium
chart and CNPG manifest are SHA-256 checked before use. ARM64 is not supported
by this initial Windows/CI harness; the pinned node index itself is multiarch.

Commands have [up](up/README.md), [install](install/README.md),
[smoke](smoke/README.md) and [down](down/README.md) instructions.
Never pass credential values through command arguments, environment exports,
logs or the rehearsal record. Additional Secrets use standard input only.

## Pins, sources and licences

Every exact digest/checksum is in [pins.json](pins.json); no mutable image tag
is used for application or node execution. The TB patch was published
2026-09-29; kind 2026-08-26; CNPG 2026-09-23; Helm 2025-09-11. All predate the
2026-10-05 cool-off cutoff. Images are **not scanned**: IOT-WO-02 is unmerged.
This inventory is not a supply-chain or licence-gate pass.

| Component | Pin / identity | Licence / source |
| --- | --- | --- |
| kind | 0.33.0, binary checksums in pins.json | Apache-2.0; [release assets and node index](https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0) |
| kind node / Kubernetes | 1.36.4, index digest in pins.json | Apache-2.0; same release |
| kubectl | 1.36.5, Linux/Windows amd64 checksums | Apache-2.0; [official binaries](https://dl.k8s.io/release/v1.36.5/bin/) |
| Helm | 3.19.0, Linux/Windows archive checksums | Apache-2.0; [release](https://github.com/helm/helm/releases/tag/v3.19.0), [checksums](https://get.helm.sh/helm-v3.19.0-windows-amd64.zip.sha256sum) |
| Cilium | 1.20.2, chart SHA-256 in pins.json | Apache-2.0; [upstream chart](https://helm.cilium.io/cilium-1.20.2.tgz) |
| CNPG | 1.30.1, operator image digest and manifest checksum | Apache-2.0; [release](https://github.com/cloudnative-pg/cloudnative-pg/releases/tag/v1.30.1) |
| TB CE tb-node | 4.3.1.6, OCI index digest, commit c77335f4a524bb9fe0209806672c6ec7aea76141 | [Apache-2.0 at the pinned source](https://github.com/thingsboard/thingsboard/blob/c77335f4a524bb9fe0209806672c6ec7aea76141/LICENSE) |
| CNPG PostgreSQL image | 18.6-202610050823-minimal-trixie, OCI index digest | [PostgreSQL](https://www.postgresql.org/about/licence/); [image source](https://github.com/cloudnative-pg/postgres-containers) (Apache-2.0 build packaging) |
| PyYAML | 6.0.3 | [MIT](https://pypi.org/project/PyYAML/6.0.3/), static test dependency only |
| actions/checkout | 5.0.0, 08c6903cd8c0fde910a37f88322edcfb5dd907a8 | MIT |
| actions/setup-python | 5.6.0, a26af69be951a213d495a4c3e4e4022e16d87065 | MIT |

Twinfra version/policy observations (read only, 2026-10-19):
module-2/artifacts.lock.json pins Kubernetes 1.36.5, Cilium 1.20.2 and CNPG
1.30.1. kind's closest published 1.36 patch is **1.36.4**, one patch behind;
there is no minor-version substitution. Cilium mode copies
module-2/values/cilium.yaml: kube-proxy replacement, native routing, Kubernetes
IPAM, IPv4 only, PodCIDR 10.42.0.0/16, host firewall, local-host policy and the
BPF/cgroup mount settings. Local endpoint/cluster identity and upstream public
repositories replace site-specific values. BPF is mounted only inside the
harness-owned kind node container. No laptop filesystem mount is added.

The namespace mirrors WO-39 item 3: account placeholder, restricted PSA,
quota/limits, deny ingress/egress, exact DNS and TB/database rules. No identity
backchannel or gateway is installed. Explicit operator/API and local kubelet
probe/port-forward permissions support only this rehearsal. No general
internet egress is allowed from the application namespace; pulls occur through
the node. The platform operators are confined to the disposable kind cluster.

The checksum-verified Cilium chart renders these Apache-2.0 image pins:

- Cilium 1.20.2: quay.io/cilium/cilium@sha256:2939231d0d3e3ebddcd80fffa168b7ddcc78fdf0dc864d1c8c126ff523c54f01
- Envoy v1.37.6-1789133542-cbec91f666af0bf742da986d43832932dbb26b82:
  quay.io/cilium/cilium-envoy@sha256:af7382699576b9e65e9184efa52eeca0b58aea70ad6e511bf260c91d9f740463
- Operator generic 1.20.2:
  quay.io/cilium/operator-generic@sha256:64d8798350e8569b8e7622563fed6e44dce2625f311e4651b774816516c744fc

These come from the pinned chart's values.yaml. The optional Hubble, ingress,
service-mesh and certificate-generation components are not enabled here.

## Rehearsal coverage

The dated [record](../../docs/rehearsals/tb-ce-kind-2026-10-19.md) distinguishes
static results, pending approvals and exclusions. Up/install/health alone do
not cover the import and upgrade facts. Item 3b requires a merged IOT-WO-03.
The oldest 3.x GitHub release with downloadable assets is
[v3.0](https://github.com/thingsboard/thingsboard/releases/tag/v3.0), published
2020-06-02. The owner-approved upgrade phase must follow the official stepwise
upgrade path on a disposable database, record each step/duration and reconcile
per-class counts/digests. Do not substitute a newer starting version or treat
the release listing as a successful download/upgrade.

No rehearsal or synthetic dataset generator is added to the contract kit here.
Do not fetch consumer code. Keycloak/API-key integration and throughput are
excluded. If the amendment or upstream permissions prevent a required run,
stop with the finding and minimal proposed fix for owner/architect review.
