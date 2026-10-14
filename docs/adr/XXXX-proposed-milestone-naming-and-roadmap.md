# ADR XXXX (proposed) -- Milestone naming and roadmap: M9 stays final legacy migration/cutover; the Java foundation is "Platform Foundation" (PF)

Status: proposed. Unnumbered draft per `docs/adr/README.md`; the number
is assigned at merge. Encodes direction given by the repository owner on
2026-09-25 ("preserve final legacy import as the final migration stage;
give the Java foundation a separate name or stage"). The stage name
**Platform Foundation (PF)** is this draft's proposal and needs the
owner's confirmation at review.

Supersedes, for naming only: ADR 0012's use of the label "M9" (its title,
Context and Decision 1). Every technical decision in ADR 0012 (Maven,
Protobuf envelope, `X-Correlation-ID`, walking skeleton in
`services/identity`, `spec/` relocation, Java-only) stands unchanged.
ADR 0012 is not edited; read it through this ADR.

## Context

Two merged documents give "M9" two different meanings:

| Source | Meaning of M9 |
| --- | --- |
| `docs/requirements-addendum.md` ("Interfaces and migration sequence", "Delivery and acceptance") | Full production legacy import, reconciliation, approval and cutover -- the **final** stage, after M8 Deployment Studio |
| ADR 0002 (accepted, M1 Migration Studio foundation) | The same: "full production legacy import/reconciliation/cutover only at M9, after Deployment Studio (M8)" |
| ADR 0012 (merged; its own H1 and Status line still read "XXXX (proposed)") | Java foundation: Track A (TB CE investigation) and Track B (Java bootstrap) |
| `CLAUDE.md` before this change | Follows ADR 0012 ("M9 is in progress") |
| `docs/track-c-execution-plan.md` | "M9 -> Track C" |

The requirement came first (addendum, ADR 0002) and is a product
commitment: final migration happens last, only after Deployment Studio
can produce the target environments. ADR 0012 reused the next free
number for foundation work without addressing that commitment.
ADR 0012 and ADR 0013 also use "M10+" to mean "business-logic Java
services after the foundation", which only makes sense under ADR 0012's
numbering.

## Decision

1. **M0-M9 are product capability milestones**, as defined by
   `docs/requirements-addendum.md`:

   | Milestone | Capability |
   | --- | --- |
   | M0 | Foundation |
   | M1 | Migration Studio foundation (vault abstraction, configuration lifecycle) |
   | M2 | Domain core (tenant identities, permissions, entitlements, operator/device command domain) |
   | M3 | MQTT/PostgreSQL ingestion, Kafka, TB shadow parity, authenticated device delivery |
   | M4 | APISIX/BFF, separated console logins, Operators page, REST/gRPC/WebSocket integration, reports |
   | M5 | Entitled firmware management |
   | M6 | Immutable evidence, secret rotation/revocation, resilience/DR |
   | M7 | Optional monetization |
   | M8 | Deployment Studio / multi-environment, identity and vault configuration in deployment plans |
   | **M9** | **Final full legacy import, reconciliation, approval and cutover** -- last, after M8 |

2. **M9 keeps exactly the addendum's meaning.** Its entry and exit
   requirements are unchanged: scoped inventory coverage, counts/hashes
   and semantic reconciliation, delta catch-up, preserved rule/report
   parity, rollback rehearsal, acceptance, authorized cutover, and no
   automatic secret import. Nothing earlier than M9 imports production
   legacy data; earlier stages use synthetic inputs or explicitly
   approved limited samples/shadow reads only.

3. **The Java foundation is a separate stage, "Platform Foundation"
   (PF)**, not a numbered milestone. It builds the platform the M1-M9
   capabilities are implemented on and delivers no business capability
   of its own:

   | PF track | Former label | Scope | Governing ADRs |
   | --- | --- | --- | --- |
   | PF-A | M9 Track A | TB CE investigation (version pin, extension surface, `tb-extensions/manifest.yaml`) | 0011, 0012 |
   | PF-B | M9 Track B | Java bootstrap (Maven parent, contracts, ArchUnit gates, `services/identity` walking skeleton), then the ADR 0013 autonomy refactor | 0012, 0013 |
   | PF-C | "M9 -> Track C" | Steps C0-C7: hexagonal skeleton, observability, IAM-agnostic identity, persistence and tenancy, event backbone, transport-swap proof, deploy foundation | 0015-0019 |

   The C0-C7 step labels are unchanged; ADRs 0016-0018 refer to them.

4. **Two tracks of delivery for M1-M8.** The Python M0-M8 slices in
   `spec/` are the frozen specification/reference implementation (ADR
   0011 Decision 9). Each M1-M8 capability is still to be implemented on
   the Java platform after (and partly alongside) PF. A milestone is
   "complete on the platform" only when its Java implementation meets
   the stage-completion checklist in `CLAUDE.md`; a spec slice being
   complete does not make the platform milestone complete.

5. **Reading the older labels.** Where ADRs 0011-0013, code comments or
   other documents say:
   - "M9" meaning Track A/B or Track C -> read **PF** (PF-A, PF-B, PF-C);
   - "M10+" meaning post-foundation Java services -> read **the Java
     implementation of M1-M8 capabilities, after PF**;
   - "M9" meaning final legacy import/cutover (ADR 0002, ADR 0003's
     "M3/M9", `docs/migration-studio.md`) -> unchanged.
   Accepted ADRs are not edited to apply this; summary documents
   (`CLAUDE.md`, `README.md`, `docs/track-c-execution-plan.md`,
   `docs/test-plan.md`) are.

## Consequences

- `CLAUDE.md`'s roadmap lists M0-M9 plus PF, and its reading order
  points at this ADR before ADR 0012.
- The current stage is PF-C (C1 done, C2 next), not "M9 in progress".
- Code comments and one ArchUnit failure message in `services/identity`
  still say "M9" / "M10+". They are harmless under Decision 5 and are
  left for a separate code-only change so this change stays docs-only
  apart from the tenancy contract fix.
- ADR 0012 keeps its file name (`0012-m9-foundation-scope.md`); renaming
  a merged ADR file would break existing references.

## Alternatives rejected

- **Renumber final migration to M10.** Rejected by the owner's direction:
  M9 is a published, accepted commitment (addendum, ADR 0002).
- **Call the foundation "M8.5" or "M0b".** Implies it sits inside the
  capability sequence; it does not -- it is the platform under M1-M9.

## Open questions for review

- Confirm the name "Platform Foundation (PF)".
- Whether M1-M8 Java implementation proceeds in milestone order or by
  dependency (for example identity and tenancy for M2 before M1's vault
  work). Not decided here.
