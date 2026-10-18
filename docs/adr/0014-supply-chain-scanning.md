# ADR 0014: Supply-chain scanning (adopts Twinfra ADR-0049)

**Status:** Accepted, as a consequence of ADR 0021 (owner D-2, 2026-10-14: Twinfra's gates apply to IOT-EE). This fills the number reserved in `docs/adr/README.md`.
**Author:** Claude (architecture). **Implementer:** Codex (IOT-WO-02).

## Decision

IOT-EE adopts Twinfra ADR-0049 unchanged, applied to IOT-EE's own artifacts:

1. **Scanners.**
   - Syft generates SBOMs for each image.
   - Grype scans images and SBOMs.
   - OSV-Scanner scans lockfiles and the Maven dependency graph, read from a CycloneDX SBOM produced by the build.
   - All three are pinned.
   - Trivy is not used (CVE-2026-33634).
2. **Scope.** The scans cover every image IOT-EE builds or deploys, including the pinned TB CE image and the dependencies it bundles. They also cover the Maven reactor and CI-only tool lockfiles.
3. **Gate rules**, the same as Twinfra:
   - a KEV match blocks the change;
   - releases have a 14-day cool-off, with an expedite rule for KEV or actively exploited issues;
   - exceptions are capped by severity at 30, 60 or 90 days, and each one needs evidence;
   - a nightly scan opens or updates one issue in place;
   - `govulncheck`-style reachability evidence is required before excepting a JVM finding. For Java this means a recorded call-path or "not on the classpath" argument; there is no automated equivalent.
4. **Signing and provenance** (cosign or Sigstore) follow Twinfra when Twinfra adopts them. They are not part of this ADR.

## Consequences

- `CLAUDE.md`'s "Supply-chain security scanning (planned — ADR 0014 …) Trivy …" paragraph is replaced by a pointer to this ADR.
- The first scan of the TB CE image will probably raise findings that CE's own upstream must fix. These are tracked as exceptions with upstream evidence, and every TB CE patch bump is re-scanned.
