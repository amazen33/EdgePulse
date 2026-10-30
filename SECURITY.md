# Security policy

## Report a vulnerability

Please **do not open a public issue** for a security problem.

Email **security@amazen33.dev** with:
- the affected product, version or commit, and component;
- steps to reproduce, or a proof of concept;
- the impact you expect, for example whose data or which system is affected;
- whether you want to be credited, and how.

## What to expect

| Step | Target |
| --- | --- |
| Acknowledgement | Within 5 business days |
| First assessment (triage) | Within 10 business days |
| Updates | At least every 14 days until resolved |
| Fix and advisory | Coordinated with you. The default disclosure window is 90 days, or earlier once a fix is released |

Advisories are published through GitHub Security Advisories for this repository. We credit reporters who want it.

## Supported versions

EdgePulse is an IoT platform in foundation development. Release streams follow
[RELEASING.md](RELEASING.md):

| Stream | Versions and status |
| --- | --- |
| Dev | Current `main` commits; unreleased development snapshots. |
| Candidate | Published pre-releases `v2.0.0-alpha.3` and `v2.0.0-alpha.4`; the latest is `v2.0.0-alpha.4`. |
| Stable | No stable EdgePulse `v2.x` release has been published. |

Historical milestone releases and tags are archival and do not constitute a
supported stable EdgePulse release.

## Scope

This policy covers this repository's source, contracts, configuration,
documentation and automation, including:

- The Java identity foundation (`services/identity/`), including REST and gRPC,
  token verification, tenant-scoped authorization and correlation/logging.
- Configuration, event, identity and migration-readiness contracts (`contracts/`).
- Test-only architecture rules and contract verification (`architecture/`,
  `contract-tests/`).
- ThingsBoard CE Helm packaging (`charts/edgepulse-thingsboard/`) and customization
  manifest (`tb-extensions/`); the manifest records plans, not implemented
  customizations.
- Local kind development scripts and pinned configuration (`dev/kind/`); the
  rehearsal is paused.
- Build, release, licence and supply-chain automation (`pom.xml`, `.github/`,
  `security/`, `tools/ci/`).

This scope covers repository artifacts. Runtime integrations and real-environment
acceptance remain pending.

**Out of scope:**
- denial-of-service testing;
- social engineering;
- physical attacks;
- spam;
- automated scanner output without a demonstrated impact;
- findings in third-party services we don't operate.

## Safe harbour

If you act in good faith and follow this policy, we will not pursue legal action against you for your research, as far as that is within our control. Good faith means you:
- do not access, change or keep other people's data beyond the minimum needed to show the problem;
- do not degrade any service;
- stop and report as soon as you reach data that isn't yours;
- give us reasonable time to fix the problem before you disclose it.

This policy follows the product security standard SEC-01 of the EdgePulse project.
