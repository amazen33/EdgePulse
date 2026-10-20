# Resolved-scope and Logback evidence — 2026-10-20

The owner approved the resolved-scope fallback in
[the work order](../../docs/work-orders/IOT-WO-02-gates-and-runtime-baseline.md),
"resolved-scope fallback and the Logback finding". This is local build/test
scope evidence, not a runtime integration or milestone receipt.

The collector uses **Dependency Plugin 3.11.0** resolved trees for scope and
reachability, and per-module **CycloneDX 2.9.1** BOMs for identity, licence
and hashes. Tree/BOM component-set mismatches fail. Clear resolved scopes
that differ from the filtered BOM are reported without failing the gate.

## Logback finding; no behaviour change

In identity, Maven resolves both `ch.qos.logback:logback-classic:1.5.8` and
`ch.qos.logback:logback-core:1.5.8` at **test** scope. The non-test BOM retains
them through Spring Boot's logging path, despite the direct test declaration.
Those two disagreements are recorded in `mavenScopeDisagreements`.

The packaged `edgepulse-service-identity-2.0.0.jar` is a thin JAR. It has:

- no `BOOT-INF/lib` or other nested dependency JARs;
- no manifest `Class-Path` entries;
- no embedded `ch/qos/logback/` classes.

Neither Logback artifact is contained in or referenced by that packaged JAR,
and neither is on Maven's resolved runtime classpath. Both are classified
**build-tool**, electing **LGPL-2.1-only** from EPL-1.0 OR LGPL-2.1-only.
No dependency, source, runtime classpath or packaging behaviour is changed.
Correcting the POM comment or restoring runtime logging is a separate,
owner-approved follow-up; shipping Logback also needs its runtime licence
decision. Part A does not make that change.

[Scope evidence](cyclonedx-scope-conflict-2026-10-20.json) records the actual
resolved scopes, report observations and source hashes. The
[executed plugin graph](maven-dependency-plugin-3.11.0.graph.json) records all
51 components and every edge. It contains no dom4j at any version.
Dependency Plugin 3.7.0 stays unexecuted and unregistered. Full BOMs and logs
are generated under ignored `target/` directories by the documented gate.

## Tool and port evidence

Dependency Plugin 3.11.0 is Apache-2.0; its
[exact published POM](https://repo.maven.apache.org/maven2/org/apache/maven/plugins/maven-dependency-plugin/3.11.0/maven-dependency-plugin-3.11.0.pom)
was available by **2026-05-24 17:19:23 UTC**, read on 2026-10-20.
Its executed classpath is registered under ADR 0026's build-tool families.
Collector plugin publication dates are in `security/tool-publication-evidence.json`.
The original Twinfra port commit `eec61fa6d713efd172fbdf17b657d2d1c9233720`
remains unchanged. Maven is 3.9.11; Java remains 17.

## Local verification scope

- Maven verify: identity **211**, contract tests **61**, architecture **0**;
  zero failures, errors or skips. Architecture is a build-time rule library.
- Licence tests: **32 passed**, including scope-resolution reporting,
  tree/BOM mismatch rejection and the four invocation-scope planted cases.
- Licence audit: **303 components**, zero blocked; 75 legacy entries due
  2027-04-20 and 13 evidence baselines expiring 2027-01-18 remain visible.
- Three Helm profiles, restricted-v2 negative checks and mocked context
  guards pass. No local engine or cluster is contacted.

CI, PR review and owner acceptance are separate evidence. Part B is not
started. No deployment or environment acceptance is claimed here.
