# ADR numbering convention

ADR numbers are assigned when the ADR merges to `main`, not when a
branch is created. Drafts live at `docs/adr/XXXX-proposed-<slug>.md`
using a placeholder number; the final number is assigned and the file
renamed at merge time. If two in-flight branches both draft an ADR, the
one that merges first takes the next free number; the other renumbers
at its own merge. This avoids the parallel-branch collision that
produced ADR 0011 (renumbered from a requested 0009, because 0009 and
0010 were already taken by an already-merged ADR and a still-unmerged
sibling branch respectively).

## Current numbers

- Highest merged: 0019. **Next free number: 0020.**
- 0014 is reserved for supply-chain security scanning (planned, not
  drafted); do not reuse it.
- Open drafts (numbered in merge order):
  `XXXX-proposed-private-cloud-infrastructure.md`,
  `XXXX-proposed-milestone-naming-and-roadmap.md`,
  `XXXX-proposed-platform-communication-direction.md`,
  `XXXX-proposed-roles-and-privileged-environment-access.md`,
  `XXXX-proposed-deployment-layers-tool-catalog-and-profiles.md`,
  `XXXX-proposed-service-api-and-payment-provider-boundaries.md`,
  `XXXX-proposed-config-studio.md`,
  `XXXX-proposed-ai-and-device-adapter-boundaries.md`.

Accepted ADRs are never rewritten in place. A change to an accepted
decision is a new ADR that names what it supersedes; summary documents
(`CLAUDE.md`, `README.md`, plans) are updated to point at it.
