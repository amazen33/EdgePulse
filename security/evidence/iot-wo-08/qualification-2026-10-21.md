# gRPC refresh supplier qualification (2026-10-21)

IOT-WO-08; ADR-0054's six criteria, applied to the twelve newly runtime-reachable
Maven inputs listed in [the exact artifact inventory](candidate-artifacts-2026-10-21.json).
This is supplier/artifact qualification and code-test evidence. It does not
establish a deployment, an integration receipt, a support subscription or MS1
acceptance. No new legacy admission is used.

## gRPC 1.84.0 (eight runtime artifacts)

Applies to grpc-api, grpc-stub, grpc-protobuf, grpc-protobuf-lite,
grpc-netty-shaded, grpc-util, grpc-core and grpc-context; Apache-2.0, tier 2.

- **Maturity:** [1.84.0 is a final release](https://github.com/grpc/grpc-java/releases/tag/v1.84.0).
  Maven Central published the exact artifacts on 2026-09-01; the release was
  announced September 2. They meet the fourteen-day cooling-off period.
- **Governance:** [CNCF hosts gRPC at Incubating maturity](https://www.cncf.io/projects/grpc/).
- **Activity/support:** the September release is within six months. The
  [published Java/transport compatibility policy](https://github.com/grpc/grpc-java/blob/v1.84.0/README.md)
  and [security compatibility table](https://github.com/grpc/grpc-java/security/policy)
  cover the 1.84.x line, including its shaded Netty dependency. The upstream
  [CVE process](https://github.com/grpc/proposal/blob/master/P4-grpc-cve-process.md)
  describes supported security handling. The pinned scan confirms that the
  old MadeYouReset advisory is absent from this exact candidate.
- **Security process:** the same policy links private reporting, coordinated
  disclosure and CVE handling. Exact artifacts are checksummed in Maven
  Central; [reviewed artifact hashes](candidate-artifacts-2026-10-21.json)
  and [published checksum comparisons](published-checksums-2026-10-21.json)
  bind this review to their bytes. OpenSSF Scorecard **7.3**, dated
  2026-10-12, [source](https://api.securityscorecards.dev/projects/github.com/grpc/grpc-java).
- **Supply chain:** the existing pinned ADR-0049 scan passes. Its identity
  CycloneDX BOM contains the exact eight candidate versions and their JAR
  hashes. OSV finds zero advisories for each; no exception is used for them.
  [Scan binding and counts](scan-2026-10-21.json).
- **Adoption:** CNCF Incubating satisfies the criterion; the
  [project's public adopter page](https://grpc.io/about/)
  supplies additional production-use context. This does not claim deployment
  of this exact patch by any named adopter.

## Protobuf Java 3.25.9

BSD-3-Clause, tier 1. The matching protoc and protobuf-bom inputs are build-time
inputs, not additional runtime admissions.

- **Maturity:** a final 3.x Java maintenance release; the exact POM/JAR was
  published 2026-03-25. It is not represented as a release within six months.
- **Governance:** [Google maintains Protobuf](https://github.com/protocolbuffers/protobuf).
  The vendor-backed route is used: Google publishes a
  [commercial support portfolio](https://cloud.google.com/support) and an
  [Assured OSS service with a commercial premium tier](https://docs.cloud.google.com/assured-open-source-software/docs/overview).
  Its [supported Java package families](https://docs.cloud.google.com/assured-open-source-software/docs/supported-packages)
  include protobuf-parent, guava-parent and proto-google-common-protos.
  This establishes an OSS-specific supplier offering, not a purchased
  EdgePulse support contract. The reviewed artifacts come from Maven Central;
  no Assured OSS artifact, account access, provenance or subscription is used.
- **Activity/support:** [the language-specific version policy](https://protobuf.dev/support/version-support/)
  explicitly keeps Java 3.25.x and protoc 25.x in maintenance, through
  2027-03-31. The project has final 36.x releases within six months; activity
  is project-level, while the exact Java candidate's maintenance status is
  checked separately. The
  [published Java security fix](https://github.com/protocolbuffers/protobuf/security/advisories/GHSA-735f-pc8j-v9w8)
  establishes delivery of fixes, rather than inferring it from commit counts.
- **Security process:** [the published disclosure and CVE policy](https://github.com/protocolbuffers/protobuf/blob/main/SECURITY.md)
  provides private Google reporting and GitHub security advisories. Maven
  Central supplies checksums; the exact JAR/POM hashes are retained in the
  artifact inventory. Scorecard **6.4**, dated 2026-10-21,
  [source](https://api.securityscorecards.dev/projects/github.com/protocolbuffers/protobuf).
- **Supply chain:** the exact 3.25.9 runtime JAR is in the scanned BOM and has
  zero OSV findings. The passing gate and digest binding are in the scan record.
- **Adoption:** [the upstream overview](https://protobuf.dev/overview/)
  describes extensive production use at Google. Adoption of the project is
  distinguished from evidence about this exact patch or an EdgePulse runtime.

## Guava 33.6.0-android and failureaccess 1.0.3

Apache-2.0, tier 2. These are runtime libraries, not annotation exemptions.
The pre-existing build-tool classification of failureaccess is replaced with
a full runtime record because the refreshed resolved tree now reaches it.

- **Maturity:** final releases in the exact artifact inventory. Guava's
  Android-compatible flavour is an ordinary Java library and does not require
  an Android environment. Neither input is a prerelease.
- **Governance:** [Google's maintained Guava project](https://github.com/google/guava)
  owns both inputs. The vendor-backed route uses the Google commercial
  Assured OSS offering and its listed Guava family, with the same bounded
  supplier-capacity scope described above.
- **Activity/support:** [the published release policy](https://github.com/google/guava/wiki/ReleasePolicy)
  covers the 33.x release family and its flavours; the
  [compatibility policy](https://github.com/google/guava/wiki/Compatibility)
  and [README's compatibility guarantees](https://github.com/google/guava/blob/master/README.md)
  document supported Java/API compatibility. The project has final September
  2026 releases, within six months. Exact candidate dates (Guava April 14,
  failureaccess March 19, 2025) are retained separately, not described as new
  releases. Security fixes are delivered through the maintained release family
  and the [published security process](https://github.com/google/guava/security/policy).
  This is not a claim of an LTS/EOL date that upstream has not published.
- **Security process:** that policy provides private Google triage and
  coordinated disclosure using GitHub advisories. Exact Maven checksums and
  JAR hashes are retained. Scorecard **8.8**, dated 2026-10-20,
  [source](https://api.securityscorecards.dev/projects/github.com/google/guava).
- **Supply chain:** the exact two runtime JARs appear in the scanned BOM and
  have zero OSV findings. No exception or legacy admission is used for them.
- **Adoption:** the official README identifies extensive use inside Google's
  Java systems and identifies failureaccess as the linkage dependency. This
  is project/library adoption evidence, not use of the exact selected versions
  by a named production installation.

## Google common protos 2.64.1

Apache-2.0, tier 2; an ordinary runtime contract library, not an annotation JAR.

- **Maturity:** final 2.x artifact, published 2026-01-13, from the exact Maven
  POM/JAR inventory. [The project's stability policy](https://github.com/googleapis/google-cloud-java#versioning)
  distinguishes stable APIs from preview APIs; the candidate has no prerelease
  suffix. No preview API is introduced into EdgePulse source.
- **Governance:** Google is the maintaining vendor, with the public commercial
  Assured OSS offering linked above explicitly lists proto-google-common-protos.
  The
  [official component documentation](https://cloud.google.com/java/docs/reference/proto-google-common-protos/latest/overview)
  establishes its place in Google's Java library family. Supplier-capacity
  evidence does not assert an EdgePulse support subscription.
- **Activity/support:** the official documentation's current final 2.x release
  and October 2026 update establish current project activity. The
  [Java library versioning policy](https://github.com/googleapis/google-cloud-java#versioning)
  documents stable-major compatibility, with security handling through the
  vendor's private reporting process. The exact January candidate date is
  recorded, not described as a recent release or an independently promised LTS.
- **Security process:** [the current Java supplier security policy](https://github.com/googleapis/google-cloud-java/blob/main/SECURITY.md)
  documents private intake and advisory handling. Exact Central POM/JAR hashes
  and published checksum evidence are retained. A component-specific
  Scorecard was not available in this review; no score is invented.
- **Supply chain:** the exact 2.64.1 JAR appears in the scanned identity BOM,
  with zero OSV findings and no exception.
- **Adoption:** Google's public Java API/Cloud library distribution consumes
  these shared protocol types, as shown by the official component documentation
  and the [gRPC 1.84.0 grpc-protobuf POM](https://repo.maven.apache.org/maven2/io/grpc/grpc-protobuf/1.84.0/grpc-protobuf-1.84.0.pom).
  This is supplier distribution/adoption, not a claim of a deployed EdgePulse
  integration or use of this precise patch by every Cloud client.

## Exclusions, unchanged admissions and scope

The [mechanical exclusion check](annotation-only-2026-10-21.json) admits only
the approved JSpecify and Animal Sniffer exclusions, including own-coordinate
Maven metadata. Error Prone 2.50.0 is ineligible because it contains an enum;
the architect's ordered fallback keeps legacy 2.28.0 and its fingerprint
unchanged. Other retained legacy entries and due dates are unchanged. Only
entries absent from the independently resolved inventory retire under the
existing removal-only guard. No named exception or permitted licence expands.

The eight gRPC artifacts are the existing transport's refreshed implementation;
Protobuf and its selected utility/contract dependencies preserve the existing
wire/API contract. Tier-1 Protobuf remains selected for serialization; tier-2
gRPC remains the approved transport. No tier-3/4 candidate or shared runtime
JAR is introduced, and no alternative transport/protocol is silently substituted.

The [runtime proof](jspecify-exclusion-2026-10-21.json) and CI establish only
the tested foundation behavior: identity 214 (including 15 REST/gRPC equivalence
cases), contract tests 61. Spring, Jackson, Log4j and Java versions are unchanged.
