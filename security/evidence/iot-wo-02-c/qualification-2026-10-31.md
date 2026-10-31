# Part C runtime qualification: the Spring Boot 4.1 line (2026-10-31)

IOT-WO-02 Amendment 6. This record covers the 30 shipped runtime components
that the Spring Boot 4.1.2 line adds or changes in `services/identity`. These
are supplier reviews and static artifact inputs, not EdgePulse runtime or
milestone acceptance. Sources were read on 2026-10-31 and 2026-11-01
(Africa/Cairo); machine criterion dates use the UTC review and scan date,
2026-10-31. Nothing was deployed or run against an environment.

Per-component JAR hashes, the scanned SBOM, OSV results and tool versions
are in [the scan record](scan-2026-10-31.json). All 30 JAR hashes match the
gate's CycloneDX BOM for `services/identity`, and each has **zero OSV
findings and no exception**.

## Cooling-off status

ADR 0014 gives releases a 14-day cool-off, expedited only for KEV or actively
exploited issues. None of the 16 retired Part C findings is in KEV, so no
expedite applies and none is claimed.

| Project | Exact release | Maven Central publication (UTC) | Cool-off met |
| --- | --- | --- | --- |
| Spring Boot | 4.1.2 | 2026-10-22T12:04:04Z | **from 2026-11-05** |
| Spring Framework | 7.0.10 | 2026-10-22T07:46:54Z | **from 2026-11-05** |
| Micrometer | 1.17.2 | 2026-10-22T07:26:55Z | **from 2026-11-05** |
| Apache Tomcat | 11.0.27 | 2026-10-06T18:35:11Z | yes |
| Jackson 3 (`tools.jackson.core`) | 3.1.7 | 2026-09-21T23:36:12Z (core), 2026-09-22T00:27:17Z (databind) | yes |
| Jackson annotations | 2.21 | 2026-01-18T22:47:14Z | yes |
| Apache Commons Logging | 1.4.0 | 2026-06-11T20:49:26Z | yes |
| Protobuf Java util | 3.25.9 | 2026-03-25T22:49:32Z | yes |

The Spring Boot, Spring Framework and Micrometer records therefore carry
`maturity: pending` until 2026-11-05. Their other five criteria pass now.
The maturity result is changed to `pass`, with that date, only on or after
2026-11-05; the licence gate fails until then, by design.

## Spring Boot 4.1.2

Thirteen modules: `spring-boot`, `-autoconfigure`, `-starter`, `-starter-web`,
`-starter-jackson`, `-starter-tomcat`, `-starter-tomcat-runtime`, `-jackson`,
`-http-converter`, `-servlet`, `-tomcat`, `-web-server`, `-webmvc`.
Apache-2.0, tier 2 ([tagged LICENSE](https://github.com/spring-projects/spring-boot/blob/v4.1.2/LICENSE.txt)).

- **Maturity:** a final GA patch of the 4.1 line (first released 2026-06-30),
  not a milestone or release candidate. The cool-off is met from 2026-11-05
  (see above).
- **Governance:** maintained by the Spring team at Broadcom under the
  published [Spring support policy](https://spring.io/support); commercial
  support exists alongside OSS support.
- **Activity/support:** the [project support calendar](https://spring.io/projects/spring-boot#support)
  (retained as `trial-2026-10-31/calendar-spring-boot.json`) gives 4.1.x OSS
  support until 2027-07-31 and commercial support until 2028-07-31. No 3.x
  line has OSS support left.
- **Security process:** the [Spring security policy](https://spring.io/security-policy)
  provides private reporting and published advisories. [OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/spring-projects/spring-boot):
  5.6, dated 2026-10-19.
- **Supply chain:** see the scan record; zero findings, no exceptions.
- **Adoption:** Apache Camel publishes and maintains
  [Camel Spring Boot](https://camel.apache.org/camel-spring-boot/latest/) LTS
  lines on Spring Boot. This shows ecosystem adoption, not use of this exact
  patch elsewhere.

## Spring Framework 7.0.10

Seven modules: `spring-core`, `-beans`, `-context`, `-aop`, `-expression`,
`-web`, `-webmvc`. Apache-2.0, tier 2 ([tagged LICENSE](https://github.com/spring-projects/spring-framework/blob/v7.0.10/LICENSE.txt)).

- **Maturity:** a final GA patch of the 7.0 line (first released 2025-11-30).
  The cool-off is met from 2026-11-05.
- **Governance:** the same Spring team and [support policy](https://spring.io/support)
  as Spring Boot.
- **Activity/support:** the [project support calendar](https://spring.io/projects/spring-framework#support)
  (retained as `trial-2026-10-31/calendar-spring-framework.json`) gives 7.0.x
  OSS support until 2027-07-31.
- **Security process:** the [Spring security policy](https://spring.io/security-policy).
  [Scorecard](https://api.securityscorecards.dev/projects/github.com/spring-projects/spring-framework):
  6.2, dated 2026-10-19.
- **Supply chain:** see the scan record.
- **Adoption:** Spring Boot 4.1 is built on Spring Framework 7.0, and the
  Camel Spring Boot lines above depend on it.

## Apache Tomcat 11.0.27

`tomcat-embed-core`, `-el` and `-websocket`. Apache-2.0, tier 2
([tagged LICENSE](https://github.com/apache/tomcat/blob/11.0.27/LICENSE)).

- **Maturity:** stable Servlet 6.1 / Jakarta EE 11 implementation;
  [which version](https://tomcat.apache.org/whichversion.html) lists 11.0.x
  as a supported stable line, with 11.0.27 as the latest release.
- **Governance:** an [Apache Software Foundation project](https://tomcat.apache.org/).
- **Activity/support:** published 2026-10-06, within six months and past
  the cool-off. [Tomcat 11 security fixes](https://tomcat.apache.org/security-11.html)
  are published per release.
- **Security process:** ASF private reporting and the published CVE list
  above. [Scorecard](https://api.securityscorecards.dev/projects/github.com/apache/tomcat):
  6.1, dated 2026-10-26.
- **Supply chain:** see the scan record. This replaces the Part B Tomcat
  10.1.60 records, which leave the runtime.
- **Adoption:** the project's [public adopter list](https://cwiki.apache.org/confluence/display/TOMCAT/PoweredBy),
  and Spring Boot's [servlet documentation](https://docs.spring.io/spring-boot/reference/web/servlet.html)
  names embedded Tomcat as a supported servlet container.

## Micrometer 1.17.2

`micrometer-observation` and `micrometer-commons`. Apache-2.0, tier 2
([tagged LICENSE](https://github.com/micrometer-metrics/micrometer/blob/v1.17.2/LICENSE)).

- **Maturity:** a final patch of the 1.17 line. The cool-off is met from
  2026-11-05.
- **Governance:** maintained by the Micrometer team at Broadcom alongside
  Spring, under the [Micrometer support policy](https://micrometer.io/support/).
- **Activity/support:** that policy lists 1.17.x with OSS support until
  2027-07 and commercial support until 2028-07.
- **Security process:** the project's [security policy](https://github.com/micrometer-metrics/micrometer/security/policy)
  provides private reporting. [Scorecard](https://api.securityscorecards.dev/projects/github.com/micrometer-metrics/micrometer):
  6.0, dated 2026-10-19.
- **Supply chain:** see the scan record.
- **Adoption:** Spring Boot's [metrics documentation](https://docs.spring.io/spring-boot/reference/actuator/metrics.html)
  uses Micrometer as its metrics facade.

## Jackson 3.1.7 and Jackson annotations 2.21

`tools.jackson.core:jackson-core` and `jackson-databind` 3.1.7, and
`com.fasterxml.jackson.core:jackson-annotations` 2.21, which Jackson 3 uses.
Apache-2.0, tier 2 ([tagged LICENSE](https://github.com/FasterXML/jackson-databind/blob/jackson-databind-3.1.7/LICENSE)).

- **Maturity:** final releases, past the cool-off. Since 2.20 the
  annotations artifact carries no patch number by design; 2.21 is the
  annotations release that the Jackson 3.1 line declares.
- **Governance:** FasterXML maintainers; [Tidelift](https://tidelift.com/subscription/pkg/maven-com-fasterxml-jackson-core-jackson-databind)
  offers commercial support for the project.
- **Activity/support:** the [Jackson releases page](https://github.com/FasterXML/jackson/wiki/Jackson-Releases)
  marks 3.1 and 2.21 as LTS lines that are still open. Activity is
  project-level; the exact 3.1.7 patch is dated September 2026.
- **Security process:** the [jackson-databind security policy](https://github.com/FasterXML/jackson-databind/blob/3.x/SECURITY.md)
  provides private reporting and lists supported versions. Scorecard:
  [jackson-databind](https://api.securityscorecards.dev/projects/github.com/FasterXML/jackson-databind)
  7.9, [jackson-core](https://api.securityscorecards.dev/projects/github.com/FasterXML/jackson-core)
  7.2, [jackson-annotations](https://api.securityscorecards.dev/projects/github.com/FasterXML/jackson-annotations)
  7.2.
- **Supply chain:** see the scan record. Jackson 2.17.2 and its datatype
  modules leave the runtime; Jackson 2.x databind and YAML stay in test scope
  only (Amendment 6, item 1).
- **Adoption:** Spring Boot's [JSON documentation](https://docs.spring.io/spring-boot/reference/features/json.html)
  makes Jackson 3 its default JSON library.

## Apache Commons Logging 1.4.0

Apache-2.0, tier 2 ([tagged LICENSE](https://github.com/apache/commons-logging/blob/rel/commons-logging-1.4.0/LICENSE.txt)).

- **Version choice (reviewer: deviation from Amendment 6):** Amendment 6
  names 1.3.6, the version Spring Boot 4.1.2 manages. 1.3.6 was published
  2026-03-04, and the [project page](https://commons.apache.org/proper/commons-logging/)
  lists 1.4.0 as the current release. The root POM overrides to 1.4.0;
  Spring Framework 7.0.10 itself declares 1.3.5. `mvn clean verify` passes
  with 214 identity and 61 contract tests on 1.4.0.
- **Maturity:** a final release, past the cool-off.
- **Governance:** an [Apache Commons](https://commons.apache.org/) component.
- **Activity/support:** 1.4.0 was published 2026-06-11, within six months.
- **Security process:** the [Apache Commons security page](https://commons.apache.org/security.html)
  and ASF private reporting. [Scorecard](https://api.securityscorecards.dev/projects/github.com/apache/commons-logging):
  7.2.
- **Supply chain:** see the scan record.
- **Adoption:** Spring Framework 7.0.10's `spring-core` POM depends on
  Commons Logging ([POM](https://repo.maven.apache.org/maven2/org/springframework/spring-core/7.0.10/spring-core-7.0.10.pom)).
  This replaces the former `spring-jcl` bridge.

## Protobuf Java util 3.25.9

BSD-3-Clause, tier 1. Pinned to `${protobuf.version}` so the protobuf family
stays at one version (Spring Boot 4.1's BOM would otherwise split it).

- **Maturity:** a final 3.x Java maintenance release, published 2026-03-25.
  It is not represented as a release within six months.
- **Governance:** Google maintains [Protobuf](https://github.com/protocolbuffers/protobuf);
  the same supplier review as the already registered `protobuf-java` 3.25.9
  applies ([IOT-WO-08 record](../iot-wo-08/qualification-2026-10-21.md#protobuf-java-3259)).
- **Activity/support:** the [version support page](https://protobuf.dev/support/version-support/)
  lists Java 3.25.x as maintenance-only, with Java 3.x supported until
  2027-03-31.
- **Security process:** the [published security policy](https://github.com/protocolbuffers/protobuf/blob/main/SECURITY.md).
  [Scorecard](https://api.securityscorecards.dev/projects/github.com/protocolbuffers/protobuf):
  6.2.
- **Supply chain:** see the scan record.
- **Adoption:** as for `protobuf-java` in the IOT-WO-08 record.

## Licence ladder

Every component above is tier 1 or tier 2 and needs no climbing record. No
tier-3 or tier-4 runtime component is added. The existing ADR 0025 Jakarta
Annotations exception (2.1.1, pinned) is unchanged.

## Retired runtime components

These leave the shipped runtime and are retired removal-only from the register
and from `ladder.legacy` in `security/licence-policy.json`; see
[legacy-retirements-2026-10-31.json](legacy-retirements-2026-10-31.json).

- Spring Boot 3.3.4 and Spring Framework 6.1.13 (including `spring-jcl`);
- Tomcat 10.1.60 (verified Part B records);
- Jackson 2.17.2 runtime modules and SnakeYAML 2.2;
- Micrometer 1.13.4 and `protobuf-java-util` 3.21.10.

## Findings outside Part C (for IOT-WO-08)

The same scan reports Maven findings that are not Part C components. Each was
first seen before this branch, and the PR does not introduce them:

- Guava 33.6.0-android (identity runtime, via gRPC) and 33.4.8-jre
  (`protobuf-maven-plugin`): GHSA-xxph-c9ww-hj94, High, fixed in 33.7.2,
  first seen 2026-10-28. It blocks from **2026-11-11**.
- `plexus-utils` 3.1.0 (the `os-maven-plugin` 1.7.1 build extension):
  CVE-2025-67030, High, fixed in 3.6.1, first seen 2026-10-20. It blocks
  from **2026-11-03**.
- `commons-lang3` 3.5 (same extension): CVE-2025-48924, Medium, report-only.
