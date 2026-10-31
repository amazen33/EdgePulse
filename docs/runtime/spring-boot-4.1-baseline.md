# Spring Boot 4.1 runtime baseline — IOT-WO-02 Part C

IOT-WO-02 Amendment 6 moves `services/identity` to a supported Spring line:

| Component | Before | After | OSS support |
| --- | --- | --- | --- |
| Java (build and CI) | 21 | 21, unchanged ([evidence](java21-baseline.md)) | — |
| Spring Boot | 3.3.4 | **4.1.2** | 4.1.x to 2027-07-31 |
| Spring Framework | 6.1.13 | **7.0.10** | 7.0.x to 2027-07-31 |
| Spring Cloud BOM | 2023.0.3 | removed (unused) | — |
| Tomcat (embedded) | 10.1.60 override | **11.0.27**, from Boot's BOM | 11.0.x supported |
| Jackson (runtime) | 2.17.2 | **3.1.7** (`tools.jackson`), annotations 2.21 | 3.1 and 2.21 are LTS |
| Micrometer | 1.13.4 | **1.17.2** | 1.17.x to 2027-07 |
| Commons Logging | `spring-jcl` 6.1.13 | **1.4.0** (root POM override) | current release |
| Log4j | 2.26.1 override | 2.26.1 override, kept (Boot manages 2.25.5, below the ADR 0027 floor) | — |

Support dates come from the Spring, Micrometer, Tomcat and Jackson support
pages, as recorded in the
[qualification record](../../security/evidence/iot-wo-02-c/qualification-2026-10-31.md).
The Spring calendars are retained in
`security/evidence/iot-wo-02-c/trial-2026-10-31/`.

## Code and configuration changes

- `application.yml` becomes `application.properties` with the same keys and
  values. SnakeYAML is excluded from the shipped runtime because it can't
  pass ADR-0054's governance and security-process criteria.
- `json-schema-validator`, `jackson-databind` 2.x and `jackson-dataformat-yaml`
  move to test scope. Only `CfgSchemaValidationTest` uses them. They return
  to compile scope, with full ADR-0054 records, when main code reads
  `cfg.yaml`.
- `spring-boot-starter-webmvc-test` replaces `spring-boot-starter-test`.
- JSpecify is excluded under the IOT-WO-08 annotation-only ruling
  ([evidence](../../security/evidence/iot-wo-02-c/trial-2026-10-31/jspecify-1.0.1-annotation-only.json)).
- `protobuf-java-util` is pinned to `${protobuf.version}` (3.25.9), so Boot
  4.1's BOM does not split the protobuf family. `grpc-bom` 1.84.0 is imported
  before Spring Boot's BOM.
- Already admitted versions are pinned and unchanged: `gson` 2.10.1,
  `j2objc-annotations` 1.3, `slf4j-api` 2.0.16, Jakarta Annotations 2.1.1
  (the ADR 0025 exception).

## Gates

- Licence gate: 30 new runtime components carry ADR-0054 records, with
  evidence in the qualification record. The 22 Spring Boot, Spring Framework
  and Micrometer records keep `maturity: pending` until ADR 0014's 14-day
  cool-off ends on **2026-11-05**. Departed runtime components are retired
  removal-only ([record](../../security/evidence/iot-wo-02-c/legacy-retirements-2026-10-31.json)).
  New imported BOMs and test-scope libraries are build-tool entries; the six
  reviewed BOM licence declarations are in `security/maven-bom-licence-evidence.json`.
- Supply-chain gate: the 16 `IOT-WO-02 Part C` exception rows are removed.
  The identity runtime has zero OSV findings on the 30 new components
  ([scan record](../../security/evidence/iot-wo-02-c/scan-2026-10-31.json)).
  The Guava High that remains belongs to IOT-WO-08.

## Limits

These are build, unit, boundary and static-scan results. They do not accept
MS1, deploy anything or prove a real-environment integration. MS1 still needs
Part D (the quality gate) and its receipt.
