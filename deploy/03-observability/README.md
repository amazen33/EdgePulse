# Layer 3 -- `deploy/03-observability` (planned, nothing here yet)

The LGTM stack (Loki, Grafana, Tempo, Mimir), OpenTelemetry Collector
and Grafana/Tempo service-graph topology visualization are installed
and validated **as their own step**, after Layer 2
(cluster add-ons) and before service instrumentation or Layer 4
(applications). ADR 0015 makes LGTM + OTel the enterprise observability
plane; `docs/adr/XXXX-proposed-observability-installation-sequence.md`
sets C2a installation before C2b code instrumentation.

**Status: planned.** No manifest, chart, values file or pipeline exists in
this directory or anywhere else in the repository. Nothing is installed on
any cluster.

## Why a separate layer

- It can be installed, upgraded, validated and removed without touching the
  engine (Layer 1), the add-ons (Layer 2) or any application (Layer 4).
- Its storage (log, trace and metric retention) needs its own storage
  profile with explicit retention and data-loss effects
  (`deploy/profiles/`, `contracts/deploy/deployment-profile.schema.json`).
- Several LGTM components are AGPLv3; the licence and version are recorded
  in `deploy/catalog/tools.yaml` and must pass the catalog's checks before
  a non-lab profile may select them.

## Acceptance criteria (before this layer can be called done)

1. Pinned versions from the tool catalog, installed by a reviewed, static
   artifact (Helm chart values or Kustomize) rendered and schema-checked in
   CI (`.github/workflows/infra.yml`), like Layer 2.
2. Runs under the cluster's restricted Pod Security Standard, or in a
   reviewed, labelled namespace with the reason recorded.
3. A storage profile with quotas, retention, reclaim policy and backup
   stated, and validated by `deploy/catalog/validate.py`.
4. Target-cluster smoke test **without IOT-EE application code**: a
   temporary synthetic OTLP emitter sends a trace, log and metric;
   operators can query all three through the intended endpoints and
   dashboards. Paired synthetic client/server spans must produce a
   service-to-service edge in Grafana's Service Graph via Tempo's
   metrics generator and Mimir. Check access controls, metric-label
   cardinality and alert routing. Cilium/Hubble network-flow mapping is
   validated separately with the selected cluster networking layer; it
   does not replace this application service-graph test.
5. Restart and recovery tests show ingestion resumes, storage and
   retention behave as declared, resource limits hold, and a failed
   observability component does not affect the cluster's other layers.
   Record an owner-approved soak interval, backlog/drop behavior,
   observed resource usage and rollback evidence. A short smoke test
   alone does not establish continuous-service stability.
6. After this installation gate, C2b connects `services/identity` and
   verifies `traceparent` and `X-Correlation-ID` in logs and spans.
   Application trace propagation is a separate proof, not a
   prerequisite to the installation gate.

Until then, record any trial installation as blocked or planned in
`deploy/README.md`, never as done.
