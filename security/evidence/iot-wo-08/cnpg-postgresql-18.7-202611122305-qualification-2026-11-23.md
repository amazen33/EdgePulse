# CNPG PostgreSQL 18.7-202611122305 qualification

IOT-WO-08 item 1. On 2026-11-23 the owner chose a partial refresh to this
build. It replaces the earlier `18.6-202611090812` target, because no eligible
build carries the glibc and krb5 fixes. Reviewed **2026-11-23**. The 14-day
cool-off ends **2026-11-26T23:16:17Z**, so the PR stays a draft until
2026-11-27. This record qualifies one image digest. It is not a deployment,
runtime or milestone receipt, and the image runs nowhere.
The [machine record](cnpg-postgresql-18.7-202611122305-qualification-2026-11-23.json)
holds the hashes and dates.

## Candidate

| | Current pin (replaced) | Candidate |
| --- | --- | --- |
| Tag | `18.6-202610050823-minimal-trixie` | `18.7-202611122305-minimal-trixie` |
| Index digest | `sha256:37ade18dbdddba430858c72725aceeec66f33fa5333e82ea1df4942f6c1c83a3` | `sha256:b98ae0b74a12f20ccff32219be0e33fdd35c7e2e8e73c8bff9173f1128e167d1` |
| Source revision | `ff34de135f29e04a841247ea9686d7a80b663005` | `e1279c43bd11570edc864d220468c28e611df5dd` |
| PostgreSQL | 18.6 | 18.7 |

The supplier, flavour and Debian release are unchanged. The
[licence at the candidate revision](https://github.com/cloudnative-pg/postgres-containers/blob/e1279c43bd11570edc864d220468c28e611df5dd/LICENSE)
is byte-identical to the one at the replaced revision (SHA-256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`).
The register keeps `Apache-2.0 AND PostgreSQL`, tier 2.

## Eligibility: 14-day cool-off

The OCI index annotation dates the build to 2026-11-12T23:05:08Z. That is a
lower bound only, so two transparency-log entries bound publication from
above:

- **Image signature:** the GHCR referrer for the exact index digest is a
  keyless cosign bundle from the postgres-containers `bake_targets.yml`
  workflow at the source revision. Its Rekor entry
  ([logIndex 3841077455](https://rekor.sigstore.dev/api/v1/log/entries?logIndex=3841077455))
  was integrated at 2026-11-12T23:16:14Z. The referrer's created annotation is
  23:16:17Z, and the payload hash matches the in-toto statement whose subject
  is the candidate digest.
- **Image catalog:** commit
  [`72fb864`](https://github.com/cloudnative-pg/artifacts/commit/72fb8647dd498f5c50a79057d20292c2cb82f553)
  in `cloudnative-pg/artifacts` lists this tag and digest in
  `catalog-minimal-trixie.yaml`. The file's signature
  ([logIndex 3841178854](https://rekor.sigstore.dev/api/v1/log/entries?logIndex=3841178854))
  was integrated at 2026-11-12T23:21:48Z.

The later of the two signature times is used, so the cool-off ends
**2026-11-26T23:16:17Z**. No KEV expedite is used. The GitHub API returned
HTTP 404 for the upstream workflow run, so the Rekor entries are the retained
build records. Certificate chains were not cryptographically verified.

## Why a partial refresh

| Build (`minimal-trixie`) | Eligible from (UTC) | glibc | krb5 | `apt` | `zlib1g` | PostgreSQL |
| --- | --- | --- | --- | --- | --- | --- |
| 18.6-202611090812 | 2026-11-23 08:24 | deb13u4 | deb13u1 | 3.0.4 | deb13u1 | 18.6 |
| **18.7-202611122305** | **2026-11-26 23:16** | deb13u4 | deb13u1 | 3.0.4 | deb13u1 | 18.7 |
| 18.7-202611160820 | 2026-11-30 08:35 | deb13u4 | deb13u1 | 3.0.4 | deb13u1 | 18.7 |
| 18.7-202611201711 | 2026-12-04 17:26 | deb13u4 | deb13u1 | 3.0.4 | deb13u1 | 18.7 |

These are pre-check values, read from each build's `linux/amd64` layers
(verified against their digests); the images were not run.
No build has the glibc fix (`2.41-12+deb13u5`) or the krb5 fix
(`1.21.3-5+deb13u2`, DSA-6650-1). This build clears the apt and zlib1g
findings and moves the server to PostgreSQL 18.7. Its glibc and krb5 findings
sit on a digest that no A-6 row matches, so they need fresh approval: the
A-7 proposal.

## PostgreSQL server-CVE coverage gap

[PostgreSQL 18.7](https://www.postgresql.org/docs/release/18.7/) (2026-11-12)
fixes 52 PostgreSQL CVEs that every 18.6 build carries. None is in the CISA
KEV catalogue 2026.11.20. The pinned scanners report no match for the PGDG
`postgresql-18` or `libpq5` packages, so server CVEs never reach the gate.
This refresh delivers the 52 fixes, but the gate cannot confirm them and
would not see future server CVEs either. A separate session is investigating
the coverage loss.

## Five supplier criteria

- **Maturity — pass:** [PostgreSQL 18.7](https://www.postgresql.org/docs/release/18.7/)
  is a stable release (2026-11-12), in CNPG's official minimal operand image.
- **Governance — pass:** the [CNCF project page](https://www.cncf.io/projects/cloudnativepg/)
  records CloudNativePG joining CNCF on 2025-01-21 and becoming Incubating on
  2026-11-02. The cloudnative-pg organisation owns postgres-containers. Its
  `GOVERNANCE.md` at the revision defers to the CloudNativePG policies.
- **Activity/support — pass:** the
  [PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/)
  supports major 18 until 2030-11-14 and lists 18.7 as the current minor. CNPG
  rebuilds weekly, and this build is within six months.
- **Security process — pass:** the
  [CloudNativePG security policy](https://github.com/cloudnative-pg/cloudnative-pg/security/policy)
  provides private reporting, a 10-business-day acknowledgement target and
  coordinated advisories. The exact digest is cosign-signed and carries SBOM
  and provenance attestations. The operator's
  [OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/cloudnative-pg/cloudnative-pg)
  is 9.3 (2026-11-20; Security-Policy 10, Signed-Releases 10). The
  postgres-containers endpoint returned HTTP 404, so no score is claimed for
  that repository.
- **Adoption — pass:** [ADOPTERS.md](https://github.com/cloudnative-pg/cloudnative-pg/blob/e9eec0d3b49adb088f6fbcfa024d4ea288105c6e/ADOPTERS.md)
  names 56 organisations, including EDB, IBM, Google Cloud and Clustermarket.
  The GitHub API reported 9,647 stars and 823 forks at
  2026-11-23T07:40:28Z. These signals are project-wide; they do not count this
  image or any EdgePulse use.

| Source (read 2026-11-23) | SHA-256 of response bytes |
| --- | --- |
| postgres-containers `LICENSE` at `e1279c4` | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| postgres-containers `GOVERNANCE.md` at `e1279c4` | `07006a15bbc1ecab17aff99f22ecbcc4251ea23bf8488b1da5be7e4b6d8c004d` |
| PostgreSQL 18.7 release notes | `36397579ea33b25e388364508454eb433972cc54664cf049907aed22d40d0d2f` |
| PostgreSQL versioning policy | `6c3347158e249096c8ce3671b6c5a8ed0893d136f69261e1bb597512dec798c0` |
| CNCF CloudNativePG project page | `aeafd230490d86cbb20684b9b7cc8bda93aeec8e08e0868d7aa6873c14677ae5` |
| CloudNativePG `SECURITY.md` at `e9eec0d` | `e110cacc046b07036aaead0bee37200aa3e326823f8ed95dad33ab8018a12308` |
| CloudNativePG `ADOPTERS.md` at `e9eec0d` | `03a885fe1b81bb59a5fcc43820a93f116486fa911c4c5159d5ca869aaf245375` |
| OpenSSF Scorecard API (operator) | `84e4f7c0d3c4600d0740a0a41174a3081a434ca75465fefb77c011b0415baa64` |
| GitHub API `repos/cloudnative-pg/cloudnative-pg` | `e1f1a6fdcebdf7ceac7b56ad323a6492bddc4ee3bac57adffa909ecf1d365991` |
| CISA KEV catalogue 2026.11.20 | `12c9ca4c5350ecacdf22bdce91b4ffcf06b8c8dc9c69b8bfb4c1a21be7a5fe50` |

Mutable pages and APIs may later return different bytes.

## Supply-chain qualification

**Pass, 2026-11-25, with the owner-approved A-7 rows.** The green gate
[rerun 45668871265](https://github.com/amazen33/EdgePulse/actions/runs/45668871265)
on `ebe032c` reports `Supply-chain: passed` with zero blockers and zero KEVs.
It used the Grype database built 2026-11-25T06:22:21Z and the CISA KEV
catalogue 2026.11.25. All 32 fixable Highs on this digest (glibc ×8, krb5
×24) now carry a block reason, and each matches an active A-7 row; no other
fixable High or Critical is present. The reviewed SBOM hash is unchanged.
This is a passing ADR-0049 disposition with evidenced exceptions, not a
vulnerability-free image. The A-7 rows expire 2026-12-14, and deploying the
image voids them.

The first PR #72
[gate run](https://github.com/amazen33/EdgePulse/actions/runs/45137906762)
on 2026-11-23 scanned all six active images, the Maven graph and the
lockfiles on Linux.
It used Syft 1.52.0, Grype 0.119.0 and OSV-Scanner 2.6.0, the Grype database
built 2026-11-23T06:28:32Z and the CISA KEV catalogue 2026.11.20. The old
digest was scanned as the previous input.

- `apt` and `libapt-pkg7.0` are 3.0.4 and `zlib1g` is
  `1:1.3.dfsg+really1.3.1-1+deb13u1`. CVE-2026-109518 and CVE-2026-85091 are
  gone, and CVE-2026-76844 is absent from both digests.
- There is no new fixable High or Critical identity compared with the old
  digest, and no KEV.
- That run's only blockers were 8 glibc Highs on this digest. 24 krb5 Highs
  started blocking on 2026-11-24 and 2026-11-25. A-7 proposed all 32 for
  this digest, and the owner approved it on 2026-11-25.

| Retained evidence | Identity / SHA-256 |
| --- | --- |
| [Green rerun artifact](https://github.com/amazen33/EdgePulse/actions/runs/45668871265/artifacts/15049665238) | `edgepulse-supply-chain-45668871265`, ID `15049665238`, GitHub-reported digest `73b5706bf57c53ef0ac39054c881d7efb00f496f18cce4b033fc161d569a4832` |
| Green rerun `report.json` | `1c4d1d6a20fed551f0044a3f6d7a7b8b5a3d17b7857335da89dadd844e80a331` |
| [Gate artifact](https://github.com/amazen33/EdgePulse/actions/runs/45137906762/artifacts/14800931763) | `edgepulse-supply-chain-45137906762`, ID `14800931763`, GitHub-reported digest `5e07c197e69a54155db2a4293782fec747699ffe9a59ff3184b7efe41ee2d240` |
| `report.json` | `bbf5a12d2666dd212bc2a152db19945b896ac700766dcf6342cc8bd49927ccd0` |
| Reviewed CycloneDX SBOM (`imageSBOM`) | `2cbd55cfd5ea6d43f5977f8e3fe25f0a8ce9a29148f205810608e720d8a2f714` |

The register's `imageSBOM` path is
`target/supply-chain/reviewed/b98ae0b74a12f20ccff32219be0e33fdd35c7e2e8e73c8bff9173f1128e167d1.cdx.json`.
The pinned Linux scanner generates it, and the licence gate checks it against
the hash above. The SBOM was neither hand-edited nor substituted.

## Retired records

- The old digest held a full verified record, not a legacy admission. Its
  register record leaves removal-only and is kept verbatim in
  [`retired-pg-18.6-admission-2026-11-23.json`](retired-pg-18.6-admission-2026-11-23.json).
  No legacy fingerprint, tier or deadline changes.
- The 35 A-6 rows for the old digest leave removal-only. Each exact block and
  its SHA-256 are in
  [`retired-pg-18.6-a6-rows-2026-11-23.json`](retired-pg-18.6-a6-rows-2026-11-23.json).

Nothing is deployed.
