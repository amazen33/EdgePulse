# ThingsBoard CE 4.3.1.8 supplier review

IOT-WO-08 Amendment 3, E-3 and Review of PR #56, A-1. Reviewed **2026-10-30**.
The five supplier criteria were accepted in the
[recorded review](../../../docs/work-orders/IOT-WO-08-image-and-dependency-refresh.md#review-of-pr-56-2026-10-30-architect).
The sixth criterion is evidenced by the green Linux reruns below. Final
architect diff review and owner merge remain pending; this is not a
deployment or milestone receipt.
The [machine record](tb-4.3.1.8-qualification-2026-10-30.json) contains the
unchanged ladder's result, HTTPS evidence and date fields. The full register
record has no legacy admission. A-1's two exact approved exceptions retain
their conditions; no gate rule or High approval is changed here.

## Candidate and release scope

The exact candidate is `docker.io/thingsboard/tb-node@sha256:5e2c180f3c48a9f4efd3e19d2f03c41b510ff1a935f25083657e0cf046a94872`.
The [publisher's tag metadata](https://hub.docker.com/v2/repositories/thingsboard/tb-node/tags/4.3.1.8)
dates the image to 2026-10-26T18:50:22.478326Z. The
[stable release](https://github.com/thingsboard/thingsboard/releases/tag/v4.3.1.8)
was published 2026-10-27T07:41:52Z, is neither a draft nor a prerelease, and
resolves to commit `ebbfc6789b81a4e04cae2711208130fb2841b31f`.
Its [exact licence](https://github.com/thingsboard/thingsboard/blob/v4.3.1.8/LICENSE)
is Apache-2.0, SHA-256 `c1b9df1275e769f3dbab000d1e457a2d4b0f28eb5da6c77e48dc37eeba202ed7`.
No 4.4, source-available release, fork or rebuild is proposed.

## Five supplier criteria

- **Maturity — pass:** the stable release above is version 4.3.1.8, with
  final distribution assets. This meets the stable-release criterion.
- **Governance — pass:** the [ThingsBoard organisation](https://api.github.com/orgs/thingsboard)
  owns the [project repository](https://api.github.com/repos/thingsboard/thingsboard).
  The [exact-release POM](https://github.com/thingsboard/thingsboard/blob/v4.3.1.8/pom.xml)
  attributes copyright to The Thingsboard Authors. The official
  [contribution guide](https://thingsboard.io/docs/user-guide/contribution/how-to-contribute/)
  identifies the ThingsBoard team as issue reviewers: contributors seek feedback
  before implementation, run tests, then submit a pull request and complete CLA
  review. The [tagged PR template](https://github.com/thingsboard/thingsboard/blob/v4.3.1.8/pull_request_template.md)
  requires issue/milestone references, compatibility and test evidence. These
  identify the maintaining organisation and its contribution process; no
  foundation status, multi-employer count or paid support entitlement is inferred.
- **Activity/support — pass:** the
  [CE release table](https://thingsboard.io/docs/releases/releases-table/)
  identifies 4.3.x as Active LTS through 2027-07-20. The recent patch's
  release notes enumerate security fixes. The publisher also
  [explicitly preserves CE 4.3 security updates](https://thingsboard.io/blog/one-thingsboard-source-available/).
  The accepted KEV expedite applies to the shorter cooling-off period.
- **Security process — pass, with a disclosed target shortfall:** the
  [tagged disclosure policy](https://github.com/thingsboard/thingsboard/blob/v4.3.1.8/security.md)
  provides private reporting, investigation and a three-business-day response.
  The exact release documents CVE fixes. The
  [official release API](https://api.github.com/repos/thingsboard/thingsboard/releases/tags/v4.3.1.8)
  publishes the distribution checksums below. This uses the ADR's
  **checksummed** alternative, not a claim of signed release artifacts.
- **Adoption — pass:** the [primary GitHub project API](https://api.github.com/repos/thingsboard/thingsboard)
  reports **22,631 stars and 6,543 forks**; the
  [publisher's Docker Hub repository API](https://hub.docker.com/v2/repositories/thingsboard/tb-node/)
  reports **5,567,518 pulls**. Both were read at **2026-10-30T12:04:50Z**.
  ThingsBoard's own [Supertech Agroline case](https://thingsboard.io/case-studies/agrolog/)
  identifies a named end-user platform using ThingsBoard as its backend in
  cloud and on-premise installations, with edition unspecified. The metrics
  are cumulative project/image-wide adoption signals; they are not unique-user,
  production-installation or CE-only counts. Neither the metrics nor the case
  proves use of 4.3.1.8 or an EdgePulse environment.

### Primary-source observations for the revised criteria

Read **2026-10-30**. API response hashes bind the observations above; mutable
endpoints may subsequently return different counts. The organisation and
repository APIs identify ownership; contribution requirements come from the
official guide and the exact-tag template, not a commercial-services page.

| Source | Observation / SHA-256 of response bytes |
| --- | --- |
| GitHub organisation API | `thingsboard`, type `Organization`, website `https://thingsboard.io`; `1ae149798484238400ffa67dbeeabadf6d3c3bbf1089b95fe960cfb4c5eeba8c` |
| GitHub project API | `thingsboard/thingsboard`, owner `thingsboard`; 22,631 stars, 6,543 forks; `ae830f7d15e29aafa6c7fcb0f10673cacf2437bfee201db8ec17b1aa7c78e52c` |
| Docker Hub tb-node API | namespace `thingsboard`, repository `tb-node`; 5,567,518 pulls; `cf9618fe7e0db1a1b4cb45531b64976ddb03304d8602b2a778fc5c456059d15c` |
| Exact-release POM | Copyright attribution; `7989ea8b76fac44b8608202ba0418abf8421772bfc79eaa506ae7290234efa6a` |
| Exact-release PR template | Issue, milestone, compatibility and testing checklist; `f5db6e426fb3902538d9c95ebcc2940cdc1defe0d117ceb69c19a962bf5f9ba8` |
| Official contribution guide | Team review, tests, PR and CLA process; `efad4a05d5f11a54e309e457a466b5df209ca34b1454303e640fece96027196b` |

### Release checksums

| Published distribution | Publisher SHA-256 |
| --- | --- |
| `thingsboard-4.3.1.8.deb` | `a53267c306e9e1c350ded5feba2a541fbf5ceea6bcfd223e4d7829c102d91e2b` |
| `thingsboard-4.3.1.8.rpm` | `143d8223f612dfdcd26e54fa0dc1edb32cd1821d18197eab44cef11bafab6908` |
| `thingsboard-windows-4.3.1.8.zip` | `28671b4069150641ce563a8a91448627a033e89b5c94413ed74b77ea35372333` |

These are published metadata checksums; the three distribution files were
not downloaded or executed. The separately scanned OCI image is the input
EdgePulse proposes to use.

## Scorecard and assurance limits

The [primary OpenSSF API](https://api.securityscorecards.dev/projects/github.com/thingsboard/thingsboard)
reports **4.9**, dated 2026-10-26, for default-branch commit
`7a53801216e14dd8b2127787f54838ebd7a3a526`. Security-Policy is 10 and
Signed-Releases is 0. This is below the ADR's target of 6. The accepted
wording states a target, not an absolute score floor; that interpretation
and the shortfall were accepted in the recorded E-3 review. No score is fabricated,
and this assessment does not establish signing or provenance. A verified
GitHub commit signature is not release-artifact signature evidence.

## Supply-chain qualification — pass under A-1

The [full Linux PR scan](https://github.com/amazen33/EdgePulse/actions/runs/41098298463)
passed on owner commit `64ad953aeac124ae7a9d60fa574651926972e47a`:
six active digest-pinned images, the Maven graph (all scopes and executed
plugin classpaths) and lockfiles; **1,024 findings, zero blockers and zero
KEVs**. Pinned tools were Syft 1.52.0, Grype 0.119.0 and OSV-Scanner 2.6.0.
The Grype database was built 2026-10-30T06:23:28Z. The full scan's fetched
CISA catalogue was 2026.10.29; the separate TB comparison fetched 2026.10.30.
These are the catalogues reported by the two runs, not an inferred single
snapshot. Both report zero KEVs.

The [full current/candidate TB comparison](https://github.com/amazen33/EdgePulse/actions/runs/41098298743)
also passed. Both complete images used one database snapshot. Findings fell
**327 → 269**, Critical **9 → 8** and High **83 → 61**, with **zero new
fixable Critical/High identities**. Brotli is `1.1.0-2+deb13u1` in the
candidate. Both OpenJDK packages remain `25.0.4.1+1-1~deb13u1`.

The only TB exception matches are the two owner-approved A-1 Critical rows
for CVE-2026-91403. The original proposal file remains immutable, SHA-256
`2a14597cadf94c4365f1dbad0f446aa251f556ee9bf941d06dd6e5d6f8c953c9`;
its active copies differ only by `approvedBy: amazen33`. This is a passing
ADR-0049 disposition with evidenced exceptions, not a vulnerability-free image.

**A-1 conditions remain binding:** starting TB anywhere (kind rehearsal,
lab or deployment) before the fixed upstream image voids both rows. They
expire 2026-11-19, with no in-place extension. They do not cover the two
OpenJDK Highs, CVE-2026-91415, first seen 2026-10-22 and blocking from
2026-11-05 if unresolved. Their separate A-2 proposals remain unapproved.

| Retained evidence | Identity / SHA-256 |
| --- | --- |
| [Full scan artifact](https://github.com/amazen33/EdgePulse/actions/runs/41098298463/artifacts/12997955992) | `edgepulse-supply-chain-41098298463`, ID `12997955992`; GitHub-reported archive SHA-256 `1305a7684fcfd5d4bd59d5ae335ba98ae11a1906af9dc9db0edbb6c8b2bc5ea0` |
| Full scan `report.json` | `7fa06ffc8b1ae99519e5455874f3435078bd4157f54b3f562a40c672743d7b0f` |
| [TB comparison artifact](https://github.com/amazen33/EdgePulse/actions/runs/41098298743/artifacts/12996554331) | `tb-refresh-evidence-41098298743`, ID `12996554331`; GitHub-reported archive SHA-256 `43e7f76724939e7a853ceae635a6810857f49c08257106576f451425566982b1` |
| TB comparison `report.json` | `94a698eadc4236e93e1cf5d5585894fae0820118db9843873a51d3116ffff4bc` |
| Reviewed TB CycloneDX SBOM, identical in both runs | `b50daf45349bc6a90bf6c6da64cc6c5e9ee2f602f1e0d37467c541026cf70349` |

The register's `imageSBOM` path is
`target/supply-chain/reviewed/5e2c180f3c48a9f4efd3e19d2f03c41b510ff1a935f25083657e0cf046a94872.cdx.json`.
It is generated by the pinned Linux scanner and verified against the hash
above; no placeholder or hand-edited SBOM is used. Linux Maven verification
passed with **214 identity + 61 contract tests**, no skips; the supply-chain
suite passed **105 tests**. No supplier criterion, scan or local test
establishes real-environment acceptance or authorizes starting TB.
