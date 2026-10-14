# Releasing

EdgePulse (formerly IOT-EE) is a **product** repository with three release streams: **Dev → Candidate → Stable**.

## Streams

| Stream | Where it comes from | Version |
| --- | --- | --- |
| **Dev** | Every merge to `main` | No tag |
| **Candidate** | Before the first stable `v2.0.0`: alphas and betas are tagged on `main`. From the first `-rc.1`: the branch `release/X.Y` | `v2.0.0-alpha.N`, `-beta.N`, `-rc.N`, published as GitHub **pre-releases** |
| **Stable** | The same commit as the accepted candidate. The release workflow creates a **draft**, and the owner publishes it | `vX.Y.Z` |

## Milestones and versions

| Milestones | Tags |
| --- | --- |
| MS0–MS6 | `v2.0.0-alpha.N`, one when each milestone completes |
| MS7 (production readiness) | `v2.0.0-beta.N` |
| MS8 (pilot migration) | `v2.0.0-rc.N`, on `release/2.0` |
| Pilot accepted | **`v2.0.0`** |
| MS9 waves | `v2.x` minors |

The tags `v0.3.0` to `v1.0.0` are **historical IOT-EE milestone tags**: the M3–M8 Python reference, then the Java bootstrap. They are never moved or reused. EdgePulse continues at 2.0.0 because ADR 0020 changes the architecture and ADR 0023 renames the product.

## Version source

The project `<version>` in the root `pom.xml` holds the **next release's base version** (`2.0.0`). The module poms reference it as their parent version. `compatibility.yaml` states what a release requires (Twinfra, ThingsBoard CE) and provides (the migration contract).

## Cutting a release

1. **Prepare.** Open a PR titled `release: X.Y.Z-alpha.N` (or similar). In `CHANGELOG.md`, move `## [Unreleased]` into `## [X.Y.Z-alpha.N]`. For an rc or a stable release, the section is `## [X.Y.Z]`. Merge it.
2. **Branch.** For the first rc, create `release/X.Y` from that commit.
3. **Candidate.** Tag and push. The `release` workflow:
   - checks the tag against `pom.xml` and the changelog;
   - checks the branch: alphas and betas on `main` or `release/X.Y`; rcs only on `release/X.Y`;
   - creates a pre-release.
4. **Stable.** Tag the **same commit** as the accepted rc `vX.Y.Z`. The owner publishes the draft.
5. **Fixes.** Fix on `main` first, then `git cherry-pick -x` onto `release/X.Y`, then cut a new rc.
6. **Next.** After a stable release, open a PR that bumps the version to the next base.

## Rules

- **Tags are immutable.** That includes the historical ones.
- **Every change goes through a PR.** `main` and `release/*` require `release-checks` and `java-platform-bootstrap`.
- **Every PR updates `CHANGELOG.md` under `[Unreleased]`**, or carries the label `changelog:skip` with a reason.

The rulesets are in `.github/rulesets/`.
