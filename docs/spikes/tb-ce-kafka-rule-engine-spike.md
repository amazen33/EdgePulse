# Spike: can TB CE 4.3.1.5 consume IOT-EE events and run its rule engine, CE-only, no source changes?

Status: spike report (not an ADR). Answers a single question raised
against ADR 0019 ("edge MQTT -> tier-1 buffer -> Kafka; TB CE downstream")
and against `docs/tb-ce-inventory.md` Section 2.2's finding that
`AbstractIntegration` is Professional/Cloud-only. Runs entirely against a
real ThingsBoard CE v4.3.1.5 instance built from ThingsBoard's own
published `.deb` artifact -- nothing here is inferred from screenshots,
blog posts, or product marketing. Every tenant, device, and credential
below is synthetic and was destroyed at the end of the spike (ADR 0012
Decision 2).

**One-line answer:** TB CE 4.3.1.5 can consume externally-originated
events and execute its rule engine, but only through its **documented
device/REST telemetry ingestion API** (a synchronous HTTP call from an
external producer into TB), which is exactly the transport-adapter model
ADR-XXXX (device adapters) already assumes. The literal ADR 0019 reading
-- **TB CE itself, unmodified, subscribing to and consuming a
platform-owned Kafka topic, with no intermediary bridge service** -- is
**BLOCKED**: no such capability exists in CE, and the one place that
capability would live (`AbstractIntegration`) is Professional/Cloud-only,
confirmed both in ThingsBoard's own docs and by testing this specific
instance did not expose it. See "Blocked path" below for the exact
missing dependency.

## Environment

- **TB CE version under test: 4.3.1.5**, the exact pinned version from
  `docs/tb-ce-inventory.md`. Downloaded directly from ThingsBoard's own
  GitHub release asset:
  `https://github.com/thingsboard/thingsboard/releases/download/v4.3.1.5/thingsboard-4.3.1.5.deb`
  (400,905,702... bytes; `sha256:fac5f69f10ce47c45774fe8e8d06716620a4e75f46eb7ec82c4abc42ef5a2fdf`).
  Confirmed from the jar manifest inside that package, not just the
  filename:
  ```
  Implementation-Title: ThingsBoard
  Implementation-Version: 4.3.1.5
  Start-Class: org.thingsboard.server.ThingsboardServerApplication
  Spring-Boot-Version: 3.5.15
  ```
  This is the real open-source CE server artifact (CE is what ThingsBoard
  publishes on its public GitHub releases; Professional/Cloud are not
  distributed this way), not a repackaged PE build.
- **Runtime:** ephemeral sandboxed container for this session (not the
  user's machine, not any shared or production environment). OpenJDK
  21.0.10, PostgreSQL 16.13 (freshly initialized, local, port 5433,
  synthetic password), `queue.type=in-memory` (TB CE's own single-node
  default; no external message broker was reachable in this container --
  see "What running Kafka would and would not have changed" below for
  why this doesn't weaken the finding).
- **Extraction method:** `dpkg-deb -x` (file extraction only -- the
  package's `postinst`/systemd/service-account maintainer scripts were
  **not** run, so nothing was installed system-wide or as a service;
  the jar was launched directly with `java -jar`).
- No TB CE source file was viewed as source and then edited to make any
  of this work. Every capability exercised is unmodified, off-the-shelf
  CE behavior reached through its public REST API.

## What was tested and how

All commands were run against `http://127.0.0.1:8082` (local to the
container). Full command transcript is in `commands.log` alongside this
report; the summary below is condensed.

### 1. Install and start (smallest runnable proof, step 1)

```
java -cp thingsboard.jar -Dloader.main=org.thingsboard.server.ThingsboardInstallApplication \
     -Dinstall.data_dir=<data> -Dinstall.load_demo=false \
     -Dspring.jpa.hibernate.ddl-auto=none -Dinstall.upgrade=false \
     org.springframework.boot.loader.launch.PropertiesLauncher
# => "Installation finished successfully!"

SPRING_DATASOURCE_URL=jdbc:postgresql://127.0.0.1:5433/thingsboard \
SPRING_DATASOURCE_USERNAME=postgres SPRING_DATASOURCE_PASSWORD=<synthetic> \
TB_QUEUE_TYPE=in-memory SERVER_PORT=8082 \
java -Dinstall.data_dir=<data> -jar thingsboard.jar
# => "Started ThingsboardServerApplication v4.3.1.5 using Java 21.0.10 ... in 28.8s"
```

Two real failures were hit and fixed along the way (both are useful
findings in their own right, recorded under "Operational notes"):
`cfRocksDb` (the new-in-4.3 Calculated Fields feature) failing to open
its local RocksDB state store under `${user.home}/.rocksdb` on first
boot, and a `TbCreateAlarmNode` config field (`propagateToOwnerHierarchy`)
that does not exist on this version's node schema, only discovered by
the server's own `RuleChainDataValidator` rejecting it against the real
class -- this only confirms the value of testing against the real
version rather than assuming a config shape from memory or an older
minor version.

### 2. Synthetic tenant/device fixtures (documented REST API only)

Created via `/api/tenant`, `/api/user`, `/api/noauth/activate`,
`/api/device`, `/api/device/{id}/credentials` -- all documented,
sysadmin/tenant-admin-scoped REST endpoints:

| Entity | Id (synthetic) |
| --- | --- |
| Tenant A | `spike-tenant-A` |
| Tenant B | `spike-tenant-B` |
| Device A | `spike-tank-sensor-A1`, type `tank-level-sensor`, tenant A |
| Device B | `spike-tank-sensor-B1`, type `tank-level-sensor`, tenant B |

Each device's own per-device access token (its own credential, not a
shared fleet secret) was fetched via `GET
/api/device/{id}/credentials` and used only for that device's own
telemetry posts.

### 3. Rule chain: consume an event, execute the rule engine

Each tenant's default **Root Rule Chain** (already present after tenant
creation -- no custom integration, no PE feature) was extended with two
stock CE rule nodes, wired off the existing "Message Type Switch" node's
"Post telemetry" relation:

- `org.thingsboard.rule.engine.filter.TbJsFilterNode` --
  `return typeof msg.tank_level_percent !== 'undefined' && msg.tank_level_percent > 80;`
- `org.thingsboard.rule.engine.action.TbCreateAlarmNode` -- raises a
  `HIGH_TANK_LEVEL` / `CRITICAL` alarm on the originating device.

This was done entirely through `GET/POST /api/ruleChain/{id}/metadata`
(the same REST surface `docs/tb-ce-inventory.md` Section 2.3 already
inventoried), not by editing TB CE source or config files.

### 4. Event ingestion and rule-engine execution

```
POST /api/v1/{deviceAccessToken}/telemetry
{"ts": 1790000060000, "values": {"tank_level_percent": 93.4, "temperature_c": 19.0}}
```

Result: `HTTP 200`; querying `GET /api/alarm/DEVICE/{deviceId}` ~3s later
returned:

```json
{"type": "HIGH_TANK_LEVEL", "severity": "CRITICAL", "status": "ACTIVE_UNACK",
 "startTs": 1790000120000, "details": {"tank_level_percent": 95.1}}
```

A telemetry value below the threshold (62.5) produced **zero** alarms in
the same check. **This is the core proof: an event that originated
outside TB CE reached TB CE's rule engine and the rule engine executed
real logic (a script filter, then a stateful alarm node) against it,
using only CE-documented capabilities.**

### 5. Tenant and device mapping

- Posting to device B's own token raised an alarm visible only under
  tenant B's own token (`GET /api/alarm/DEVICE/{deviceB}` with tenant A's
  token -> `404 Device ... is not found`, not a 403 with the device's
  data leaked in the error body).
- `GET /api/device/{deviceB}` with tenant A's admin token -> same `404`.
- Device A's own alarm count was unaffected by device B's event (checked
  before/after: 1, then still 1).

Device-to-tenant mapping is enforced by which device access token was
used to authenticate the telemetry post (the token is bound to one
device, which is bound to one tenant at creation time) -- not by any
claim in the payload itself. An external bridge service integrating
IOT-EE with TB CE this way must keep its own per-device, per-tenant
credential map; TB CE will not accept a tenant or device id asserted in
the message body over this API.

### 6. Duplicate delivery

The identical payload (`ts=1790000240000`, `tank_level_percent: 97.0`)
was POSTed three times in a row. Result:

- **Timeseries storage:** exactly one point at that `ts` (last write to
  the same `(entity, key, ts)` overwrites; querying the range afterward
  returns one value, not three).
- **Alarm:** exactly one active `HIGH_TANK_LEVEL` alarm existed
  afterward, not three. But its `endTs` had been bumped forward to the
  wall-clock processing time of the *last* duplicate
  (`1790389149254`, a receive-time value, not the event's own `ts`).

**Finding:** this is not general message deduplication. `TbCreateAlarmNode`
specifically looks up an already-active alarm of the same type on the
same originator and updates it rather than creating a second one; that
is alarm-level upsert behavior built into that one node, not an
at-most-once guarantee for the message pipeline as a whole. The rule
chain still ran all three times end-to-end (three script-filter
evaluations, three alarm-node invocations); a rule chain with a
non-idempotent side effect (an outbound RPC, a webhook call, an
email/SMS action) would fire three times. **TB CE's REST ingestion path
provides no message-id-based deduplication.** The idempotent-consumer
discipline ADR 0012 already assumes has to live upstream of TB CE (in
the bridge or in IOT-EE's own outbox), exactly as already designed --
this spike found nothing that would let that assumption be relaxed.

### 7. Retries and failure recovery

```
$ pkill -f thingsboard.jar   # simulate TB CE outage
$ curl -m5 -X POST http://127.0.0.1:8082/api/v1/<token>/telemetry -d '{...}'
curl: (7) Failed to connect to 127.0.0.1 port 8082 after 0 ms: Couldn't connect to server
(0.009s -- immediate, not a timeout)
```

- The failure is immediate and synchronous: there is no server-side
  receive buffer on this path. A caller that does not itself retry loses
  that event.
- TB CE was restarted (same JVM args, same Postgres, same
  `install.data_dir`) and came back up cleanly in ~29s with all prior
  tenants, devices, rule chains and alarm history intact (Postgres-backed
  state survived the restart, as expected for a stateless-process /
  stateful-database design).
- The event that failed during the outage was replayed manually
  afterward (`POST` the same payload again) and landed normally. **TB CE
  itself has no memory of the outage window and performs no automatic
  replay or gap detection** -- recovering a lost event is entirely the
  external caller's responsibility. This matches, and does not weaken,
  the outbox/idempotent-consumer/replay design already specified in
  ADR 0012 and the device-adapter ADR draft; it does mean that
  responsibility cannot be assumed away by "TB CE will just re-read it
  from Kafka," because on the REST path there is no Kafka to re-read
  from.

## The blocked path, named precisely

What was **not** demonstrated, and is marked **BLOCKED**, is the literal
ADR 0019 architecture: **TB CE, unmodified, subscribing to and consuming
a platform-Kafka-owned topic directly, with no bridge service in
between**, the way a Kafka consumer group would.

**Exact missing dependency:** an external-event-source integration
point in Community Edition. The only place this would live is
`AbstractIntegration` (the pluggable integration framework, gRPC-executor
based, that a custom or remote integration implements). ThingsBoard's own
documentation states plainly, and this spike's own instance confirms by
absence (no Integrations menu/API surface responds as available on this
CE build):

> "This feature is available in ThingsBoard Professional and ThingsBoard
> Cloud only." -- <https://thingsboard.io/docs/user-guide/integrations/>

This was independently re-verified against the live documentation during
this spike (not just carried over from `docs/tb-ce-inventory.md`), and
no CE-only substitute for "subscribe to an arbitrary external Kafka
topic and feed it into the rule engine" was found. The rule engine does
have Kafka/MQTT/RabbitMQ **outbound** action nodes (for the rule chain to
*publish* to an external topic as a side effect) -- that is the opposite
direction from what ADR 0019 needs and does not help here.

**What running an external Kafka broker in this spike would and would
not have changed:** `TB_QUEUE_TYPE=kafka` was not tried in this spike
because no Kafka broker was reachable in this sandboxed container
(package/image registries the container can reach do not include one --
see "Operational notes"). This is a real gap, but it would not have
changed the answer above: `TB_QUEUE_TYPE=kafka` selects the backend for
TB CE's **own internal** queue (`tb_transport.api.*`, `tb_rule_engine`,
`tb_core`, per `docs/tb-ce-inventory.md` Section 2.4), consumed
exclusively by TB CE's own transport/core/rule-engine actors expecting
its own internal `TransportProtos.proto` wire format (tenant ids as
MSB/LSB longs, partition assignment matching TB's own partition service,
etc.). There is no configuration flag that makes TB additionally
subscribe to a second, externally-defined topic and schema as a generic
event source; that is exactly the gap `AbstractIntegration` fills, and it
is PE/Cloud-only. Producing directly onto TB's own internal topic names
in TB's own internal protobuf format, without going through
`AbstractIntegration` or a transport, is *technically* possible without
touching TB CE source, but it is not a documented, versioned, public
integration contract -- it depends on TB CE's internal wire format and
partitioning logic, which can change on any patch release with no
deprecation notice, and was not attempted here because it would be
unsupported, unverifiable against documentation, and the opposite of
what "verify claims against official documentation" asks for. It is
listed here as a theoretical option only, explicitly **not
recommended**.

## Recommendation

**A CE-compatible path is demonstrated, but it is not "TB CE downstream
of Kafka" as ADR 0019 currently states it.** It is: an external Java
bridge service (already implied by ADR 0011 Decision 3's "prefer
external Java services over in-TB modifications", and consistent with
`docs/tb-ce-inventory.md`'s own conclusion in Section 2.2) that:

1. consumes IOT-EE's own Kafka topic(s) as a normal Kafka consumer
   (IOT-EE's own contract, IOT-EE's own schema -- no coupling to TB
   internals);
2. holds its own per-device, per-tenant credential map (device access
   tokens, from the vault per the device-adapter ADR draft);
3. translates each event into a call against TB CE's documented device
   telemetry API (`POST /api/v1/{token}/telemetry`) or the MQTT Gateway
   API (not tested in this spike; also CE-documented and worth a
   follow-up spike if MQTT ingestion specifically is needed);
4. owns retry, backlog and idempotency for that translation step, since
   TB CE provides none of the three on this path (Sections 6 and 7
   above).

This is not a new design -- it is what ADR 0011 Decision 3 already
preferred and what `docs/tb-ce-inventory.md` already flagged as the
consequence of `AbstractIntegration` being PE-only. What this spike adds
is that the bridge pattern is now demonstrated working end-to-end against
the real pinned version, not just argued from documentation, and that
the specific ADR 0019 phrase "TB CE downstream of Kafka" should be
corrected at the owner's next ADR revision to read "an external bridge
service downstream of Kafka, upstream of TB CE" -- **this spike does not
make that edit**, since revising ADR 0019 is a topology decision outside
this spike's scope (the task explicitly excluded changing production
topology from this investigation).

## Explicitly out of scope for this spike (per the task's own bounds)

- No change was made to M9's milestone scope or sequencing. Full legacy
  data import and cutover remain in M9, untouched.
- No production topology or deployment profile was changed. Nothing
  here argues for or against Kafka clustering, multi-cluster, or
  Istio -- this spike is a single local process, not a capacity or
  throughput test, and draws no throughput conclusion.
- ADR 0019 itself was not edited. The correction above is a
  recommendation for the owner's next revision, not applied here.
- `TB_QUEUE_TYPE=kafka` (TB's own internal cluster queue backend) was not
  exercised, for the reason given above (no reachable broker in this
  sandbox) -- flagged as a gap, not silently skipped.
- MQTT Gateway API ingestion was not tested; only the REST/HTTP device
  telemetry path was. If MQTT is the intended transport, that is a
  separate, still-open follow-up.

## Operational notes (useful side-findings, not part of the core claim)

- This container's network allowlist reaches `github.com` /
  `*.githubusercontent.com` (the release `.deb` downloaded cleanly and
  its checksum was recorded) but not Docker Hub, GHCR, Quay, other OCI
  registries, or `apt`/Ubuntu archive mirrors -- a Docker-Compose-based
  TB CE spike was not possible in this sandbox for that reason; the
  `.deb`'s files were extracted directly instead (`dpkg-deb -x`, no
  maintainer scripts run, nothing installed system-wide).
- TB CE 4.3.1.5's new Calculated Fields feature needs a writable local
  RocksDB path (`${user.home}/.rocksdb/...` by default) even when
  Calculated Fields are not otherwise used; first boot failed until that
  directory existed and had no stale lock file. Worth a line in
  `docs/tb-ce-inventory.md`'s "Gaps and unknowns" (Calculated Fields
  execution-model question) since this is a concrete operational
  dependency, not just a rule-chain-semantics question.
- `TbCreateAlarmNode`'s configuration schema at 4.3.1.5 does **not**
  include a `propagateToOwnerHierarchy` field (present in some
  older-version examples found while drafting this spike's rule chain).
  The server's own `RuleChainDataValidator` rejects an unrecognized field
  outright rather than silently ignoring it -- a good sign for
  config-schema discipline on TB CE's side, and a reminder that any
  future Track B code generating rule-chain configs for a specific
  pinned version should validate against that exact version, not an
  example copied from other documentation.

## Cleanup

The TB CE process, its Postgres database, and every synthetic tenant,
device, and credential created for this spike were local to this
session's ephemeral container and are not part of any persisted
environment. No real inventory, credential, or address was used or
stored (ADR 0012 Decision 2; CLAUDE.md secrets/PII rule).
