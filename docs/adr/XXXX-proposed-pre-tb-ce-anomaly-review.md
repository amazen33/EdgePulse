# ADR XXXX (proposed) -- Anomaly detection and human review before TB CE

Status: proposed. No production detector, review workflow or pre-TB CE gate
exists. Number at merge. This refines the external Kafka-to-TB CE bridge and
keeps TB CE downstream of IOT-EE's canonical ingestion.
The [event-processing topology](../event-processing-topology.md) shows this
gate alongside Flink, search, RAG and Flowable branches.

## Proposed flow

```text
device -> authenticated ingestion -> durable raw/canonical Kafka event
                                  |                  |
                                  |                  +-> detector -> alert/case
                                  |                                   |
                                  +-> delivery gate <--- human decision <-+
                                               |
                                     external bridge -> TB CE API -> CE rules
```

The Tier 3 detector evaluates a versioned tenant/device policy using validated
telemetry, quality checks, thresholds/rules and optional model scores. Flink
CEP is the candidate for complex patterns across time and devices; it emits
curated critical alerts to the versioned `alerts-critical` Kafka topic for
the Tier 4 Flowable Event Registry adapter. It must isolate state by tenant,
define device/group keys, event-time watermarks, late-event behavior and
deduplication. Simpler checks can use a service-owned detector. It
emits a separate `AnomalyAssessment` with event ID, policy/model version,
score/reason code and timestamp. The source event remains immutable and
replayable. Never overwrite the measurement with a model output. A service
owned decision policy classifies each event as **pass**, **flag and pass**, or
**hold for human review**. Only approved high-impact classes may be held;
ordinary telemetry flows to TB CE within its latency SLO. Alerts and cases
can be raised before CE processing without stopping all data.

For a held event, the delivery gate persists a state keyed by tenant/device/
event ID and prevents the bridge from posting that event to TB CE until an
authorized decision arrives. A human reviewer sees the measurement, source
quality, rule/model explanation and any relevant history, then releases,
rejects or escalates with a reason. The reviewer may open a work order or
request a device action through the owning service; the workflow engine
cannot send a command directly. A released event preserves event time,
correlation and decision provenance when delivered to CE. A rejected event
remains in the evidence/replay ledger with an explicit disposition; it is
not silently deleted. The gate is asynchronous and bounded: define backlog
capacity, review deadline, staffing escalation and an explicit per-class
timeout outcome. Safety-critical actions fail closed, while noncritical
telemetry follows its approved continuity policy. No implicit timeout
approval is allowed.

The detector may use a replaceable model provider, but deterministic
thresholds, quality rules and authorized human decisions control the gate.
Model drift, false positives/negatives and per-tenant baselines require
measurement. Do not use anomaly scores as tenant authorization. Keep alert
delivery independent of CE availability. CE's own rule engine still runs
after release, so compare CE alarms/rules and displayed data against the
ungated baseline and account for delayed or withheld events explicitly.
Preserve per-device ordering where CE rules depend on it; later events for
that device may need a bounded hold or a documented out-of-order policy.

## Required proof before activation

Run synthetic normal, flagged, held, approved, rejected, timed-out and
duplicate events across two tenants. Prove no cross-tenant review, one case
and one bridge disposition per event, deterministic replay, process and CE
outage recovery, lag alarms, backlog limits, reviewer audit, and delivery
ordering. Test a model false positive and detector outage. Measure latency
and CE rule/alarm/dashboard parity by tenant/device/time window. Record
policy/model versions and approved thresholds. Human review capacity and
continuity policy must meet the 24/7 operating target before enabling a
hold class in production.

See the [workflow engine selection ADR](XXXX-proposed-workflow-engine-selection.md)
for the human-task adapter choice and the
[Kafka-to-TB CE bridge ADR](XXXX-proposed-tb-ce-kafka-bridge.md) for CE
delivery ambiguity and idempotency limits.
