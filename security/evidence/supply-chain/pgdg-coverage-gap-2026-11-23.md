# PGDG PostgreSQL coverage gap in the supply-chain gate

Evidence for the proposed
[IOT-WO-02 Amendment 7](../../../docs/work-orders/IOT-WO-02-gates-and-runtime-baseline.md#amendment-7-proposed-2026-11-23-pgdg-postgresql-coverage).
Recorded **2026-11-23**. This is a static reading of an existing CI artifact
and public pages. No image was pulled, run or deployed. No gate rule,
exception, pin or scanner is changed here. The
[machine record](pgdg-coverage-gap-2026-11-23.json) has the hashes, the
package records and the 52 CVEs.

## Finding

The gate never reports PostgreSQL server or libpq CVEs for the CNPG image
`ghcr.io/cloudnative-pg/postgresql@sha256:37ade18d…`
(`18.6-202610050823-minimal-trixie`). PostgreSQL 18.7 (2026-11-12) fixes 52
CVEs that affect 18.6. By the CNA's CVSS v3 scores, 38 are High, 12 Medium,
2 Low and none Critical. 43 are in the core server, 6 in the client and 3 in
contrib modules. None is in CISA KEV catalog 2026.11.20. The gate shows none
of them. A passing PostgreSQL row therefore does not show that the server has
no known CVEs.

## Source

Supply-chain gate run
[45132416685](https://github.com/amazen33/EdgePulse/actions/runs/45132416685)
(PR #70 head `ae3fa423`), artifact `edgepulse-supply-chain-45132416685`.
Syft 1.52.0 and Grype 0.119.0 were used with DB schema v6.1.10, built
2026-11-23T06:28:32Z.

- The Syft SBOM has 140 artifacts, all `deb`. The distro is Debian 13.7
  (trixie).
- The PGDG packages are `postgresql-18`, `postgresql-client-18` and `libpq5`
  at **`18.6-1.pgdg13+2`**, plus `postgresql-common` and
  `postgresql-client-common` at `293.pgdg13+1`.
  - Syft writes them as `pkg:deb/debian/…?distro=debian-13.7`.
  - The only sign of PGDG origin is the `.pgdg13` version suffix. The
    maintainer field is the same as in Debian, and dpkg status records no
    repository origin.
- Grype found 479 matches, all from the `dpkg-matcher` in namespace
  `debian:distro:debian:13`. **None is for a PostgreSQL or libpq package.**
- No other image in the artifact has a third-party-repository OS package.

## Why matching fails

1. **Distro namespace: this is the cause.** Grype's dpkg matcher (v0.119.0,
   `grype/matcher/dpkg/matcher.go`) searches only the image's distro
   namespace. It looks up the exact package name and each source package
   name, so `postgresql-18` is searched for all three binary packages.
   Debian trixie ships PostgreSQL 17: the Debian security tracker lists
   `postgresql-17` 17.12-0+deb13u1 for trixie, and `postgresql-18` only for
   forky and sid (18.7-1). So `debian:13` has no `postgresql-18` records to
   match.
2. **No PGDG data source.** Grype's vulnerability DB has no apt.postgresql.org
   provider. The PostgreSQL security page links no machine-readable feed
   (CSAF, OSV or JSON).
3. **CPE fallback is off for dpkg, by design.** The dpkg matcher uses CPEs
   only for end-of-life distros (`use-cpes-for-eol`, false here). Even if it
   used them, Syft's generated CPEs would not match:
   - they use products such as `postgresql-18` and `libpq5`, but NVD uses
     `postgresql:postgresql`;
   - they carry the Debian version string, not the upstream version.
4. **Syft drops the binary classifier's result.** Syft ran its `postgresql`
   binary classifier with
   `exclude-binary-packages-with-file-ownership-overlap: true`, so binaries
   owned by a dpkg package are removed. Not verified: whether the classifier
   matched the server binary before it was removed.
5. **The version scheme is not the cause.** A port of dpkg's `verrevcmp`
   gives `18.6-1.pgdg13+2 < 18.7-1` and `18.7-1.pgdg13+1 > 18.7-1`. A Debian
   fix version would compare correctly if a record existed.

## Checks for the proposal

These were checked on 2026-11-23, from public pages:

- Grype 0.119.0 accepts a bare CPE input (`grype/pkg/cpe_provider.go`,
  prefix `cpe:`). The stock matcher matches by CPE when `stock.using-cpes` is
  true, which is the gate's effective setting.
- The sampled CVEs are CVE-2026-6460, -120151, -116330 and -14661.
  - NVD shows them as *Awaiting Analysis*, with no configurations.
  - Anchore's `nvd-data-overrides` already gives each one
    `cpe:2.3:a:postgresql:postgresql:*` with the bounds `>= 18, < 18.7`.
- Not verified:
  - the other 48 CVEs;
  - whether the 2026-11-23 DB snapshot contains these overrides;
  - whether Grype reports a fix version for CPE matches;
  - whether the DB holds `postgresql-18` under `debian:14` or
    `debian:unstable`. Vunnel's release map emits forky as `14` and sid as
    `unstable`.

  Amendment 7's probe must answer these questions before any finding counts
  toward the gate.
