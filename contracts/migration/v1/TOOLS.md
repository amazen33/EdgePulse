# Test tools and dependency inventory (MR-14 / MR-7)

Contract: **v1.0.0-draft**. **Licence and supply-chain gates: pending IOT-WO-02**.
This is the input inventory for that register, not a claim that its gates ran or
passed. Leaving `-draft` requires those gates after IOT-WO-02 merges. All added
libraries are test-scope only and permissively licensed (tiers 1/2). None runs
in a platform service. No Node, Spectral, TB source code or consumer code is added.

## Direct additions

- Swagger Parser `io.swagger.parser.v3:swagger-parser:2.1.24`, Apache-2.0 (tier 2),
  published by 2024-11-18. OpenAPI 3 parser/validator plus local JUnit lint rules.
  The unused Swagger 2 converter is explicitly excluded. Version and inherited
  licence: [official parent POM](https://repo.maven.apache.org/maven2/io/swagger/parser/v3/swagger-parser-project/2.1.24/swagger-parser-project-2.1.24.pom).
- Java JSON Canonicalization `io.github.erdtman:java-json-canonicalization:1.1`,
  Apache-2.0 (tier 2), published by 2018-08-18. JCS at test scope, verified against
  RFC 8785 vectors; fixed scalar framing is described in digest-spec.md.
  [Official POM](https://repo.maven.apache.org/maven2/io/github/erdtman/java-json-canonicalization/1.1/java-json-canonicalization-1.1.pom).

The dates below are the official Maven Central POM Last-Modified publication
bounds, read on 2026-10-19. All are earlier than the 14-day cutoff 2026-10-05.
Coordinates provide exact artifact identity for the future register. Shared
versions remain fixed by the existing Spring Boot 3.3.4 BOM; additions use exact
release versions, never ranges or snapshots.

## Resolved parser/JCS library inventory

| Exact Maven coordinates (group:artifact:version) | Licence option / tier | Available by (UTC) |
| --- | --- | --- |
| `io.swagger.parser.v3:swagger-parser:2.1.24` | Apache-2.0, tier 2 | 2024-11-18 |
| `io.swagger.parser.v3:swagger-parser-v3:2.1.24` | Apache-2.0, tier 2 | 2024-11-18 |
| `io.swagger.core.v3:swagger-models:2.2.26` | Apache-2.0, tier 2 | 2024-11-18 |
| `io.swagger.core.v3:swagger-core:2.2.26` | Apache-2.0, tier 2 | 2024-11-18 |
| `jakarta.xml.bind:jakarta.xml.bind-api:4.0.2` | BSD-3-Clause (EDL-1.0), tier 1 | 2024-02-19 |
| `jakarta.activation:jakarta.activation-api:2.1.3` | BSD-3-Clause (EDL-1.0), tier 1 | 2024-02-15 |
| `org.apache.commons:commons-lang3:3.14.0` | Apache-2.0, tier 2 | 2023-11-18 |
| `io.swagger.core.v3:swagger-annotations:2.2.26` | Apache-2.0, tier 2 | 2024-11-18 |
| `jakarta.validation:jakarta.validation-api:3.0.2` | Apache-2.0, tier 2 | 2022-05-26 |
| `io.swagger.parser.v3:swagger-parser-core:2.1.24` | Apache-2.0, tier 2 | 2024-11-18 |
| `io.swagger.parser.v3:swagger-parser-safe-url-resolver:2.1.24` | Apache-2.0, tier 2 | 2024-11-18 |
| `commons-io:commons-io:2.17.0` | Apache-2.0, tier 2 | 2024-09-15 |
| `io.github.erdtman:java-json-canonicalization:1.1` | Apache-2.0, tier 2 | 2018-08-18 |

The two Eclipse APIs use the [Eclipse Distribution License 1.0](https://www.eclipse.org/org/documents/edl-v10.php),
a BSD-style permissive licence. This records that permissive option; it does not
substitute for the pending platform licence register or a security clearance.
Their licences are inherited from their official Maven parent POMs. Swagger
artifacts likewise inherit Apache-2.0 from their published project POMs.

## Reused managed baseline (not newly admitted libraries)

- `com.networknt:json-schema-validator:1.5.1` (Apache-2.0), required by the
  amendment; reused from the parent's existing json-schema-validator.version.
- Jackson databind/core/annotations/dataformat-yaml/jsr310 `2.17.2` (Apache-2.0),
  SnakeYAML `2.2` (Apache-2.0), SLF4J API `2.0.16` (MIT), and
  `com.ethlo.time:itu:1.10.2` (Apache-2.0): the existing managed parser/schema stack.
- The parent already supplies JUnit Jupiter `5.10.3` and Platform `1.10.3`
  (EPL-2.0), OpenTest4J `1.3.0` and API Guardian `1.1.2` (Apache-2.0), and ArchUnit
  `1.3.0` (Apache-2.0). No JUnit or test-framework version is introduced or changed
  by this work order. The new module inherits the existing JUnit as the amendment
  directs; this is not a tier-1/2 admission of a new EPL dependency.
- Existing Maven build plugins: compiler `3.13.0`, Surefire `3.3.1`, Enforcer
  `3.5.0`, protobuf plugin `0.6.1` / protoc `3.25.5`; no versions changed.
  Their existing coordinates remain in the root and identity POMs. Enforcer's
  new rule uses that existing plugin. The empty contract-test JAR contains no
  main classes and is forbidden as a dependency in every scope.
- Diagnostic graph command: `org.apache.maven.plugins:maven-dependency-plugin:3.7.0:tree`
  (Apache-2.0), an existing Maven diagnostic plugin; not added to CI or a runtime.
  JDK SHA-256, UTF-8, epoch-time conversion and sorting use the existing Java 17
  target's standard library, with no cryptography dependency added.

## CI action pins

Only the existing required platform workflow's action references are changed;
no new action or job is introduced. Exact immutable pins, MIT (tier 1):

| Action | Exact version | Source commit | Commit date (UTC) |
| --- | --- | --- | --- |
| actions/checkout | v5.0.0 | `08c6903cd8c0fde910a37f88322edcfb5dd907a8` | 2025-08-11 |
| actions/setup-java | v4.7.1 | `c5195efecf7bdfc987ee8bae7a71cb8b11521c00` | 2025-04-08 |

Both pins are over 14 days old. Sources:
[checkout](https://github.com/actions/checkout/tree/08c6903cd8c0fde910a37f88322edcfb5dd907a8),
[setup-java](https://github.com/actions/setup-java/tree/c5195efecf7bdfc987ee8bae7a71cb8b11521c00).
The existing release-checks workflow already uses an immutable action SHA.
No action was taken against a deployment, host, vault, WSL distro or consumer.
