# ADR XXXX (proposed) -- Evaluate Cilium and Istio Ambient for workload networking and security

Status: proposed. The owner has kept Cilium and Istio Ambient as options;
the final profile-level choice is deferred. No Cilium or Istio Ambient
installation, workload-authentication proof, or service-mesh migration has
happened. Number this ADR at merge.

Proposes to supersede ADR 0011's fixed Istio choices in Decision 3
(mesh/load balancing), Decision 5 (Istio-delivered service mTLS), and
Decision 7 (Istio multi-cluster federation) with a tested profile choice.
ADR 0011 remains an immutable record; its transport, tenant-authorization
and replaceability requirements still apply. APISIX remains the north-south
gateway and service-owned RBAC/ABAC remains the business authorization
boundary.

## Decision

1. Evaluate the owner's layered model: **Cilium** owns CNI and coarse
   pod reachability (L3/L4 policy); **Istio Ambient** owns workload identity,
   mTLS and service-level L4/L7 authorization for enrolled workloads. L7
   policy requires a waypoint. Cilium policy still applies to Ambient's
   encrypted tunnel, but cannot inspect its inner source, destination or
   application request. Istio must enforce in-mesh service policy. Do not
   configure Cilium and Istio L7 HTTP policy for the same flow. The combined
   profile needs coexistence tests before selection; a Cilium-only profile
   remains a comparison candidate. Neither is the platform default yet.
   Kiali is conditional on an Ambient profile;
   Hubble is conditional on Cilium. LGTM/OTel remains the independent
   application trace and service-graph authority in every profile.
2. Keep workload authentication, encryption and authorization distinct.
   Cilium network identity/policy and Istio workload identity do not
   authorize a tenant or business action. WireGuard/IPsec encryption does
   not by itself establish the
   peer service's application identity. Cilium's mutual-authentication
   feature is currently beta, requires encryption to meet the intended
   combined guarantees, and has documented limits for multi-cluster and
   external mTLS interoperation. Istio Ambient provides workload mTLS via
   ztunnel/HBONE, but its default permissive mode can accept non-mesh
   plaintext traffic; prove STRICT enforcement where required. A waypoint
   is needed for L7 policy, and policy placement changes peer identity
   visibility. Production gRPC calls require verified peer-authenticated
   TLS/mTLS under the selected profile; use application-layer mTLS where
   cluster-layer proof or coverage is incomplete.
   Each service still validates JWT/workload identity and authorizes its
   own operation; no network location or policy verdict alone grants it.
3. Treat both approaches as cluster changes, not drop-in manifest swaps.
   Inventory the RKE2 lab's current CNI and kube-proxy settings first.
   Review kernel, CNI ownership, routing, LoadBalancer interaction, Pod
   Security, upgrades and rollback. For a Cilium profile, choose and pin
   the RKE2-integrated path or a reviewed external Helm installation;
   never enable kube-proxy replacement by assumption. For Ambient, test
   ztunnel, optional waypoint, policy attachment, plaintext bypass and
   certificate rotation. If combined with Cilium, validate the documented
   CNI and socket-LB compatibility settings and assign one owner for each
   L7 policy to avoid conflicting enforcement.
4. Existing-cloud `applications-only` profiles install neither option.
   Their cluster operator must prove equivalent network policy, workload
   authentication and encryption capabilities as external dependencies.
   A cloud CNI or mesh may differ if it passes the same conformance suite;
   business code and charts must not depend on either vendor API.
5. Keep Spring Cloud LoadBalancer only where a service client must select
   an instance itself. Kubernetes Services and the selected cluster
   networking layer normally route in-cluster calls; neither candidate
   inherits the other's traffic-management claims without a specific test.

## Decision comparison before profile approval

Record versions, license/edition, target distribution, owner, resource
cost, support model and test evidence for: default-deny policy, gRPC
connectivity, peer mTLS, plaintext rejection, certificate rotation,
ingress/egress, L7 policy where needed, multi-cluster behavior, topology,
failure isolation, upgrade/rollback and operations. Compare Cilium-only,
Ambient with the chosen CNI, and Cilium-plus-Ambient where coexistence is
required. Select a default only after those results and a human ADR
approval; no product domain code depends on the selection.

## Acceptance evidence before deployment

- Pin candidate versions, verify component licenses and support status,
  and add a reviewed profile selection and install artifacts only after
  the comparison.
- Show default-deny network policy, allowed gRPC flow, denied unauthorized
  flow, and tenant-level denial inside the receiving service.
- Show peer-identity validation, transport encryption, certificate/key
  rotation and expiry, and failure behavior. Multi-cluster claims need
  separate evidence; Cilium mutual authentication must not be assumed to
  cover Cluster Mesh.
- Show Hubble or Kiali network/mesh topology where selected and LGTM's
  paired-span application service graph, with scoped access and bounded
  metrics cardinality.
- Rehearse CNI/mesh upgrade, rollback and node recovery on an isolated cluster.
  Record compatibility separately for RKE2, EKS, AKS and any OKD profile.

## Primary references

- [Cilium source and component licenses](https://github.com/cilium/cilium).
- [Cilium mutual authentication (beta) and limitations](https://docs.cilium.io/en/stable/network/servicemesh/mutual-authentication/mutual-authentication/).
- [Hubble service map](https://docs.cilium.io/en/stable/observability/hubble/hubble-ui/).
- [Cilium installation with RKE2](https://docs.cilium.io/en/stable/installation/k8s-install-rke/).
- [Istio Ambient architecture](https://istio.io/latest/docs/ambient/overview/) and [L4 policy and STRICT peer authentication](https://istio.io/latest/docs/ambient/usage/l4-policy/).
- [Cilium and Istio coexistence guidance](https://docs.cilium.io/en/stable/network/servicemesh/istio/).
