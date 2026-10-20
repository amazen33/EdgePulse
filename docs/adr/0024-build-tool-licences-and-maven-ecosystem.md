# ADR 0024 (proposed): EPL-2.0 build tools and the Maven ecosystem in EdgePulse's licence gate

**Status:** Accepted (owner, 2026-10-19). Its number is assigned at merge: the next free number on EdgePulse `main` is 0024.
**Applies:** ADR 0021 Decision 3 (Twinfra's licence gate applies to EdgePulse) and Twinfra ADR-0042 (build-time tools), in EdgePulse's port only. **Twinfra is not changed.**

## Context

IOT-WO-02 Part A ports Twinfra's licence checker (`tools/ci/check_licences.py`, register schema and policy at Twinfra `origin/main` `0d95007`). Codex stopped the port on 2026-10-19 with two findings:

1. ADR-0042 lets the `build-tool` class use "the permitted list plus MPL-2.0, LGPL and GPL". **EPL-2.0 is not listed.** The checker rejects EPL-2.0 under both `build-tool` and `weak-copyleft`. EdgePulse's test stack is EPL-2.0: JUnit Jupiter 5.10.3 and Platform 1.10.3 now, and JaCoCo is the coverage candidate for Part D.
2. The register schema and checker have **no `maven` ecosystem**. Twinfra has no Java. They verify build-tool status only for npm (`dev: true`) and binaries (`toolchain.lock.json`).

ADR-0042 justifies its build-tool rule this way: "copyleft obligations attach to distributing or linking the covered work. A tool whose output we do not distribute does not make Twinfra's code subject to its licence." EPL-2.0 is weaker copyleft than GPL, which ADR-0042 already allows for build tools. Its file-level copyleft and its distribution trigger are narrower.

## Decision

1. **EPL-2.0 joins the `build-tool` allow-list in EdgePulse's port**, under ADR-0042's three conditions unchanged:
   - it runs only in CI or on developer machines;
   - it is never copied into an EdgePulse artifact (image, chart, release archive, deployed manifest) and never linked into shipped code;
   - it is used unmodified.

   It stays **blocked** for any deployed or shipped component. AGPL, SSPL, BUSL, Elastic-2.0 and account-gated licences stay blocked in every class.
2. **Maven ecosystem.** Add `maven` to EdgePulse's register schema and collector. The Maven equivalent of npm's `dev: true` is that a component counts as `build-tool` only when all of these hold:
   - it is **test-scoped**, or it is a **Maven build plugin** (or one of its dependencies), according to the CycloneDX SBOM and `mvn dependency:tree`;
   - it is not reachable from any module's `compile` or `runtime` classpath;
   - it is never included in an image or packaged artifact. The gate fails if a later change makes it reachable.

   Everything else is evaluated as a shipped component under the permitted list.
3. **Same semantics otherwise.** The port keeps Twinfra's classes, SPDX evaluation, baseline, ratchet and 90-day rule unchanged. The two additions are marked in the code as EdgePulse extensions, with this ADR's number.
4. **Upstream later.** After Twinfra v0.1.0 (its `main` is frozen from about 10-31 until the release), the architect proposes the same EPL clarification to Twinfra as an ADR-0042 amendment. If Twinfra decides differently, EdgePulse follows that decision with a superseding ADR.
5. **No framework or coverage swap.** JUnit stays. JaCoCo is permitted for Part D under Decision 1. TestNG or IntelliJ Coverage migrations are not needed.

## Consequences

- IOT-WO-02 Part A can register JUnit, JaCoCo, Surefire, Enforcer, the protobuf plugin and the other test or build components without a baseline exception.
- The gate becomes stricter for Maven than it would be without the ecosystem, because shipped-scope Maven dependencies are now evaluated as deployed components.
- This is an engineering position, not legal advice. As with ADR-0042, the owner's legal reviewer confirms it before commercial release (ADR-0030).

## Alternatives considered

- **Migrate the tests to TestNG and coverage to IntelliJ Coverage.** Rejected: a large, risky change that removes no legal exposure, because test tools aren't distributed.
- **Record JUnit and JaCoCo as 90-day baseline exceptions.** Rejected: the exception would recur every 90 days for something that is permanently fine, which weakens the meaning of an exception.
- **Wait for a Twinfra ADR change.** Rejected for now: Twinfra `main` freezes for v0.1.0, and MS1 would stall.
