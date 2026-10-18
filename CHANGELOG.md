# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
See [RELEASING.md](RELEASING.md) for the release streams.

Sections `0.3.0` to `1.0.0` are back-filled from the IOT-EE milestone tags (tag messages only).

## [Unreleased]

## [2.0.0-alpha.2] - 2026-10-18

- MS0 Reset was accepted ([acceptance receipt](docs/acceptance/ms0-reset-2026-10-18.md)). This release has the same content as 2.0.0-alpha.1, which was never released; see below.

## [2.0.0-alpha.1] - 2026-10-18

> Not released. Tag v2.0.0-alpha.1 points at a80e73e, the PR #40 head before the squash merge, which is not on main; its release run failed. Superseded by 2.0.0-alpha.2.

- MS0 Reset was accepted ([acceptance receipt](docs/acceptance/ms0-reset-2026-10-18.md)).

### Added

- IOT-WO-01 Part B decision records: ADRs 0014 and 0020–0023, the approved
  milestone plan, snapshot draft dispositions and aligned architecture pointers.
  Runtime integration, infrastructure freeze, Python archival and renaming remain
  separate work orders.
- Release streams (Dev, Candidate, Stable): `RELEASING.md`, this changelog,
  `compatibility.yaml`, the `release-checks` and `release` workflows, and the rulesets in
  `.github/rulesets/`.

### Changed

- IOT-WO-05: rename active Maven, Java/proto, Spring configuration and
  contract identifiers to EdgePulse under ADR 0023; align standing documents
  and add the blocking naming gate with exact historical-reference exemptions.
  MS0 remains open until the owner signs its receipt and tags `v2.0.0-alpha.1`.

- IOT-WO-01 Part C: mark retained infrastructure frozen under ADR 0021;
  archive the Python M0-M8 specification in tag `archive/python-spec-final`,
  remove it from the active checkout and CI, and retain the required Java gate.
  Active reference documentation points to the archive; MS0 still requires
  IOT-WO-05 and its receipt. No deployment or identifier rename is included.

- The version is now `2.0.0`, the next base version: EdgePulse continues after the IOT-EE
  tags (`v0.3.0`–`v1.0.0`). It was `0.1.0-SNAPSHOT` in the root and module poms.

## [1.0.0] - 2026-09-23

- M9 Track B: Java platform bootstrap: contracts/, architecture/, services/identity walking
  skeleton. First green Java platform gate; every ADR 0013 mechanism mechanically enforced.

## [0.10.0] - 2026-09-23

- Python reference implementation frozen and relocated to spec/ (ADR 0012 Decision 7). Last
  Python-only state before Java work.

## [0.9.0] - 2026-09-23

- Post-M8: WORM S3 adapter graduation + ADR 0011 (Java platform pivot) + ADR 0012 (M9 scope).
  Last Python-feature state.

## [0.8.0] - 2026-09-22

- M8: inert Deployment Studio: plan/validate-only, immutable profile registry, mechanical
  isolation.

## [0.7.0] - 2026-09-22

- M7: optional monetization behind a default-off runtime flag + mechanical billing isolation.

## [0.6.0] - 2026-09-22

- M6: immutable evidence, legal hold, replay/reconciliation for DR.

## [0.5.0] - 2026-09-22

- M5: firmware signing, provenance, staged canary/broad rollout + rollback.

## [0.4.0] - 2026-09-22

- M4: reporting read-model + APISIX/auth gateway contract, 200/200.

## [0.3.0] - 2026-09-22

- M3: ingestion + outbox + Kafka relay + shadow-parity, 150/150.
