# Identity logging qualification and climbing evidence (2026-10-21)

IOT-WO-06 and ADR 0027. Exact candidate: Log4j API, Core, SLF4J 2 provider
and JUL adapter **2.26.1**, Apache-2.0, tier 2. Supplier review and local/CI
code tests establish this bounded qualification; no deployed integration or
milestone acceptance is asserted. Review date is 2026-10-21 in Africa/Cairo;
machine criterion dates use the actual UTC review/scan date, 2026-10-20.

## Qualification criteria

- **Maturity:** the [ASF Log4j project](https://logging.apache.org/log4j/2.x/)
  provides a stable 2.x logging API/implementation. The exact final 2.26.1
  artifacts are published in [Maven Central](https://repo.maven.apache.org/maven2/org/apache/logging/log4j/log4j-bom/2.26.1/),
  dated 2026-06-29 and older than 14 days. This is the release selected by
  the architect's 2026-10-21 ruling; no prerelease is used.
- **Governance:** the same official project is an Apache Software Foundation
  project. Exact Maven POMs and the four JARs carry Apache-2.0 licensing;
  hashes and licence-entry hashes are in the linked scan record.
- **Activity/support:** ASF's [security policy](https://logging.apache.org/security.html)
  directs users from EOL Log4j 1 to Log4j 2 and publishes current 2.x fixes,
  including 2.26.1. The architect's ruling confirms active 2.x support.
  No support claim is made for the retained Spring Boot 3.3 line.
- **Security process:** ASF's policy provides private vulnerability reporting,
  triage guidance and public affected/fixed-version advisories. This is an
  upstream process check, not a claim that all possible vulnerabilities are absent.
- **Supply chain:** the merged Part B gate's [fresh PR scan](https://github.com/amazen33/EdgePulse/actions/runs/39504344710)
  passed. Its exact identity CycloneDX BOM includes all four 2.26.1 JARs;
  SHA-256 values match the reviewed Maven artifacts. OSV produced **zero
  findings for each of the four**; no Log4j exception or legacy admission is
  needed. Existing exceptions for other inputs remain unchanged. Full
  artifact/scan binding, tool versions and hashes are in
  [the scan record](scan-2026-10-21.json).
- **Adoption:** [Elasticsearch's official documentation](https://www.elastic.co/docs/deploy-manage/monitor/logging-configuration/elasticsearch-log4j-configuration-self-managed)
  identifies Log4j 2 as its logging framework, and [Kafka 4.0's shipped configuration](https://github.com/apache/kafka/blob/4.0.0/config/log4j2.yaml)
  configures Log4j 2. These establish ecosystem adoption, not use of this
  exact patch in those systems or an EdgePulse environment.

## Licence ladder / climbing decision

ADR 0027 rejects shipping **Logback, tier 3 (EPL-1.0 OR LGPL-2.1)**: neither
option is on the shipped permitted list, and a tier-2 Apache-2.0 candidate
now passes every qualification criterion. Select Log4j 2; do not create a
Logback runtime exception. Each new register entry links to this decision
in its notes. This is the accepted ADR's selection record, not a fabricated
failure of a lower-tier candidate. The existing old logging entries await
authorized retirement under the Part B transition guard.

## Runtime and compatibility proof

Full Maven verification on CI-matched Temurin 17.0.16+8 passes: identity 214
(211 existing plus three new tests), contract tests 61. Isolated JVM probes
exclude test dependencies, verify one Log4j SLF4J provider, boot the application
context with log4j2-spring.xml and capture a synthetic request log containing
the interceptor's server-issued correlation ID. Only a console appender is
active; JNDI lookup is disabled. No log shipping or environment acceptance is
claimed. [Resolved graph and version comparison](runtime-proof-2026-10-21.json)
show four Log4j artifacts at one version and zero other managed-version changes.

The Log4j BOM's exact POM hash is recorded as a build-time input in the scan
record; registration awaits the explicit BOM-inventory gate ruling. It is not
represented as a runtime JAR or slipped into a legacy admission. No Boot
logging starter is added. Part C must re-evaluate the override and direct
artifact declarations when the Spring line changes.
