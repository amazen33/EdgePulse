# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
See [RELEASING.md](RELEASING.md) for the release streams.

Sections `0.3.0` to `1.0.0` are back-filled from the IOT-EE milestone tags (tag messages only).

## [Unreleased]

### Security

- IOT-WO-02 Part C, Java-only step: target Java 21 and pin CI Temurin
  21.0.12.1+1 (setup-java SemVer 21.0.12+101.0.LTS), with verified official
  archive hashes and a build-tool register entry. Spring and all application
  dependency versions remain unchanged; the supported Spring trial is separate.

- IOT-WO-08: refresh identity's gRPC to 1.84.0 with Protobuf 3.25.9;
  prove and exclude annotation-only JSpecify and Animal Sniffer artifacts,
  and preserve the exact legacy Error Prone annotations 2.28.0 admission.
  Remove CVE-2025-55163's cleared exception after the pinned scan.
- IOT-WO-06 / ADR 0027: use BOM-managed Log4j 2.26.1 for identity runtime
  logging, with a console-only correlation-ID pattern and runtime-classpath
  provider/context/request-log tests; remove Logback and reverse bridges.
  The 2026-10-21 ruling adds POM-only BOM inventory and removal-only legacy
  retirement guards in EdgePulse wiring, with planted-violation tests.
- IOT-WO-02 Part B: wire checksum-pinned Syft, Grype and OSV-Scanner over
  digest-pinned image inputs, Maven reactor BOMs/resolved trees and lockfiles.
  Preserve the ADR 0014 policy and an evidence-only legacy SBOM backfill guard;
  scan results and any remaining acceptance blockers accompany the PR.
- IOT-WO-02 Amendment 5: patch supported Tomcat 10.1 and gated build/test
  dependencies, evaluate a dated minimal PostgreSQL image, and retain
  out-of-support runtime lines for Part C with explicit dated findings.

### Added

- IOT-WO-02 Part A: a separate licence gate, the Maven/component register and
  planted-violation checks under ADRs 0024ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“0026, ported from Twinfra `0d95007`.
  Supply-chain, quality and runtime-baseline work remain in later parts.

### Removed

- IOT-WO-07: retire the 61 frozen own-infrastructure files and their non-required
  infrastructure workflow under ADR 0021; history remains in `archive/iot-ee-own-infra`.
  Remove their exclusively used tools, licence records and six obsolete evidence gaps.
  Application code, archive tags and environment state are unchanged.

## [2.0.0-alpha.4] - 2026-10-19

- MS2 migration contract v1 was accepted ([acceptance receipt](docs/acceptance/ms2-migration-contract-v1-2026-10-19.md)).

### Added

- IOT-WO-03: migration contract `v1.0.0-draft` (MR-1 to MR-14), test-only
  contract kit, provenance-compatible envelope fields and synthetic reference
  fixtures. Additive changes only within v1; licence and supply-chain gates
  remain pending IOT-WO-02. No service or live integration is implemented.

- Prepare IOT-WO-04 Amendment 3's namespaced TB CE chart, pinned isolated kind
  harness, restricted-v2 render and context-guard checks, and local rehearsal
  record. Live steps require separate owner approval; no milestone receipt.

## [2.0.0-alpha.3] - 2026-10-18

- MS0 Reset was accepted ([acceptance receipt](docs/acceptance/ms0-reset-2026-10-18.md)). Same content as 2.0.0-alpha.1; tags v2.0.0-alpha.1 and v2.0.0-alpha.2 were never released (see below).

## [2.0.0-alpha.2] - 2026-10-18

> Not released. Tag v2.0.0-alpha.2 was pushed on 48a314a before this section existed; its release run failed. Superseded by 2.0.0-alpha.3.

## [2.0.0-alpha.1] - 2026-10-18

> Not released. Tag v2.0.0-alpha.1 points at a80e73e, the PR #40 head before the squash merge, which is not on main; its release run failed. Superseded by 2.0.0-alpha.3.

- MS0 Reset was accepted ([acceptance receipt](docs/acceptance/ms0-reset-2026-10-18.md)).

### Added

- IOT-WO-01 Part B decision records: ADRs 0014 and 0020ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“0023, the approved
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
  tags (`v0.3.0`ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“`v1.0.0`). It was `0.1.0-SNAPSHOT` in the root and module poms.

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
