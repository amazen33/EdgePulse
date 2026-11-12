# Guava 33.7.2 qualification (2026-11-03)

IOT-WO-08 refresh of GHSA-xxph-c9ww-hj94 / CVE-2026-102554 in the identity
runtime and executed Protobuf plugin classpath. This branch is stacked on
PR #60 at `6321bb2`; its 22 pending Spring cool-off records are unchanged.
This is supplier, dependency and build evidence. Nothing was deployed.

## Artifact and licence review

The [machine record](guava-33.7.2-qualification-2026-11-03.json) binds the
exact JAR/POM hashes, publication dates, classes and six criterion results.
Both Guava flavours were published to Maven Central on 2026-09-29 at
14:47:28 UTC; the [final upstream release](https://github.com/google/guava/releases/tag/v33.7.2)
was published at 14:53:52 UTC. Both meet the 14-day cool-off.

The exact [Android parent POM](https://repo.maven.apache.org/maven2/com/google/guava/guava-parent/33.7.2-android/guava-parent-33.7.2-android.pom)
and [JRE parent POM](https://repo.maven.apache.org/maven2/com/google/guava/guava-parent/33.7.2-jre/guava-parent-33.7.2-jre.pom)
declare Apache-2.0, inherited by their child POMs. The runtime Android
artifact remains tier 2 (`allowed`); the plugin JRE copy is `build-tool`.
The plugin's newly resolved Error Prone annotations 2.50.0 and J2ObjC
annotations 3.1 are Apache-2.0 build tools, with exact POM/hash evidence
in the machine record. Their runtime versions remain 2.28.0 and 1.3.
No annotation exemption or runtime reclassification is introduced.

## Runtime supplier criteria

Read on 2026-11-03, following the
[previous Guava/failureaccess review](qualification-2026-10-21.md#guava-3360-android-and-failureaccess-103).

- **Maturity: pass.** The final 33.7.2 release and exact Central publication
  timestamps establish a non-prerelease older than 14 days. The Android
  flavour is a Java library, as the upstream
  [release policy](https://github.com/google/guava/wiki/ReleasePolicy) explains.
- **Governance: pass.** [Google maintains Guava](https://github.com/google/guava).
  The vendor-backed route is the same bounded one used in the earlier
  review: Google offers [Assured OSS](https://docs.cloud.google.com/assured-open-source-software/docs/overview)
  and lists the Guava family among its
  [supported packages](https://docs.cloud.google.com/assured-open-source-software/docs/supported-packages).
  This is supplier-capacity evidence; EdgePulse has no claimed support
  subscription and uses the public Central artifacts, not Assured OSS builds.
- **Activity/support: pass.** The September security patch demonstrates
  recent maintenance of the 33.x family. The
  [release policy](https://github.com/google/guava/wiki/ReleasePolicy),
  [compatibility policy](https://github.com/google/guava/wiki/Compatibility)
  and [tagged README](https://github.com/google/guava/blob/v33.7.2/README.md)
  cover the Java/API and Android/JRE compatibility boundaries. No fixed
  LTS or EOL date absent from upstream policy is claimed.
- **Security process: pass.** The
  [supplier policy](https://github.com/google/guava/security/policy) identifies
  Google's private vulnerability intake and coordinated advisories. The
  [published advisory](https://github.com/google/guava/security/advisories/GHSA-xxph-c9ww-hj94)
  and release identify the allocation fix. The supplier's
  [OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/google/guava)
  is 8.8, dated 2026-11-02T18:15:11Z; the response hash is recorded.
- **Supply chain: pass.** The exact candidate
  [full Linux/amd64 CI run](https://github.com/amazen33/EdgePulse/actions/runs/41642485897)
  passed ADR-0049 with zero blockers, no introduced fixable Critical/High
  identity, and zero findings or exceptions in either requested Guava target.
  The [scan record](guava-33.7.2-scan-2026-11-03.json) binds the artifact,
  exact BOM/JAR hashes, raw OSV results, tool versions and before/after rows.
  The runtime Guava record now has all six verified criteria.
- **Adoption: pass.** The supplier's tagged README describes extensive use
  within Google Java projects and by other companies. This is library-family
  adoption evidence; it does not claim a named installation uses this patch.

## Scope and compatibility

The generated resolved tree and isolated plugin BOM contain one Guava
version each: 33.7.2-android for identity and 33.7.2-jre for Protobuf.
Failureaccess 1.0.3 and listenablefuture
9999.0-empty-to-avoid-conflict-with-guava retain their hashes and registry
records. Identity's existing JSpecify exclusions are unchanged and its
runtime classpath contains no JSpecify. Error Prone 2.28.0 and J2ObjC 1.3
retain their existing runtime admissions. Stale Guava 33.6.0-android,
33.4.8-jre and build-only JSpecify 1.0.0 entries were removed only after the
collector proved they were absent from the resolved inventory.

`mvn -B -f pom.xml clean verify` passed locally on Windows with registered
Maven 3.9.11 and Temurin 21.0.12.1+1: identity 214, contract tests 61,
including 15 REST/gRPC transport-equivalence tests; no failures or skips.
These checks preserve legitimate behavior; the pinned Linux scan supplies
the static security-clearance evidence above. No native-deserialization denial-of-service
PoC was executed.

The Maven 3.9.11 distribution separately bundles Guava 33.4.8-jre. The
Protobuf plugin override does not replace the host Maven installation's
libraries. This refresh clears only the two specified scan targets; it does
not claim every Guava copy in the development toolchain was upgraded.
