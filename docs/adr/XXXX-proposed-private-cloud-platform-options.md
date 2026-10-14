# ADR XXXX (proposed) -- Private-cloud and Kubernetes management profiles

Status: proposed evaluation. No listed production stack is installed or
approved for IOT-EE. This ADR extends the deployment-layer proposal; it does
not replace the current Hyper-V/RKE2 lab. Number at merge.

Assumption: **OCM** means the open-source **Open Cluster Management** project,
not Red Hat's similarly abbreviated OpenShift Cluster Manager service.

## Owner's target topology

The target is one **IOT-EE management control plane** running upstream CAPI
controllers, with provider-specific infrastructure adapters creating separate
workload Kubernetes clusters:

```text
IOT-EE management cluster / Deployment Studio
                 |
        Cluster API (CAPI)
                 |
    +------------+------------+
    |            |            |
 CloudStack   OpenStack   Bare metal / Metal3
    |            |            |
 Kubernetes   Kubernetes   Kubernetes
```

Here "one control plane" means a common management *API and workflow*, not
one Kubernetes control-plane quorum spanning all three sites. The CAPI
management cluster requires its own bootstrap, HA, backup and recovery plan.
Each workload cluster has its own Kubernetes control plane, fault domain,
network, storage and lifecycle. The three infrastructure providers must not
share credentials or give one tenant authority over another provider.

For each branch, CAPI requires an infrastructure provider plus compatible
bootstrap and control-plane providers. The proposed bare-metal adapter is
**Cluster API Provider Metal3** with Bare Metal Operator and Ironic;
hardware BMC access, provisioning network, images, IPAM and API endpoint
need their own protected design. The default upstream bootstrap/control-plane
candidate is kubeadm. RKE2 requires a separately verified compatible pair.
CloudStack and OpenStack provider releases also need explicit CAPI and
Kubernetes version-matrix checks.

## Candidate profiles

| Profile | Infrastructure and cluster lifecycle | Good fit | Main proof needed |
| --- | --- | --- | --- |
| OKD + Machine API + OCM | OKD manages its own nodes where Machine API is operational; OCM registers and governs multiple clusters | Teams choosing an integrated Kubernetes platform and multicluster governance | Bare-metal installation mode and Machine API support, OCM hub recovery, OKD upgrades, SCC/chart conformance, Cilium/Ambient compatibility |
| Harvester + Rancher + RKE2 | Harvester supplies VMs/storage/network integration; Rancher provisions and manages guest RKE2 clusters | Smaller private cloud that primarily needs VM-backed Kubernetes | Harvester/Rancher/RKE2 version matrix, separate Rancher management availability, CSI/CCM, storage and VM recovery, upgrade and rollback |
| CloudStack + CAPI + Kubernetes | CloudStack supplies IaaS; Cluster API Provider CloudStack manages cluster machines | One infrastructure branch of the common CAPI management plane | CAPI infrastructure, bootstrap and control-plane provider compatibility; images, networking, CSI/CCM, management-cluster recovery |
| OpenStack + CAPI + Kubernetes | OpenStack supplies IaaS; Cluster API Provider OpenStack manages cluster machines | One infrastructure branch of the common CAPI management plane | OpenStack operating capacity, CAPI provider compatibility, Neutron/Cinder/Octavia integration, upgrade and management-cluster recovery |
| Bare metal + CAPI + Kubernetes | Metal3/Ironic provisions physical hosts; Cluster API Provider Metal3 manages machines | Direct Kubernetes clusters on owned hardware without a VM/IaaS layer | BMC and provisioning network security, images, IPAM, endpoint/LB, hardware replacement and management-plane recovery |

RKE2 on CloudStack or OpenStack is a **separate variant**, not an automatic
result of selecting CAPI. CAPI's infrastructure provider provisions machines;
the selected bootstrap and control-plane providers must explicitly support
the pinned RKE2 version. If that combination is unsupported, use a reviewed
RKE2 lifecycle mechanism outside CAPI or use a supported Kubernetes bootstrap
such as kubeadm. Do not claim a tested RKE2+CAPI profile until it exists.

OKD's Machine API is based partly on upstream Cluster API ideas but is not
the same deployment path as installing an upstream CAPI provider. On
user-provisioned infrastructure it can require additional configuration;
platform type `none` cannot use Machine API. OCM is a multicluster inventory,
placement and governance layer, not a VM provisioner or substitute for the
cluster's own lifecycle. Rancher is likewise a management plane; its loss
must not become an untested single point of failure for application runtime.

## Recommendation for IOT-EE

Keep the existing RKE2 lab and application-only cloud profiles as the near
term implementation path. Make the **common CAPI management plane with
CloudStack, OpenStack and Metal3 branches** the target architecture to
validate, beginning with one provider and one disposable workload cluster.
Add providers only after management-cluster recovery and workload parity are
proven. CloudStack and OpenStack are alternatives for the IaaS branch, not
requirements to operate both. Direct bare metal is the third branch.
Evaluate Harvester/Rancher/RKE2 and OKD/Machine API/OCM as independent
platform profiles where their integrated lifecycle better serves an operator;
do not force them through the common CAPI path by assumption.

Deployment Studio should select a versioned **profile**, not expose arbitrary
tool combinations as a supported product. Separate Layer 0 IaaS, Layer 1
cluster lifecycle, multicluster management and Layers 2-4 add-ons,
observability and applications. Keep IOT-EE business services on Kubernetes
APIs and service-owned contracts, with provider-specific CSI, load balancer,
ingress, CNI, identity and backup settings confined to the profile. The
applications-only path must remain available when customers supply a cluster.

## Evidence gate for every profile

Pin versions and licenses; record support ownership and total operating cost.
Prove installation, node replacement, upgrades and rollback, management-plane
loss, storage/network recovery, backup/restore, security policy and workload
identity, observability before applications, isolated tenant access, and
application chart/API parity. Run the same synthetic IOT-EE behavior and
failure tests on each supported profile. Define RTO/RPO through business
impact analysis and measure them in failover exercises. No profile is
production-supported merely because its upstream components interoperate.

## Primary sources

- [OKD Machine API overview](https://docs.okd.io/latest/machine_management/index.html) and [bare-metal limits](https://docs.okd.io/latest/machine_management/creating_machinesets/creating-machineset-bare-metal.html).
- [Open Cluster Management architecture](https://open-cluster-management.io/docs/concepts/architecture/).
- [Harvester node driver](https://docs.harvesterhci.io/v1.9/rancher/node/node-driver/) and [Harvester cloud provider](https://docs.harvesterhci.io/v1.9/rancher/cloud-provider/).
- [Cluster API providers and management-cluster requirements](https://main.cluster-api.sigs.k8s.io/reference/versions), [CloudStack provider](https://github.com/kubernetes-sigs/cluster-api-provider-cloudstack), [OpenStack provider](https://github.com/kubernetes-sigs/cluster-api-provider-openstack), and [Metal3 provider](https://github.com/metal3-io/cluster-api-provider-metal3).
