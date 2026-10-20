# ADR 0025 (proposed): Test-only reactor modules, and a named runtime exception for `jakarta.annotation-api`

**Status:** Accepted (owner, 2026-10-20). It lands as 0025, after ADR 0024.
**Clarifies:** ADR 0024 (build-tool licences and Maven ecosystem), Decision 2. ADR 0024 itself is not edited.
**Applies:** ADR 0021 Decision 3, and Twinfra ADR-0030 and ADR-0042, in EdgePulse's port only. Twinfra is not changed.

## Context

IOT-WO-02 Part A stopped again on 2026-10-20, after the unchanged port (`eec61fa`, Twinfra `0d95007`), with three components:

| Component | Path | Licence |
| --- | --- | --- |
| `org.junit.jupiter:junit-jupiter-api:5.10.3` | `architecture`, direct, compile scope | EPL-2.0 |
| `org.junit.platform:junit-platform-commons:1.10.3` | `architecture` → junit-jupiter-api, compile scope | EPL-2.0 |
| `jakarta.annotation:jakarta.annotation-api:2.1.1` | `identity` → `spring-boot-starter-web` → `spring-boot-starter` → this, compile scope | EPL-2.0 OR GPL-2.0-only WITH Classpath-exception-2.0 |

- `architecture` is EdgePulse's shared ArchUnit rule library. ADR 0013 permits it only as a test-scope build artifact, and an Enforcer rule already fails the build if any module declares it outside test scope. `contract-tests` (ADR 0022, IOT-WO-03) is test-only in the same way. The ADR 0024 test "not reachable from any module's compile or runtime classpath" reads these modules' own compile classpaths literally, which isn't its intent: neither module is ever shipped.
- `jakarta.annotation-api` is the Jakarta Annotations API (annotation types such as `@PostConstruct`, `@Generated`). It is a small, unmodified API JAR that Spring Boot requires, and it does ship inside the identity service. Twinfra's shipped-component rule (ADR-0030) allows the permitted list only, with one recorded exception (OpenBao, MPL-2.0).

## Decision

1. **Test-only reactor modules.** A reactor module is **test-only** when:
   - every module that depends on it does so at `test` scope, enforced by a Maven Enforcer rule that fails the build otherwise;
   - it produces no image, chart or release archive.

   Today these are `architecture` and `contract-tests`. Every dependency of a test-only module, in any scope, is evaluated as `build-tool` under ADR 0024 Decision 1. ADR 0024 Decision 2's reachability test means reachability from the compile or runtime classpath of a **shipped** module.
   - The licence gate reads the test-only list from the register, and fails if a listed module loses its Enforcer rule or becomes a non-test dependency of any module.
   - Adding a module to the list needs an architect review in its PR.
2. **Named runtime exception: `jakarta.annotation:jakarta.annotation-api`.**
   - EdgePulse elects the **EPL-2.0** option of the dual licence.
   - The JAR is shipped **unmodified**, as a dependency of Spring Boot, and EdgePulse modifies no EPL-licensed file. The EPL-2.0 source-availability obligation is met by pointing to the upstream source of the exact version, which the register records.
   - The exception is per artifact: it covers this artifact only, at any version that keeps the same licence expression, and it is recorded in the register with this ADR's number. It doesn't permit EPL-2.0 for any other shipped component; each needs its own decision.
   - It is reviewed when the Spring line changes in IOT-WO-02 Part C. If the Spring Boot 4 line changes the dependency, the exception is re-checked or removed.
3. **No dependency surgery.** Don't exclude `jakarta.annotation-api` from the Spring starter. Spring needs it, and removing it would change behaviour.
4. **Upstream later.** Together with ADR 0024 Decision 4, the architect proposes the test-only-module rule to Twinfra after v0.1.0. The Jakarta exception is EdgePulse-specific, because Twinfra ships no Java.

## Consequences

- Part A can close with no baseline exception for JUnit, and one named exception for a standard Jakarta API.
- The licence gate now has two kinds of documented exception: OpenBao (Twinfra, carried over) and `jakarta.annotation-api` (EdgePulse). Both are visible in the register with their ADR.
- This is an engineering position, not legal advice. The owner's legal reviewer confirms both before commercial release (ADR-0030).

## Alternatives considered

- **Move `architecture`'s JUnit to `provided` or `test` scope.** Rejected: the rule factories compile against JUnit and ArchUnit APIs, so changing the scope only hides the dependency.
- **A 90-day baseline exception for `jakarta.annotation-api`.** Rejected: it would renew every 90 days for a permanent dependency.
- **Exclude the JAR, or replace Spring.** Rejected: it breaks Spring for no legal gain.
