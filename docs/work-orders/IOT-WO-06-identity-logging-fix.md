# IOT-WO-06: Identity service logging fix (Log4j 2)

**Status:** Approved (owner, 2026-10-20), with ADR `XXXX-proposed-identity-logging-backend.md`, which the owner accepted on 2026-10-20 and which lands as 0027. **Milestone:** MS1 follow-up (runtime correctness).
**Author:** Claude · **Implementer:** Codex, as the Enterprise Senior AI engineer · **Branch:** `codex/iot-wo-06-logging`
**Start gate:** IOT-WO-02 Part B has merged. Log4j 2 is a new runtime component and needs a passing supply-chain gate for its full ADR-0054 record.

## Goal

The identity service logs at runtime through Log4j 2, with the correlation ID on every request log line (ADR 0012 Decision 5). Tests prove the runtime path.

## Scope

1. In `services/identity/pom.xml`:
   - exclude `spring-boot-starter-logging` from every Spring Boot starter that brings it in;
   - add `spring-boot-starter-log4j2`, version managed by the Spring Boot BOM, with the patch floor from ADR 0027 Decision 4;
   - remove the direct test-scope `logback-classic` declaration.
2. Add `src/main/resources/log4j2-spring.xml`, a console appender whose pattern includes the MDC correlation key the service binds. No file appenders, no remote appenders, no JNDI lookups, and no message lookups.
3. Tests:
   - `CorrelationIdHandlerInterceptorTest`'s MDC assertion passes on Log4j 2;
   - a new test asserts exactly one SLF4J provider on the **runtime** classpath (Log4j 2's), and no Logback;
   - a new test asserts that a logged request line contains the correlation ID.
4. Licence gate:
   - register Log4j 2's runtime artifacts with **full, verified** ADR-0054 records (they can't be `legacy-pending`);
   - record Logback's rejection in the climbing evidence;
   - the gate shows Log4j 2 at runtime scope.
5. A CHANGELOG entry, and a short note in `services/identity/README.md`.

## Out of scope

Other services (there are none yet), log shipping, and OpenTelemetry. Those come with MS5 on Twinfra's stack.

## Acceptance

- `mvn -B -f pom.xml verify` passes. Identity tests are 211 plus the new ones, and every ArchUnit and planted test is still green.
- CI is green: `java-platform-bootstrap`, `naming-gate`, `release-checks` and `licence-gate`, plus Part B's gate.
- The PR shows the resolved runtime tree with Log4j 2 present and Logback absent.

### Ruling (architect, 2026-10-21): Log4j 2 version override

The Spring Boot 3.3.4 BOM manages Log4j 2.23.1. ADR 0027 Decision 4 requires the newest Log4j 2.x release at least 14 days old: **2.26.1** (Maven Central, 2026-06-29). Read "patch" in that Decision as "release on the 2.x line".

1. **Override with Log4j's own BOM, imported before Spring Boot's.** The root `pom.xml` imports `spring-boot-dependencies` as a BOM rather than as the parent, so Boot's `log4j2.version` property has no effect (corrected 2026-10-21).
   - In the root `dependencyManagement`, import `org.apache.logging.log4j:log4j-bom:2.26.1` (Apache-2.0) **before** the `spring-boot-dependencies` import. The first import of a managed artifact wins, so every Log4j artifact (`log4j-api`, `log4j-core`, `log4j-slf4j2-impl`, `log4j-jul`, `log4j-to-slf4j`) moves together, with no per-artifact versions.
   - Put the version in a root property (`log4j2.version`) with a comment citing ADR 0027 and this ruling.
   - Show in the PR that the resolved tree has exactly one Log4j version, and that no other Boot-managed version changed.
2. **Compatibility proof.** Spring Boot 3.3's Log4j 2 integration must start with 2.26.1: a test boots the application context with `log4j2-spring.xml` and asserts that the Log4j 2 logging system is active, plus the work order's MDC and correlation tests.
3. **Part C re-evaluates the override.** When the Spring line changes, remove the property if the new Boot BOM manages a Log4j version at least as new; otherwise keep it, with the same proof.
4. **Full records:** Log4j 2.26.1's artifacts are new runtime components, so they need full, verified ADR-0054 records (the 2.x line is in active support), with supply-chain evidence from the merged Part B gate.

### Ruling (architect, 2026-10-21): no Spring Boot starter for Log4j 2

**Codex's stop:** `spring-boot-starter-log4j2:3.3.4` is a new runtime component on a line out of public support (Boot 3.3.x ended 2025-06-19). Its `activitySupport` criterion therefore can't pass, and a new runtime component can't take a legacy admission. Codex was right to stop.

1. **Don't add the starter.** This replaces Scope item 1's "add `spring-boot-starter-log4j2`".
   - Declare instead the three artifacts the starter's 3.3.4 POM lists (Maven Central, checked 2026-10-21): `org.apache.logging.log4j:log4j-slf4j2-impl`, `log4j-core` and `log4j-jul`.
   - Declare them without versions, so the Log4j BOM from the previous ruling manages them at 2.26.1. `log4j-api` arrives transitively, at the same version.
   - The starter JAR is metadata only and holds no classes. Spring Boot picks its Log4j 2 logging system by finding `log4j-core`'s classes on the classpath, not by finding the starter. The previous ruling's item 2 compatibility test proves this.
2. **The gate does not change.**
   - The gate is right to treat any runtime-scope JAR as runtime.
   - There is no "metadata-only" reclassification and no new exemption class, and the starter gets no legacy admission or register entry.
   - A metadata-only rule would need per-release class inspection, and it would open a path for unsupported lines to enter. Not depending on the starter removes the question.
3. **The other parts of Scope item 1 stand:**
   - exclude `spring-boot-starter-logging` from every starter that brings it in;
   - remove the test-scope `logback-classic`.

   The excluded starter also carries `log4j-to-slf4j` and `jul-to-slf4j`, and both must be absent. The single-provider test covers this.
4. **Full records** for `log4j-api`, `log4j-core`, `log4j-slf4j2-impl` and `log4j-jul` at 2.26.1. The previous ruling's item 4 applies unchanged.
5. **PR evidence:** the resolved runtime tree must show:
   - no `spring-boot-starter-log4j2`;
   - exactly the four Log4j artifacts, all at 2.26.1;
   - no Logback, `log4j-to-slf4j` or `jul-to-slf4j`.

   The `pom.xml` comment cites this ruling.
6. **Part C:** a supported Spring Boot line may bring the starter back, but only with its own full record. Otherwise the direct declarations stay.
