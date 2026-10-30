# ThingsBoard CE 4.3.1.8 supplier review

IOT-WO-08 Amendment 3, E-3. Reviewed **2026-10-30**. Proposed for architect
and owner review; this is not an admission, deployment or milestone receipt.
The [machine record](tb-4.3.1.8-qualification-2026-10-30.json) contains the
unchanged ladder's result, HTTPS evidence and date fields. Supply chain is
pending; no active exception, legacy admission or gate rule is changed here.

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
- **Security process — pass, with a target shortfall for review:** the
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
and the shortfall require explicit architect review. No score is fabricated,
and this assessment does not establish signing or provenance. A verified
GitHub commit signature is not release-artifact signature evidence.

## Supply-chain qualification remains pending

The full current/candidate comparison must run with the pinned scanners on
Linux CI, using one vulnerability database snapshot and the current KEV
catalogue. It must retain both complete image SBOMs and scan outputs and
reject newly introduced fixable Critical/High package/advisory identities.
The earlier Windows package-database check does not replace that comparison.
The two OpenJDK Critical proposals have empty approval fields and are not
active exceptions. A scan blocked by those proposals does not qualify as an
ADR-0049 pass. No supplier criterion establishes real-environment acceptance.
