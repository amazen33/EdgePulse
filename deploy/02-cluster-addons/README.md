# Layer 2 -- `deploy/02-cluster-addons`

(Formerly `deploy/k8s`.) Static manifests only, rendered with Kustomize and
schema-checked by kubeconform in CI; never applied by CI. The address pool
below is the **lab profile's** default, inside its private NAT network.
Observability is a separate Layer 3 (`deploy/03-observability`) and
application releases are Layer 4 (`deploy/04-apps`); neither belongs here.

Layer 2: cluster add-ons applied after the Layer 1 engine
(`deploy/01-k8s-engine/rke2-ansible`) is up. Layer 1 installs only RKE2;
everything that runs *on* the cluster starts here.

| Path | What it does |
| --- | --- |
| `kube-vip/` | LoadBalancer Services: kube-vip-cloud-provider, the address pool (10.20.0.40-.49), and a kube-vip DaemonSet in services-only mode that announces the addresses. No control-plane VIP: clients reach the API on the server's address. |

The cluster enforces the **restricted** Pod Security Standard in every
namespace except the RKE2 system namespaces (Layer 1). Anything added here
that needs more (host networking, capabilities) must run in `kube-system` or
in a namespace labelled explicitly, with the reason in its PR.

## Scaling: why there is no Cluster Autoscaler

The Kubernetes Cluster Autoscaler can only add nodes through a cloud or
Cluster API provider, and none exists for Hyper-V. Rather than ship an
autoscaler that cannot create a VM, node count is declared, reviewed and
applied by a human (lab profile):

1. Add (or remove) an entry in the `nodes` map of the git-ignored
   `deploy/00-infra/private-hyperv/terraform.tfvars` (site data stays out
   of Git; change the committed `terraform.tfvars.example` defaults only in
   a PR).
2. After review, `tofu apply` creates (or deletes) the VM; regenerate
   Layer 1's git-ignored `inventory/hosts.ini` from the
   `ansible_inventory_ini` output and run `validate-inventory.yml`.
3. From `deploy/01-k8s-engine/rke2-ansible`:
   `ansible-playbook -i inventory/hosts.ini site-rke2.yml --limit rke2-master-01,rke2-worker-03`
   joins it (the first server is included because it supplies the join token).

Removing a node: drain it first
(`heal.yml --limit <node> --tags drain` in Layer 1, with typed
confirmation), then remove its entry. Every apply stays a human-approved
step, per the development contract's rule that infrastructure changes need
explicit approval.

Pod-level autoscaling (HorizontalPodAutoscaler) is unaffected: it needs only
metrics-server, which RKE2 installs by default.
