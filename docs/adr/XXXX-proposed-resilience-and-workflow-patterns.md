# Proposed ADR -- Resilience and distributed-workflow policy

Status: proposed. Complements ADR 0018's outbox/idempotent-consumer
decision and ADR 0007's M6 resilience/DR stage. Specify the policy
before implementing each remote call or long-running workflow; M6
verifies system behavior under sustained faults. No production
resilience configuration or SLO has been verified.

## Decision

1. **Classify each dependency and operation.** The owning service
   records the caller, dependency, tenant scope, operation, end-to-end
   latency budget, failure mode, idempotency key, retry owner, queue
   capacity, fallback and alert in its service contract/runbook. Use
   observed load and SLOs to set numeric thresholds; do not apply a
   universal breaker or timeout configuration.
2. **Bound every remote call and queue.** Set connection and operation
   deadlines inside the caller's end-to-end deadline. Bound concurrent
   calls, worker pools, queues, batch size and memory. Separate
   critical telemetry, commands, identity and evidence capacity from
   optional AI, reports, maps and migration work. Use admission control,
   per-tenant fair limits and backpressure so one tenant or dependency
   cannot exhaust shared capacity. APISIX edge rate limits do not
   replace service-side resource limits.
3. **Retry only safe operations.** Retry transient failures with a
   capped attempt/time budget, exponential backoff and jitter; honor
   server retry hints. Assign one layer ownership of each retry so
   nested clients, mesh and gateway do not multiply attempts. A write
   needs a stable idempotency key or a proven reconciliation step.
   Never retry invalid authorization or validation failures. A timeout
   after a remote write is an ambiguous outcome, not proof of failure.
4. **Use circuit breakers on failure-prone synchronous dependencies.**
   A breaker is scoped to a dependency and operation class, with
   measured failure/slow-call policy and controlled probes to recover.
   It protects caller resources when a downstream dependency fails;
   it is not a substitute for timeout, retry budget or durable backlog.
   A broker/CDC consumer normally pauses, backs off and resumes from a
   checkpoint rather than discarding events because a breaker opened.
5. **Use bulkheads where failures can spread.** Isolate concurrency
   and resources for external TB CE, payment providers, AI providers,
   report queries, firmware distribution and migration jobs. Keep
   critical control paths and tenants from starvation. Reject, queue
   within a hard bound, or degrade optional work when a pool is full;
   do not silently grow queues without limit.
6. **Declare truthful degradation.** Optional AI, maps, reports and
   payment-provider operations may fail independently of telemetry,
   alarms and authorized device control. A cached/read-model fallback
   is permitted only if its age and status are visible and access is
   rechecked. Never report a device command, payment, firmware update,
   audit write or migration cutover as successful based on a fallback.
   Fail closed for authentication, authorization and secret access.
7. **Select Saga only for a cross-owner business workflow.** A durable
   orchestrator or state machine is appropriate when local transactions
   in several services must reach an agreed outcome (for example
   payment-to-entitlement activation). Record forward recovery,
   compensation, timeout, manual intervention and the point after
   which physical/device effects cannot be undone. Do not add Saga to
   ordinary telemetry, map updates or CDC. Firmware rollout and M9
   cutover require durable workflows and recovery; neither implies
   that every completed physical action is automatically reversible.
   Start with a service-owned persisted state machine when the process
   is small. Consider a BPMN engine only when versioned process models,
   human tasks or complex cross-service coordination justify its
   operational cost. Keep workflow commands/events and state behind
   service-owned ports; do not put engine-specific APIs in domain code.
   The engine coordinates an authorized cutover but never grants its
   own approval or bypasses the human gate.
   A device/alarm repair is another candidate: an authorized alarm or
   service request can create a work order, assign and notify a
   technician, track acknowledgment and repair, escalate overdue work,
   then require verification and authorized closure. Flowable Open Source
   is the provisional BPMN/human-task pilot; CIB seven, EximeeBPMS and
   FINOS Fluxnova are comparison candidates under the
   [workflow selection ADR](XXXX-proposed-workflow-engine-selection.md).
   The alarm, work-order and device services still own
   their data, permissions and state transitions; Flowable receives
   scoped IDs and invokes versioned use cases through an adapter. It
   must not become the sole system of record or bypass tenant checks.
8. **Make failure visible and operable.** Publish bounded-cardinality
   metrics and traces for deadline expiry, breaker state, bulkhead
   rejection, retry amplification, backlog age, dead-letter count and
   degraded mode. Define health/readiness by actual service capability,
   alert on SLO and data-freshness impact, and maintain runbooks for
   replay, recovery and human escalation. Do not put tenant/device IDs
   into metric labels or sensitive values into logs.

## Application by stage

| Stage/path | Required policy before implementation |
| --- | --- |
| M3 ingestion and Kafka-to-TB CE bridge | Durable outbox/inbox, bounded backlog, idempotency and checkpoint replay; CE HTTP deadlines, retry budget, breaker and isolated worker capacity. Test ambiguous accepted-but-timed-out posts against side-effecting rules. |
| M3 pre-TB CE anomaly review | Durable assessment and gate ledger, scoped alert/case, bounded human-review hold, explicit timeout disposition, per-device ordering and replay; test false positives and CE parity. See the [anomaly-review ADR](XXXX-proposed-pre-tb-ce-anomaly-review.md). |
| M4 BFF, reports and live updates | Per-route deadline and admission limit; bound report queries and WebSocket/SSE buffers; stale read-model data labelled, authorized and resynchronized after gaps. |
| M5 firmware/device commands | Bounded dispatch and per-device concurrency, acknowledgment/expiry, staged rollout and pause; no false success or automatic rollback claim after a physical flash. |
| M7 payments/entitlements | Provider-specific deadline, breaker and bulkhead; idempotent payment operations, webhook reconciliation, durable activation workflow and explicit pending/failed states. Core IoT operation remains independent of payment availability. |
| M8/M9 deployment and migration | Rate-limited jobs and source-impact budgets, persisted checkpoints, approval gates, stop/resume and rehearsed recovery. Never convert a failed cutover to a silent success. |
| AI integration | Isolated concurrency and spend limits, deadline/breaker and optional degradation without affecting telemetry, alarms or commands. |

## Required proofs

For each selected dependency, test timeouts, slow responses, partial
outages, recovery probes, bounded retry amplification, queue saturation,
bulkhead isolation and tenant fairness. Inject ambiguous write results
and confirm reconciliation instead of duplicate effects or false
success. Test a full-dependency outage and recovery while measuring
critical-path SLOs, backlog drain and operator alerts. M6 includes
load/soak, backup/restore and DR against owner-approved RPO/RTO; those
tests do not replace the earlier stage-specific failure tests.

## Open inputs

Service and tenant SLOs, expected concurrency/traffic, allowed stale
read age, dependency budgets, operator escalation, backlog retention,
provider limits and which workflows need compensation versus forward
recovery. Numeric settings stay provisional until measured.

## Mechanism references

- [Azure transient-fault guidance](https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults) discusses retry budgets and circuit breakers.
- [Azure reliability patterns](https://learn.microsoft.com/en-ie/azure/well-architected/reliability/design-patterns) covers bulkheads, circuit breakers and rate limiting.
- [AWS Saga patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-patterns.html) distinguishes choreography and orchestration.
