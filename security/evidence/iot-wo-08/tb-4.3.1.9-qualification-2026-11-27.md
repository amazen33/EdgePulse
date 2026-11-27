# ThingsBoard CE 4.3.1.9 candidate review (draft)

IOT-WO-08 item 1 (TB 4.3.1.x refresh check), following the Amendment 2/3
pattern of the [4.3.1.8 review](tb-4.3.1.8-qualification-2026-10-30.md).
Recorded **2026-11-27**. **Not eligible before 2026-12-08**: no KEV
expedite applies, so ADR 0014's 14-day cool-off runs from the 2026-11-24
release. This draft changes no pin, chart, register entry or exception.
Its criteria are proposed for architect review and are not accepted. This
is not a deployment or milestone receipt, and it does not authorize
starting TB.

The [machine record](tb-4.3.1.9-qualification-2026-11-27.json) holds the
ladder fields and the exact-digest package proof that
`tools/ci/tb_refresh_evidence.py` re-verifies on every run.

## Candidate and release scope

The exact candidate is the 4.3.1.9 index digest
`docker.io/thingsboard/tb-node@sha256:3795fa72d86f8cf7908f532a742447fb18a2cbb7a69d9438f87f2a0ef233c4fc`,
scanned as linux/amd64 (`sha256:73c83bf8e30f37c5fbe5b84a3427c262f2790326ff4324b71b67a89911ad07af`).
The [publisher's tag metadata](https://hub.docker.com/v2/repositories/thingsboard/tb-node/tags/4.3.1.9)
dates the tag to 2026-11-24T14:21:41Z. The
[stable release](https://github.com/thingsboard/thingsboard/releases/tag/v4.3.1.9)
was published 2026-11-24T18:34:29Z, is neither a draft nor a prerelease,
and resolves to commit `d13c25a6f73880a6a4cd65fe5bcac981cda822b7`. Its
[exact licence](https://github.com/thingsboard/thingsboard/blob/v4.3.1.9/LICENSE)
is Apache-2.0, SHA-256
`c1b9df1275e769f3dbab000d1e457a2d4b0f28eb5da6c77e48dc37eeba202ed7`, the
same bytes as 4.3.1.8. The baseline is the pinned 4.3.1.8 digest
`sha256:5e2c180f3c48a9f4efd3e19d2f03c41b510ff1a935f25083657e0cf046a94872`.
No 4.4 (BUSL-1.1) release, fork or rebuild is proposed.

The release notes list security fixes for CVE-2026-116689,
CVE-2026-59171, CVE-2026-106554 and CVE-2026-110879. They do not change
Tomcat: the tagged
[`pom.xml`](https://github.com/thingsboard/thingsboard/blob/v4.3.1.9/pom.xml)
still pins `tomcat.version` 10.1.61, as 4.3.1.8 does.

## Supply-chain scan: net improvement passes; Tomcat remains

[TB comparison run 45916833345](https://github.com/amazen33/EdgePulse/actions/runs/45916833345)
on commit `d9cc6aea32d521e9cc5dbec28648c158fb3fe7e3` scanned both complete
images on Linux with pinned Syft 1.52.0 and Grype 0.119.0, using one
database (built 2026-11-26T06:22:34Z) and CISA KEV catalogue 2026.11.25.

| Measure | 4.3.1.8 baseline | 4.3.1.9 candidate |
| --- | ---: | ---: |
| Findings (distinct package, version, advisory) | 394 | 257 |
| Critical / High | 10 / 114 | 6 / 94 |
| Fixable Critical/High identities | 32 | 8 |
| New fixable Critical/High identities | — | **0** |
| KEV findings | 0 | **0** |

**Net improvement passed** under the unchanged rule. The job still exits
non-zero because the two Tomcat Criticals have no exception on the
candidate digest.

### Findings now covered or blocking

| Group | Advisories | Packages | 4.3.1.8 | 4.3.1.9 | Result |
| --- | --- | --- | --- | --- | --- |
| A-5 OpenJDK Critical | CVE-2026-91403, CVE-2026-114820 | `openjdk-25-jdk-headless`, `openjdk-25-jre-headless` | 25.0.4.1+1-1~deb13u1 | 25.0.5.1+2-1~deb13u1 | **Fixed** (4 rows) |
| A-5 OpenJDK High | CVE-2026-91415, CVE-2026-114938 to CVE-2026-114942 | same two | 25.0.4.1+1-1~deb13u1 | 25.0.5.1+2-1~deb13u1 | **Fixed** (12 rows) |
| A-5 zlib1g High | CVE-2026-85091 | `zlib1g` | 1:1.3.dfsg+really1.3.1-1+b1 | 1:1.3.dfsg+really1.3.1-1+deb13u1 | **Fixed** (1 row) |
| A-5 apt High | CVE-2026-109518 | `apt`, `apt-transport-https`, `libapt-pkg7.0` | 3.0.3 | 3.0.4 | **Fixed** (3 rows) |
| A-5 glibc High | CVE-2026-19499, CVE-2026-5435 | `libc-bin`, `libc6` | 2.41-12+deb13u4 | 2.41-12+deb13u5 | **Fixed** (4 rows) |
| Tomcat Critical | CVE-2026-116561, CVE-2026-118028 | `tomcat-embed-core` | 10.1.61 | 10.1.61 | **Still present**; blocks at once |
| Tomcat High | CVE-2026-106012, CVE-2026-116830, CVE-2026-117517, CVE-2026-118233, CVE-2026-118436 | `tomcat-embed-core` | 10.1.61 | 10.1.61 | **Still present**; blocks from 2026-12-10 |
| Tomcat High | CVE-2026-116600 | `tomcat-embed-websocket` | 10.1.61 | 10.1.61 | **Still present**; blocks from 2026-12-10 |

All 24 A-5 identities are absent from the candidate. All 8 Tomcat
identities carry over unchanged (fix 10.1.62), first seen 2026-11-26.
`libbrotli1` stays at the KEV-fixed 1.1.0-2+deb13u1.

Report-only observations in the candidate, all carried from the baseline:
three Critical advisories with no fix in `spring-webmvc` and
`spring-webflux` 6.2.19 (CVE-2026-47884, CVE-2026-47890, CVE-2026-47892;
first seen 2026-10-20), and CVE-2026-121649 in `tomcat-embed-core` 10.1.61
with a fix but Unknown severity. That advisory would become a ninth
blocking Tomcat finding if it is rated High or Critical.

### Consequence for the TB route

Only an upstream TB release can change the bundled Tomcat, and 4.3.1.9 does
not. Promoting 4.3.1.9 after 2026-12-08 would clear all 24 A-5 rows, but it
would still need the Tomcat findings bridged on the new digest, or a later
4.3.1.x patch with Tomcat 10.1.62 or newer.

The sequence recommended on 2026-11-28 takes the first route: qualify
4.3.1.9 and keep this PR in draft. The digest-specific bridge is proposal A-9,
`security/vulnerability-exception-proposals/iot-wo-08-tb-4.3.1.9-tomcat-2026-11-28.json`
(SHA-256 `2257195a05472138602b67014f2b1506560a8f6ef78cd60479ca7bc7e389bd64`;
[evidence](../vulnerability-exceptions/tb-4-3-1-9-tomcat-2026-11-28.md)).
It is not approved and not active. Its eight rows target this candidate
digest, expire 2026-12-23 and carry the A-8 conditions. A-8 covers only
the 4.3.1.8 digest. Until the promotion activates A-9, this candidate
gate stays red on the two Tomcat Criticals by design.

### Retained evidence

| Retained evidence | Identity / SHA-256 |
| --- | --- |
| [TB comparison artifact](https://github.com/amazen33/EdgePulse/actions/runs/45916833345/artifacts/15162342864) | `tb-refresh-evidence-45916833345`, ID `15162342864`; GitHub-reported archive SHA-256 `38c4f8b694ab8304aaedcf887956dc9fa559b695858d056d7e6119c0fc72b16e` |
| `report.json` | `fbfa34d3a0259a0a12f58d3809e131e8c87e76afe34a43da86262f7cae245a30` |
| `net-improvement.json` | `3bbb4c6da41ee651a200363e5c2020bc61f1700d65326f0a6e892b2ef8db9699` |
| `findings.json` | `c58a4015797d86729b206f1c661b148adfac8d0647d2efbc72415944d4218a36` |
| CISA KEV download (2026.11.25) | `a76360009e4a65794a2b8073df5475f7a787a3bb83c3bfad2b0c3434a067631a` |
| Reviewed candidate CycloneDX SBOM | `822508ed4a9af61570bd10a74bdb07cec63cfa48cdda58f082415d26472596bd` |

The package versions in the tables come from that run's Syft SBOMs. The
record's `expectedPackages` binds them to the candidate digest, so a later
run on a different image fails. The artifact expires after 90 days, so a
promotion PR needs a fresh full scan on the exact digest.

## Five supplier criteria (proposed, unreviewed)

Read **2026-11-27** from primary sources. The response hashes bind these
observations; mutable endpoints may later return different values.

- **Maturity, proposed pass:** stable release 4.3.1.9 with final
  distribution assets (above). The cool-off is a separate ADR 0014 rule and
  ends 2026-12-08.
- **Governance, proposed pass:** unchanged from the accepted 4.3.1.8
  review. The [ThingsBoard organisation](https://api.github.com/orgs/thingsboard)
  owns the [project repository](https://api.github.com/repos/thingsboard/thingsboard).
  The [tagged PR template](https://github.com/thingsboard/thingsboard/blob/v4.3.1.9/pull_request_template.md)
  is byte-identical to 4.3.1.8's, and the
  [contribution guide](https://thingsboard.io/docs/user-guide/contribution/how-to-contribute/)
  still documents team review, tests, pull requests and CLA review.
- **Activity/support, proposed pass:** the
  [CE release table](https://thingsboard.io/docs/releases/releases-table/)
  lists 4.3.x as Active LTS through 2027-07-20, with v4.3.1.9 (2026-11-24)
  as its current patch. The release notes list four security fixes.
- **Security process, proposed pass, with the target shortfall disclosed:** the
  [tagged disclosure policy](https://github.com/thingsboard/thingsboard/blob/v4.3.1.9/security.md)
  is byte-identical to 4.3.1.8's. The release API publishes the asset
  digests below; this uses the ADR's checksummed alternative and makes no
  signing claim.
- **Adoption, proposed pass:** the GitHub project API reports **22,731
  stars and 6,573 forks**, and the
  [Docker Hub repository API](https://hub.docker.com/v2/repositories/thingsboard/tb-node/)
  reports **5,604,931 pulls**, read at 2026-11-27T00:27:51Z. The vendor's
  [Supertech Agroline case](https://thingsboard.io/case-studies/agrolog/)
  names an end-user platform, edition unspecified. These figures are
  cumulative signals for the whole repository and image. They are not
  unique-user, production-installation or CE-only counts, and they do not
  show use of this patch or of any EdgePulse environment.
- **Supply chain, pending:** the scan above passes net improvement, but
  admission needs the cool-off and a green gate on the exact digest.

| Source | Observation / SHA-256 of response bytes |
| --- | --- |
| GitHub release API, v4.3.1.9 | published 2026-11-24T18:34:29Z, draft false, prerelease false; `f6e960130a4711d156d91a60b1fe27a733a5807e7a98f8a9433956a6bd4acc98` |
| Docker Hub tag API, 4.3.1.9 | digest `sha256:3795fa72…33c4fc`, pushed 2026-11-24T14:21:41Z; `3f4c9cec5030b3d6b5474e39c46f8e1524a3e44bd8020d40b06b9e5162ea4c4b` |
| GitHub organisation API | `thingsboard`, type `Organization`; `a7bb89fd2be0e6cb9d134faadb02634346a1d7969fa673d8bdd3d0d926555c18` |
| GitHub project API | 22,731 stars, 6,573 forks; `5defce6d83a7f35f4112822927396c5646c350d749162f7494360fb4e7a36075` |
| Docker Hub tb-node API | 5,604,931 pulls; `97bd8ad3e48b197838cb23e1158f053447fc1388507f4e2adb84d4b9280c3fbc` |
| Tagged `security.md` | identical to v4.3.1.8; `f81e09139512d33725c7622e15458316cb24eded24aab3e30fe92de70143c80c` |
| Tagged PR template | identical to v4.3.1.8; `f5db6e426fb3902538d9c95ebcc2940cdc1defe0d117ceb69c19a962bf5f9ba8` |
| Tagged `pom.xml` | version 4.3.1.9, `tomcat.version` 10.1.61; `27516410c552dcf9f19d23e88907ab138e2a513d6945436b71d7e2daee64dd0e` |
| CE release table | 4.3.x Active LTS to 2027-07-20, current patch v4.3.1.9; `3b90317212021a193b1ec60998018d4fe38dad7e6aad6f52d5ad59ad0b2d60e5` |
| OpenSSF Scorecard API | 4.7, dated 2026-11-23, commit `d39bcf650ed7aefd84267b7ec452b743cb7a3def`; Security-Policy 10, Signed-Releases 0; `9483bcfbdb1326818ed01e87c7835ddd1adebfb0161cc4981d2b3cae502776e3` |

| Published distribution | Publisher SHA-256 |
| --- | --- |
| `thingsboard-4.3.1.9.deb` | `24b69455fe3812aa4524f94e229f6ec37225d7e5f79f231066fd301750da7e3d` |
| `thingsboard-4.3.1.9.rpm` | `ce1a2ffba6288e0e47af6ef87055de6c34d3bd4bf5cb36019c0c250e1fb39eb5` |
| `thingsboard-windows-4.3.1.9.zip` | `2b25600d3d8a48f0d7d59fcb783eb66630457742c9c9037d1f1a4493b381f162` |

The distribution files were not downloaded or executed. The Scorecard
(4.7) is lower than at the 4.3.1.8 review (4.9) and is still below the
ADR's target of 6, which the accepted E-3 review treats as a target rather
than a floor.

## Before promotion (not part of this PR)

1. Wait until the cool-off ends on 2026-12-08.
2. Rerun the full Linux scan on the exact digest, then propose the pin,
   chart, register (full ADR-0054 record) and `imageSBOM` change.
3. Remove the A-5 rows that the scan clears.
4. Activate A-9 (once approved by hash) and retire the eight A-8 rows for
   the old digest, all in the same reviewed change.
5. Watch CVE-2026-121649: if it is rated High or Critical, it needs its own
   entry with fresh evidence.

Starting TB anywhere still voids the A-5 rows.
