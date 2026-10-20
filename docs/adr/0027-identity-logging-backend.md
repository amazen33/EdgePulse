# ADR 0027: Logging backend for EdgePulse services: Log4j 2, chosen by the licence ladder

**Status:** Accepted (owner, 2026-10-20). It lands as 0027.
**Applies:** Twinfra ADR-0054 (the licence ladder), ADR 0021 Decision 3, and ADR 0012 Decision 5 (correlation IDs in logs).

## Context

IOT-WO-02 Part A (PR #46) confirmed a latent bug. `services/identity/pom.xml` declares `ch.qos.logback:logback-classic` directly at `test` scope, to support `CorrelationIdHandlerInterceptorTest`. Maven's nearest-wins mediation lets that direct declaration override the compile-scope Logback that `spring-boot-starter-logging` brings in. Logback therefore resolves at **test** scope only: it isn't on the identity service's runtime classpath, and the packaged JAR doesn't contain it. At runtime, SLF4J has no provider. The correlation-ID log lines that ADR 0012 requires, and the MDC binding the test asserts, are lost outside tests.

Restoring Logback means shipping it. Logback is `EPL-1.0 OR LGPL-2.1`, and neither option is on the shipped-component permitted list, so it would need a named runtime exception like ADR 0025. ADR-0054's ladder says to choose **the most permissive tier that has a candidate passing the enterprise-grade gate**. Spring Boot officially supports **Log4j 2** through `spring-boot-starter-log4j2`. Log4j 2 is Apache-2.0 (tier 2), hosted by the Apache Software Foundation, under active LTS maintenance, with a published security process. It is that candidate, and it needs no exception.

## Decision

1. **Log4j 2 is the logging backend for EdgePulse's Spring Boot services.** In each service, exclude `spring-boot-starter-logging` and add `spring-boot-starter-log4j2`. Services keep logging through the SLF4J API.
2. **Fix the identity service now:**
   - remove the direct test-scope `logback-classic` declaration;
   - switch to Log4j 2;
   - add a Log4j 2 configuration whose pattern includes the correlation ID from the MDC (`%X{correlationId}`, or the key the service binds).
3. **Tests must prove the runtime path, not only the test classpath:**
   - `CorrelationIdHandlerInterceptorTest` keeps asserting the MDC binding against Log4j 2;
   - a new test asserts that the resolved runtime classpath contains exactly one SLF4J provider, Log4j 2's;
   - the licence gate shows Log4j 2's artifacts at runtime scope.
4. **Version and supply chain:** the newest Log4j 2 patch that is at least 14 days old, at or above every version with a known critical CVE (for example the 2021 Log4Shell series). It enters the register as a new runtime component, so it needs **full** ADR-0054 records with every criterion verified, including a passing IOT-WO-02 Part B supply-chain gate. It can't use `legacy-pending`.
5. **Logback is not shipped.** No runtime exception is created for it. If Logback stays anywhere at test scope, it remains `build-tool`.
6. **Climbing record:** Logback (tier 3) was rejected because a tier-2 candidate passes the gate. Record that in the register's climbing evidence for logging.

## Consequences

- The identity service logs again, with correlation IDs, through an Apache-2.0 backend, and no licence exception is needed.
- New services follow the same rule (Decision 1). ArchUnit or Enforcer can ban `logback-classic` at runtime scope.
- Log4j 2's history (CVE-2021-44228) is the reason for Decision 4's version floor and full supply-chain evidence. The patched 2.x line is the current, supported release.

## Alternatives considered

- **Ship Logback under a named EPL-1.0 exception.** Rejected: the ladder requires the tier-2 candidate when one passes the gate.
- **`java.util.logging` through `slf4j-jdk14`.** Rejected: weaker MDC support, which ADR 0012's correlation logging depends on, and unusual in Spring Boot operations.
- **Leave it as it is.** Rejected: the service silently loses its required correlation logs.
