# ADR 0026 (proposed): Build-tool licence families

**Status:** Accepted (owner, 2026-10-20). It lands as 0026, after ADRs 0024 and 0025.
**Supersedes:** ADR 0024 Decision 1 (EPL-2.0 alone). ADR 0024 is not edited.
**Applies:** Twinfra ADR-0042's build-tool rule, in EdgePulse's port only. Twinfra is not changed. Shipped components are unaffected.

## Context

ADR 0024 added **EPL-2.0** by name to the `build-tool` class. IOT-WO-02 Part A then stopped a third time, on 2026-10-20, on eight **Maven plugin dependencies**. They run only during the build and are never shipped:

| Components | Licence |
| --- | --- |
| Eclipse Aether API, implementation, SPI and utilities `1.0.0.v20140518`, used by Spring Boot's Maven plugin and others | EPL-1.0 |
| Eclipse Sisu Inject and Plexus `0.3.5` | EPL-1.0 |
| `javax.annotation:javax.annotation-api:1.2` | CDDL-1.0/1.1 OR GPL-2.0 WITH Classpath-exception-2.0 |
| `javax.servlet:javax.servlet-api:3.1.0` | CDDL-1.0/1.1 OR GPL-2.0 WITH Classpath-exception-2.0 |

Twinfra ADR-0042 allows build tools the permitted list plus MPL-2.0, LGPL and GPL. Its reason is that copyleft obligations attach to distributing or linking, and build-tool output isn't distributed. EPL-1.0 and CDDL are weak, file-level copyleft licences in the same family as MPL. The GPL option carries the Classpath exception, which only weakens GPL further. Listing licences one by one makes the gate stop on every new member of an already-permitted family.

## Decision

1. **The build-tool licence families.** In EdgePulse's port, a component that qualifies as `build-tool` (ADR-0042's three conditions, ADR 0024 Decision 2, ADR 0025 Decision 1) may carry any of these:
   - the permitted list;
   - **weak copyleft:** MPL-1.1, MPL-2.0, EPL-1.0, EPL-2.0, CDDL-1.0, CDDL-1.1, LGPL-2.1, LGPL-3.0;
   - **GPL:** GPL-2.0 and GPL-3.0, with or without the exceptions `Classpath-exception-2.0`, `GCC-exception-3.1` or `LLVM-exception`.

   For an `OR` expression, the gate passes if any one option is in the families above, and records the elected option.
2. **Still blocked in every class:** AGPL, SSPL, BUSL, Elastic-2.0, account-gated or proprietary licences, and any component with **no** or an **unknown** licence. Those still stop the work.
3. **Shipped components are unchanged:** the permitted list only. The named exceptions are OpenBao (Twinfra) and `jakarta.annotation-api` (ADR 0025).
4. **Upstream later**, with ADR 0024 Decision 4 and ADR 0025 Decision 4, as one Twinfra ADR-0042 clarification after v0.1.0.

## Consequences

- Part A can register the whole Maven plugin graph. The gate still fails, with a planted test, on a blocked licence, an unknown licence, or a build-tool component that becomes reachable from a shipped classpath.
- New build plugins in the families above need no new ADR. Shipped dependencies still do.
- This is an engineering position, not legal advice. It is confirmed by the owner's legal reviewer before commercial release (ADR-0030).

## Alternatives considered

- **Add EPL-1.0 and CDDL by name.** Rejected: the same stop would recur for the next family member.
- **Replace the plugins or pin newer versions.** Rejected: Aether and Sisu sit under Spring Boot's and Maven's own plugins, so replacing them would mean replacing the build tool.
