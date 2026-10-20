# IOT-WO-08: Image and dependency refresh (clears the Part B exceptions)

**Status:** Approved for implementation when the owner approves PR #48's exception list, which references this work order. **Due: 2026-11-19**: every exception that names it expires then (ADR-0049's 30-day Critical limit).
**Author:** Claude · **Implementer:** Codex, as the Enterprise Senior cloud engineer · **Branch:** `codex/iot-wo-08-refresh`
**Decision:** ADR 0014 / Twinfra ADR-0049, and IOT-WO-02 Amendment 5.

## Scope

Clear every exception in `security/vulnerability-exceptions.json` whose `workOrder` is `IOT-WO-08`: 287 entries at PR #48, mostly in the kind node, the three Cilium images, the CNPG operator, the TB image, and one executed Maven plugin.

1. **Weekly refresh check, each Monday until done.** For every affected image and package, check for a newer release at least 14 days old: kind, and its node image matching Kubernetes 1.36; Cilium at Twinfra's locked line; CNPG; TB 4.3.1.x; the Maven plugin.
   - Adopt each one as soon as it qualifies, in a small PR that rescans, removes the exceptions it clears, and updates the pins, the register (with the re-fingerprint rule, or full records where a component changes) and the evidence.
2. **The TB image:** EdgePulse never forks or rebuilds TB (ADR 0020). If no 4.3.1.x patch clears its entries by **2026-11-12**, report the remaining TB findings with reachability notes. The owner then decides: a newer TB line, or new evidenced exceptions (each Critical needs its own entry and fresh approval).
3. **The kind node and Cilium (local and CI test harness only, never deployed by EdgePulse):** if upstream hasn't published fixed releases by **2026-11-12**, report it. The owner decides between new evidenced exceptions and an ADR on how ADR-0049 applies to test-harness-only images. Don't build custom node images without a decision.
4. Exceptions are never extended in place. A renewal is a new, owner-approved entry with fresh evidence.

## Acceptance

- No `IOT-WO-08` exception remains, or each remaining one is replaced by an owner-approved entry under item 2 or 3, before 2026-11-19.
- CI is green: `java-platform-bootstrap`, `naming-gate`, `release-checks`, `licence-gate` and `supply-chain-gate`.
- Each PR lists the exceptions it removed, and the before and after counts.

## Owner checkpoints

- **2026-11-12:** a status report on what remains, with the decisions under items 2 and 3.
- **Before 2026-11-19:** approve any renewal entries.
