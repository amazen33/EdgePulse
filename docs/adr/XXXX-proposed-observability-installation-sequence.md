# Proposed ADR -- Install and stabilize observability before service instrumentation

Status: proposed. Refines ADR 0015's implementation sequence only;
LGTM/OTel remains the enterprise observability authority and its
correlation/trace requirements are unchanged. The owner's sequencing
decision is infrastructure scaffolding -> observability installation
and stability proof -> service instrumentation and application proof.
The repository contains no verified lab VM, Kubernetes-cluster or
observability-stack installation evidence.

## Decision

1. Prepare and statically validate the reviewed Layer 3 manifests,
   pinned tool/image/chart versions, resource requests and limits,
   storage/retention/backup policy, access controls, dashboards and
   topology visualization.
   Layer 3 owns the Collector and LGTM components; it does not install
   or modify application services.
2. Apply and verify Layers 0-2 in the approved isolated lab profile
   before installing Layer 3. Layer 3 installation is an explicit,
   separately approved operation with a recorded inventory, rendered
   manifests, version set and rollback procedure. A local container
   demonstration cannot substitute for the target-cluster proof.
3. Prove Layer 3 works **without IOT-EE application code** using a
   synthetic OTLP trace, log and metric from a temporary test emitter.
   Check ingest, query, dashboards, alert routing, retention, access,
   resource use, restart/recovery and failure isolation. Remove the
   test emitter after the proof. Record load and stability over an
   owner-approved soak interval; do not claim 24/7 readiness from a
   one-request smoke test.
   Install the open-source Grafana/Tempo **Service Graph** capability
   with the Layer 3 stack: Tempo's service-graph metrics generator
   sends bounded-cardinality metrics to Mimir, and Grafana displays
   service dependencies with request rate, errors and latency. A
   synthetic paired client/server trace must create the expected graph
   edge before application code is instrumented. Verify that sensitive
   identifiers do not become metric labels and that missing/expired
   graph edges are visible as diagnostic conditions. The live graph
   gains real service edges only after C2b instruments services.
   Cilium/Hubble is the separately reviewed **network-flow and
   connectivity** view for profiles that select Cilium. Prove a synthetic
   allowed and denied flow, scoped access, and a visible service-map edge
   at the cluster-networking layer. Hubble does not replace the LGTM
   application trace graph. Neither view substitutes for the
   tenant-authorized device map or a
   physical network inventory.
4. Only after the Layer 3 gate passes, instrument the existing
   identity REST/gRPC service and other services as they are built.
   Service instrumentation must preserve `traceparent` and the
   server-issued `X-Correlation-ID` in their distinct carriers per
   ADR 0015. Later C3/C5 work adds authenticated actor and Kafka
   propagation, followed by end-to-end tests on the installed stack.
5. Keep Layer 3 independently upgradeable and replaceable through
   versioned deployment artifacts and operational conformance tests.
   An observability outage must not halt telemetry, alarms or device
   commands; buffer/drop policy for telemetry export is explicit and
   bounded, with health alerts and no secret/PII leakage.

## Gates and open inputs

The installation gate needs approved versions and licenses, available
cluster capacity, storage class and retention/backup configuration,
network access, administrative roles, synthetic ingest/query checks,
synthetic service-graph edge and cardinality checks,
failure/restart/rollback evidence and a defined soak target. The
current lab profile still lists the stack as unpinned and Layer 3 as
planned. These are prerequisites, not proof of installation. Production
HA, DR and 24/7 support require separate environment-specific evidence.

Mechanism references: [Grafana Tempo service graphs](https://grafana.com/docs/tempo/latest/metrics-from-traces/service_graphs/enable-service-graphs/) and [Hubble service map](https://docs.cilium.io/en/stable/observability/hubble/hubble-ui/).
