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

The seven active images have reviewed digest-bound SBOM paths and hashes in
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
