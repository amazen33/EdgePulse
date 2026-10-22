# PR #51 developer review — 2026-10-22

Scope: ADR 0028 Decisions 1–4, the EdgePulse wrapper and class guard,
exception removal, planted tests, and unchanged upstream tooling. Reviewed
base c126d1e00b345d0721ed08fbcc4e92a87384055d against head
a59e6b7cf407c2d103221a1542cbe6c34e875824 before the review fix.

This is a developer self-review and remediation record. It is not an
independent approval, milestone receipt or environment acceptance. Human
review and merge remain required.

## Finding R1 — inherited image reference bypassed job permissions (P1)

The guard selected jobs using only the job body. A workflow-level environment
variable could contain a harness image and be used by another job, while that
job's contents-write permission or repository-secret reference escaped the
ADR 0028 check. The existing workflows did not use this pattern.

Reproduction: three synthetic tests added before the fix failed: write access
was not rejected, secret access was not rejected, and the read-only job was
missing from the coverage list. No real secret or container was used.

Resolution: select jobs using workflow-level environment plus job contents,
then apply the existing exact permissions and secret/environment checks to
that inherited input. The three regressions now pass, including the permitted
read-only case. The full supply-chain suite passes 88 tests.

## Preservation checks

The five class entries and image digests, all licence records and legacy
deadlines, the 266-entry removal, all 36 retained exception entry bytes, the
ported tools/tests, checker, ladder, schemas and workflow names are unchanged.
The existing tests retain KEV and staleness blocking and strict shipped-image
handling. No local cluster, deployment, tag or merge action was performed.

CI evidence and full scan artifacts are linked from
[PR #51](https://github.com/amazen33/EdgePulse/pull/51). Only green checks on
the latest head count for readiness; this record does not approve the PR.
