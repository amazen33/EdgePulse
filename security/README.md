# Licence gate — IOT-WO-02 Part A

This gate inventories existing EdgePulse build and runtime inputs. It does
not prove a deployment, runtime integration, vulnerability clearance or
milestone acceptance. Merged [PR #48](https://github.com/amazen33/EdgePulse/pull/48)
adds the supply-chain gate and static artifact evidence. Under Amendment 5,
the Java/Spring baseline is Part C, before the Part D quality gate; both
remain incomplete. Existing legacy deadlines and security exceptions retain
their recorded scope and expiry.

## Authority and port

[UPSTREAM.md](UPSTREAM.md) identifies Twinfra commit
`0d950075a8bf43358d9fd406b80b67d657f804e1` and the byte-for-byte first port
commit `eec61fa6d713efd172fbdf17b657d2d1c9233720`. The second commit adds:

- ADR 0024: Maven inventory and EPL-2.0 build tools;
- ADR 0025: enforced test-only modules and the named Jakarta API exception;
- ADR 0026: build-tool licence families and recorded OR elections;
- the work order's known-permissive, invocation-scope, resolved-scope and
  existing-runtime enterprise-grade rulings.

The upstream licence classes, strict SPDX parser, expiring evidence baseline
and unchanged `licence_ladder.py` remain the foundation. AND obligations are
retained. An OR needs a recorded `electedSpdx`; family permissions apply only
to build tools. Unknown, absent or blocked licences cannot enter a baseline.
Full custom permissive texts and exact sources are in
[licences/README.md](licences/README.md). No ThingsBoard code is copied.

## Inventory and scope

`licence-register.json` records every resolved Maven dependency in every
scope; executed plugins and their complete isolated classpaths; Maven build
extensions and native generators; SHA-pinned Actions; pinned CI Python
requirements/tools; migration-contract TOOLS.md inputs; and the binaries,
charts, manifests and images in `dev/kind/pins.json`. The retired own-infrastructure
sources remain in `archive/iot-ee-own-infra` under IOT-WO-07; they are not active
inventory inputs. The collector never invokes Dependency
Plugin 3.7.0 or the `enforcerNegativeTest` diagnostic profile.

The **resolved per-module Dependency Plugin 3.11.0 tree** decides scope.
Per-module CycloneDX 2.9.1 BOMs supply identities, licences and hashes. A
tree/BOM component mismatch fails. A clear resolved scope differing from
the scope-filtered BOM is recorded in `mavenScopeDisagreements`. No scope is
inferred from CycloneDX's `required` component label. Logback's resolved test
scope and identity-JAR inspection are in `logbackPackaging` in the report;
Part A changes no application dependency or packaging behaviour.

The invocation guard checks every workflow run step and every collector
command against `licence-policy.json.gatedMavenCommands`. New phases, goals,
properties, POMs or profiles fail until reviewed. The effective POM and
plugin descriptors identify reached lifecycle bindings. The gate blocks an
excluded plugin becoming active and any unregistered classpath component.
[maven-unexecuted-plugins.json](maven-unexecuted-plugins.json) records the
excluded plugins, bindings, reasons and evidence dates without giving them
a licence class. Site, Invoker and Dependency 3.7.0 remain excluded.

`architecture` and `contract-tests` are test-only modules. Their active,
inherited Enforcer fences and resolved consumers are checked. The latter
cannot be consumed in any scope. Build tools must not be shipped-reachable
or packaged. Thin JARs, nested dependency JARs and the identity manifest
classpath are inspected; current checks also reject bundled build-tool
classes. Adding a test-only module needs architect review.

## Evidence still due

The existing runtime/input set uses the port's exact `legacy-pending`
mechanism, with immutable fingerprints and **2027-04-20** due dates. The PR
lists the full set; **owner approval of that PR approves that list**.
Changing a fingerprint or adding a runtime component requires full verified
enterprise-grade criteria. A deadline extension fails. Part B stores scan
evidence separately; no criterion is attached to a legacy-pending entry.
Supported Part B replacements and Part C upgrades require full records, not
legacy admission. Build and test-only components have no enterprise-grade record.

Jakarta Annotations is an unmodified linked API JAR, elected EPL-2.0 under
ADR 0025. Its exact upstream source is recorded. It is **not a separate
unit**: the register says `separateUnit: false`. A follow-up ADR and full
tier-3 evidence are required before 2027-04-20. OpenBao's historical Twinfra
MPL exception remains visible in the policy; no OpenBao component is used
or registered by this repository's current inputs.

The original seven image inputs had reviewed digest-bound SBOM paths and hashes in
the register; [backfill evidence](evidence/supply-chain/image-backfills-2026-10-20.json)
records the exact transitions and [scan evidence](evidence/supply-chain/scan-summary-2026-10-20.json)
lists their removed baseline IDs. Six unchanged images add only `imageSBOM`;
the supported minimal PostgreSQL replacement retires its old legacy admission
and has full criteria. This is static artifact evidence. The primary image
project licence does not independently clear its OS or transitive packages.

## Run the gate

Use Python or `py -3` on Windows. Maven is downloaded into the repository's
ignored `target/licence-tools/` directory with a verified SHA-256; no host
configuration is changed. On Windows, pass that Maven's `bin/mvn.cmd` path
to `--mvn`, or put its bin directory on the current process PATH. In CI,
the bootstrap writes its bin path to `GITHUB_PATH`.

```text
python -m pip install -r security/requirements.txt
python security/bootstrap_maven.py
python security/maven_commands.py
python -m unittest discover -s security/tests -v
mvn -B -f pom.xml verify
python security/collect_maven.py
python tools/ci/edgepulse_supply_chain.py verify-manifests
python tools/ci/stage_tools.py --source . --destination target/scan-tools --only syft grype osv-scanner
python tools/ci/edgepulse_supply_chain.py image-sboms
python security/check_licences.py --report target/licence/report.json
```

Evidence, BOMs and trees are generated under the reactor modules' ignored
`target/` directories. The report records counts, every component, scope
disagreements, packaging observations, open baselines and legacy deadlines.
CI runs the blocking job **`licence-gate`**, separately from existing
`java-platform-bootstrap`, `naming-gate` and `release-checks`. Required check names are unchanged; agents do not edit the ruleset.

The SBOM commands use Linux CI binaries and an integrity-checked Syft cache;
they run without a container engine. On Windows use reviewed artifact files
at their registered paths for the offline checker. Never substitute an empty
or fallback SBOM to satisfy a hash check.

The planted tests cover the work order's six Amendment 3 cases, four
Amendment 4 cases, three legacy-ratchet cases, missing full LicenseRef text,
four invocation-scope cases, scope disagreement and tree/BOM mismatch,
plus packaging, election and baseline protections. They use synthetic data.

## EdgePulse supply-chain schema extension

The owner-approved Part B wiring extension changes only the `workOrder`
pattern in `vulnerability-exceptions.schema.json` to
`^IOT-WO-[0-9]{2}( Part [A-Z])?$`. EdgePulse exceptions name their own
remediation orders, such as `IOT-WO-08` and `IOT-WO-02 Part C`; bare
Twinfra forms such as `WO-08` are rejected because their numbers collide
with different Twinfra orders. The unchanged first port is commit
`0a5a2f1`; `tools/ci/supply_chain.py` remains unchanged. The extension and
its planted tests are in the EdgePulse wiring commits. The upstream
proposal generator's bare work-order output is rejected by this schema;
the EdgePulse adapter suppresses those proposals.

[IOT-WO-08](../docs/work-orders/IOT-WO-08-image-and-dependency-refresh.md)
defines the image and dependency refresh due 2026-11-19. Initial exception
approval for the exact 303-entry list was given explicitly by the owner
on 2026-10-20 ([record](evidence/vulnerability-exceptions/owner-approval-2026-10-20.json)).
Human PR review and merge remain separate owner actions.

## IOT-WO-06 ruling 2026-10-21

The owner-approved extensions live only in EdgePulse wiring. The ported
checker, licence ladder and schemas retain their existing bytes.

Imported POM-only BOMs are build-tool inputs. `ImportedBoms.java` uses the
registered Maven 3.9.11 model builder offline to enumerate every import,
including nested imports and parent models of reactor dependencies and
executed plugin classpaths, and obtains the effective POM
licence declarations. The collector hashes exact POM bytes and compares
the resulting managed model with the gated Maven effective model. This
does not execute another Maven goal or add a tool/dependency. Unreviewed
licence declarations and model disagreements fail closed. Reviewed OR
elections are bound to exact POM hashes and declarations in
`maven-bom-licence-evidence.json`. An import cannot authorize a runtime or
packaged coordinate; both paths fail. New explicit gated profiles require
a matching model request before the collector can admit their inputs.

Legacy admission retirement is removal-only: the component must be absent
from independently resolved inputs. IOT-WO-06 retires the four admissions
for Log4j API 2.23.1, log4j-to-slf4j 2.23.1, jul-to-slf4j 2.0.16 and
spring-boot-starter-logging 3.3.4. The two test-only Logback 1.5.38 entries
also leave the register. Retained legacy fingerprints and deadlines stay
unchanged, with no new legacy admission. Part B's seven image evidence
transitions and supported-line replacement checks still apply.

Planted tests reject missing BOM registration, runtime/package reachability,
omitted BOM evidence, retirement while a component remains resolved, and
any new or altered legacy admission; an absent-component retirement passes.

## ADR 0028: test-harness image class

`security/supply-chain-policy.json` lists the five architect-reviewed harness
repositories. This vulnerability class is independent of licence classes:
all licence records, image pins, SBOM requirements and upstream tool bytes stay
unchanged. EdgePulse's `edgepulse_harness.py` wiring checks tracked references,
packaging inputs, transitive workflow callers, effective permissions and secret
references before a finding can receive the class. Documentation links to the
harness do not package an image; literal harness image references in charts fail.

The blocking supply-chain gate and nightly scan still scan every image and
check the current CISA KEV catalogue. Harness KEV findings cannot be excepted.
Fixed Critical/High harness findings appear in a separate report-only section
with the original first-seen state, before the general findings table. The
unchanged trusted reporter carries this section into the single nightly issue;
full findings and SBOMs remain in the run artifact. TB, PostgreSQL and Maven
findings retain strict ADR-0049 handling.

Every gate/nightly/weekly run checks official release metadata live. The
14-day eligibility cutoff and the strictly-more-than-30-day publication-age
limit use UTC. Kind node candidates come from kind release notes for the pinned
Kubernetes minor; Cilium and its bundled Envoy follow the pinned Cilium minor;
CNPG uses published stable operator releases. A newer release does not reset
the clock of any older eligible, unadopted release. Missing or uninterpretable
publication evidence fails closed. The report records source hashes and dates.

A stale candidate blocks until adoption or a reviewed `ownerReasons` record
in the policy identifies its exact repository/release, owner `amazen33`, date
and reason. There are no owner overrides in this change. KEV cannot be waived
by such a record. Weekly comparison scans retain their upstream logic; the
EdgePulse wrapper adds the same isolation, KEV and staleness checks.

Amendment 1 removes exactly 266 `IOT-WO-08` harness exceptions. The remaining
36 entries preserve their exact bytes and order. The repository regression
test compares them with immutable base `c126d1e`; the removal list is in
`security/evidence/iot-wo-08/harness-reclassification-2026-10-21.json`.

## IOT-WO-08 Amendments 2 and 3: paused kind and TB qualification

The kind node is absent from active image inputs while its Brotli KEV is
unfixed. `dev/kind/rehearsal-pause.json` records its historical identity and
the restore duty; `kind-smoke` is explicitly skipped and local up, install
and smoke scripts refuse before engine access. Chart renders and context
guard tests still run. The harness policy still has five repositories;
four are active. KEV rules and the upstream tools remain unchanged.

The weekly watch scans official node candidates on Kubernetes 1.36 with
the pinned scanners, retaining the SBOM, scan and KEV evidence. It reports
availability only when the image contains the fixed Brotli version and no
KEV finding. Restore rehearsal through review within 14 days of the first
verified fixed publication; a newer candidate does not reset that clock.

TB 4.3.1.8 replaces the old digest with a full ADR-0054 record.
The [supplier review](evidence/iot-wo-08/tb-4.3.1.8-qualification-2026-10-30.md)
lists the five primary-source criteria accepted in the recorded E-3 review.
The sixth, `supplyChain`, cites the
[green Linux ADR-0049 run](https://github.com/amazen33/EdgePulse/actions/runs/41098298463).
The [green TB comparison](https://github.com/amazen33/EdgePulse/actions/runs/41098298743)
scans both complete images with one database snapshot and rejects new fixable
Critical/High identities. The reviewed generated imageSBOM hash is bound to
the new digest. Final architect diff review and owner merge remain pending;
these records prove static artifact qualification, not runtime integration.

The immutable pre-approval OpenJDK rows stay in
`vulnerability-exception-proposals/iot-wo-08-tb-openjdk-2026-10-30.json`,
with empty `approvedBy`. Under A-1, exactly two copies were added to the
active ledger, changing only `approvedBy` to `amazen33`; the original 36
active rows are unchanged. Starting TB anywhere before the fixed upstream
image voids both approvals. They expire 2026-11-19, with no extension, and
do not cover the two OpenJDK Highs that become blocking on 2026-11-05.
Separate A-2 proposals are due by 2026-11-03 unless an upstream fix clears
them. No High approval is granted by the Critical disposition.
The two absent old image admissions are retired under the existing
removal-only rule; [their record](evidence/iot-wo-08/retired-image-admissions-2026-10-30.json)
preserves their old fingerprints. Every retained legacy deadline and
fingerprint stays unchanged. Nothing is deployed or accepted as MS3.

## IOT-WO-08: os-maven-plugin removal

The identity build no longer loads the os-maven-plugin 1.7.1 extension,
which has no newer release and whose classpath carried plexus-utils 3.1.0
(CVE-2025-67030, High). Two OS-activated profiles in
`services/identity/pom.xml` set `os.detected.classifier` to
`linux-x86_64` or `windows-x86_64`, the two classifiers the collector
already inventories for protoc and protoc-gen-grpc-java. Other platforms
have no inventoried generator binary and fail to resolve. The twelve
build-tool records found only on that classpath leave the register
removal-only, and the cleared exception is removed; the
[record](evidence/iot-wo-08/os-maven-plugin-removal-2026-11-01.json)
keeps their exact bytes. No component or exception is added.
