# Licence gate — IOT-WO-02 Part A

This gate inventories existing EdgePulse build and runtime inputs. It does
not prove a deployment, runtime integration, vulnerability clearance or
milestone acceptance. Supply-chain evidence is **pending IOT-WO-02 Part B**;
quality is Part D and the Java/Spring baseline is Part C.

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
charts, manifests and images in `dev/kind/pins.json`. Existing frozen image
references are inventoried too. The collector never invokes Dependency
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
enterprise-grade criteria. A deadline extension fails. Part B supplies the
supply-chain criterion; Part C upgrades require full records, not legacy
admission. Build and test-only components have no enterprise-grade record.

Jakarta Annotations is an unmodified linked API JAR, elected EPL-2.0 under
ADR 0025. Its exact upstream source is recorded. It is **not a separate
unit**: the register says `separateUnit: false`. A follow-up ADR and full
tier-3 evidence are required before 2027-04-20. OpenBao's historical Twinfra
MPL exception remains visible in the policy; no OpenBao component is used
or registered by this repository's current inputs.

Thirteen existing evidence gaps have **2027-01-18** expiry, within 90 days:
three immutable-digest gaps in frozen deploy sources and ten full-image
SBOM gaps. The primary image project licence does not clear its OS packages
or transitive contents. Each gap has an owner, reason and required evidence;
none waives a known blocked licence. Frozen deploy sources are not changed.

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
python security/check_licences.py --report target/licence/report.json
```

Evidence, BOMs and trees are generated under the reactor modules' ignored
`target/` directories. The report records counts, every component, scope
disagreements, packaging observations, open baselines and legacy deadlines.
CI runs the blocking job **`licence-gate`**, separately from existing
`java-platform-bootstrap`, `naming-gate` and `release-checks`. The owner adds
the new job to the ruleset after merge; agents do not edit that ruleset.

The planted tests cover the work order's six Amendment 3 cases, four
Amendment 4 cases, three legacy-ratchet cases, missing full LicenseRef text,
four invocation-scope cases, scope disagreement and tree/BOM mismatch,
plus packaging, election and baseline protections. They use synthetic data.
