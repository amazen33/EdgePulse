# EdgePulse development team

Owner direction: 2026-10-22. This is current EdgePulse workflow guidance;
it does not amend product architecture or historical authorship.

| Role | Assignment and authority |
| --- | --- |
| Owner, product lead and acceptance tester | Ahmed Mazen (@amazen33): accepts decisions and exceptions, authorizes live actions, reviews and merges PRs, and signs acceptance receipts. |
| Architecture proposals and implementation | Codex: reviews evidence, proposes decisions and work orders, implements authorized changes, runs gates and opens PRs. An owner decision is required where the work order says so. |
| Advisory assistance | GitHub Copilot: bounded housekeeping and explicitly assigned read-only reviews. It does not edit repository code, documentation or receipts under the current helper role. |

OpenCode is excluded from the EdgePulse team. Do not assign EdgePulse work or
reviews to it, or dispatch tasks through its imported configuration. No
OpenCode process, installation, global configuration or other repository is
changed by this policy.

Claude is not a required workflow participant. Existing ADRs, historical
reviews and author credits remain unchanged. Accepted ADRs remain binding
until superseded by another owner-accepted decision.

## Review and execution boundaries

- Every change requires a PR, passing relevant CI and human review. No agent
  approves its own work, merges a PR or signs an acceptance receipt.
- Developer self-review can find and fix defects; it is not independent
  approval. Advisory AI feedback does not satisfy the human review requirement.
- Use one implementer per checkout/branch. The separate Part C trial worktree
  belongs to its assigned task and must not be read or changed here.
- Keep AGENTS.md and CLAUDE.md aligned except for their titles. Copilot-specific
  instructions reference that contract rather than duplicating it.
- Choose AI models explicitly when model/provider restrictions are part of a
  task. The main session's model does not establish a review agent's backend.
- Current owner instructions and this repository's contract govern EdgePulse;
  generic handoff helper prompts do not grant broader repository access,
  deployment permission, merge authority or a role for OpenCode.
- Product and security choices remain governed by accepted ADRs, including
  0014, 0020 and 0021. Changing an assistant does not authorize a new stack.

## Current delivery order

IOT-WO-02 Parts A and B provide code/CI foundations in merged
[PR #46](https://github.com/amazen33/EdgePulse/pull/46) and
[PR #48](https://github.com/amazen33/EdgePulse/pull/48). Amendment 5 moves
Part C before Part D: Java 21 first with no Spring change, then a separately
bounded Spring trial and owner decision, then quality gates. MS1 remains
incomplete until its required gates, runtime baseline and acceptance receipt.
This policy does not accept a milestone or authorize a live environment run.
