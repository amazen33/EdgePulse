# ADR XXXX (proposed) -- Platform communication direction: REST via APISIX/BFF, gRPC internal sync, Kafka async, MQTT devices; Spring Cloud LoadBalancer only where client routing needs it

Status: proposed. Unnumbered draft per `docs/adr/README.md`; the number
is assigned at merge. Encodes the platform direction agreed by the
repository owner on 2026-09-25.

Supersedes ADR 0011 Decision 3's "Inter-service transport" bullet
("gRPC internally; REST + Spring Cloud LoadBalancer for external HTTP")
and narrows ADR 0011 Decision 1's "client-side load balancing ...
wherever a cross-cutting platform concern needs one". All other parts of
ADR 0011 Decisions 1 and 3 stand. ADR 0011 is not edited.

## Context

`docs/requirements-addendum.md` ("Interfaces and migration sequence")
already states the interface split: REST over HTTPS for the frontend
through APISIX/BFF, gRPC between separately deployed services,
in-process interfaces inside a modular monolith, Kafka for asynchronous
domain events, MQTT for devices, and one authorized multiplexed
WebSocket per browser.

ADR 0011 Decision 3 describes the same stack but pairs Spring Cloud
LoadBalancer with "external HTTP". Spring Cloud LoadBalancer is a
client-side, in-process load balancer for a *service client* choosing
among instances; it is not an edge component, and external HTTP already
enters through APISIX (ADR 0011 Decision 3, "Gateway"). In the
production-default topology, Kubernetes Services and the selected profile's
networking layer route in-cluster traffic (proposed Cilium/Ambient ADR), so a
second client-side balancer on every call would duplicate that routing.

ADR 0017 Decision 3 (dual REST + gRPC driving adapters over the same
`port.in`) is compatible with this ADR and unchanged by it.

## Decision

| Path | Transport | Notes |
| --- | --- | --- |
| Browser / external client -> platform | REST over HTTPS through **APISIX** (north-south L7) and a **BFF** | Browser sessions per the addendum: authorization code + PKCE, HttpOnly cookies, CSRF protection. Services still re-verify JWTs (ADR 0016 Decision 4) |
| Browser live updates | One tenant-authorized, multiplexed **WebSocket** per browser through APISIX | Progress and scoped read-model updates only; never raw Kafka or device streams; never firmware binaries |
| Map-only/embedded browser live updates (proposed location ADR) | Read-only **SSE** instead of the full-console WebSocket | REST snapshot first, then scoped versioned location deltas; reconnect and gap require resnapshot; no parallel SSE and WebSocket feed for the same map |
| Service -> service, synchronous | **gRPC** | Contracts in `contracts/` (`.proto`); each service generates its own stubs (ADR 0013). Peer-authenticated TLS/mTLS requires independent conformance proof; Cilium network policy or encryption alone is insufficient (proposed Cilium ADR) |
| Module -> module inside the modular-monolith profile | In-process port interfaces | Same `port.in` interfaces the gRPC adapter would call (ADR 0017) |
| Asynchronous domain events | **Kafka** (Kafka-protocol brokers per ADR 0018) | Transactional outbox, idempotent consumers, no cross-system atomicity claim |
| Devices | **MQTT** over authenticated TLS (mTLS where supported), per-device broker ACLs | Broker stays L4/broker, not absorbed into APISIX. Firmware binaries over HTTPS/object storage |

1. **APISIX remains the selected north-south gateway.** It stays behind
   the plug-and-play rule in `CLAUDE.md` (replaceable by NGINX/Envoy
   without touching business logic), but no replacement is planned.
2. **Spring Cloud LoadBalancer only where service-client routing
   requires it.** It is not a default dependency and never sits on the
   external edge. Allowed only where a service's own client must choose
   among instances and nothing else does -- for example a deployment
   profile without suitable Kubernetes Service routing. Each use is named
   in that service's README with the reason. Where the cluster routes a
   call, the client uses the service address and no client-side balancer.
3. **No other synchronous inter-service protocol** (REST between
   internal services, or direct database access across service
   boundaries) is introduced without a new ADR. External-facing REST
   adapters in services exist to serve APISIX/BFF traffic (ADR 0017
   Decision 3).

## Consequences

- `CLAUDE.md` and `README.md` state this direction.
- No code changes: `services/identity` already exposes REST and gRPC
  adapters over one `port.in` and has no Spring Cloud LoadBalancer
  dependency.
- None of these paths is verified end to end. APISIX, the BFF, a Kafka
  cluster, an MQTT broker, Cilium and workload mTLS are all **planned**;
  the only live transport is the identity walking skeleton's REST and
  gRPC adapters under test.

## Alternatives rejected

- **REST for internal synchronous calls.** Loses the typed `.proto`
  contracts ADR 0013 relies on for autonomy.
- **Spring Cloud LoadBalancer on every client.** Duplicates cluster routing and
  adds per-service configuration with no benefit in the default profile.
- **Spring Cloud Gateway instead of APISIX.** APISIX is already selected
  (ADR 0011 Decision 3, ADR 0005's route/policy contract).

## Open questions

- Which deployment profiles lack suitable cluster routing, and therefore may
  need Spring Cloud LoadBalancer. Profile 1 (modular monolith) uses
  in-process calls; profile 4 (edge) is not designed (ADR 0011 Risk 6).
- BFF technology and placement. Not decided here.
