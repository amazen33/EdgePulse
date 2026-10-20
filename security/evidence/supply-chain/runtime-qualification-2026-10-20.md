# Supported runtime qualification inputs (2026-10-20)

IOT-WO-02 Amendment 5. These are upstream supplier checks and static artifact
inputs, not EdgePulse runtime acceptance. Per-component supply-chain results
and SBOM hashes are in the [evidence index](runtime-evidence-index-2026-10-20.json).
The new Tomcat and minimal PostgreSQL inputs need no exceptions; the owner
explicitly approved the exact initial exception list for other components
on 2026-10-20 ([record](../vulnerability-exceptions/owner-approval-2026-10-20.json)).
Nothing was deployed or run against an environment.

## Tomcat 10.1.60: core, EL and WebSocket

- Maturity: stable Servlet 6.0 / Jakarta EE 10 implementation; the
  [version policy](https://tomcat.apache.org/whichversion.html) explicitly lists
  10.1 as a currently supported stable line, Java 11 or later.
- Governance: [Apache Software Foundation project](https://tomcat.apache.org/).
- Activity/support: Maven Central published the
  [10.1.60 POM](https://repo.maven.apache.org/maven2/org/apache/tomcat/embed/tomcat-embed-core/10.1.60/tomcat-embed-core-10.1.60.pom)
  on 2026-09-09T22:43:58Z, within six months and over fourteen days old.
  [Security fixes](https://tomcat.apache.org/security-10.html) include the
  CVE-2025-24813 correction starting at 10.1.35. No cooling-off waiver is used.
- Security process: [disclosure policy](https://github.com/apache/tomcat/blob/10.1.60/SECURITY.md),
  the published CVE list above, and signed/checksummed
  [release artifacts](https://archive.apache.org/dist/tomcat/tomcat-10/v10.1.60/).
  [Scorecard](https://api.securityscorecards.dev/projects/github.com/apache/tomcat):
  6.1, dated 2026-10-12; checked 2026-10-20.
- Adoption: the project's
  [public production adopter list](https://cwiki.apache.org/confluence/display/TOMCAT/PoweredBy).
- Licence: [unmodified Apache-2.0 release](https://github.com/apache/tomcat/blob/10.1.60/LICENSE),
  tier 2. No new weak-copyleft permission or legacy admission.
- Supply chain: actual per-module CycloneDX BOM, resolved Maven tree,
  SHA-256 artifact hashes and OSV results are required. The final scan receipt
  records the result; a unit test or this supplier review alone is insufficient.

## CloudNativePG PostgreSQL 18.6 minimal, dated October 5

- Maturity: stable PostgreSQL 18.6, not a beta. The image is an official
  [supported operand flavour](https://github.com/cloudnative-pg/postgres-containers#image-types).
- Governance: [CloudNativePG](https://www.cncf.io/projects/cloudnativepg/) is a
  CNCF project; PostgreSQL has its own established project governance.
- Activity/support: [PostgreSQL version policy](https://www.postgresql.org/support/versioning/)
  covers major 18; [18.6](https://www.postgresql.org/docs/release/18.6/) was
  released 2026-08-13. The dated image tag is
  `18.6-202610050823-minimal-trixie`, built 2026-10-05T08:23:19Z. Its immutable
  index is `sha256:37ade18dbdddba430858c72725aceeec66f33fa5333e82ea1df4942f6c1c83a3`.
  Registry enumeration found later October 12 and 19 builds; neither meets
  fourteen days on the review date.
- Security process: [CloudNativePG disclosure policy](https://github.com/cloudnative-pg/cloudnative-pg/security/policy),
  signed images, SBOMs and provenance described in the
  [operand documentation](https://cloudnative-pg.io/docs/current/#container-images).
  [Operator Scorecard](https://api.securityscorecards.dev/projects/github.com/cloudnative-pg/cloudnative-pg):
  9.5, dated 2026-10-20. The separate postgres-containers Scorecard endpoint
  returned HTTP 404; no score is invented for that repository.
- Adoption: [named production users](https://github.com/cloudnative-pg/cloudnative-pg/blob/main/ADOPTERS.md)
  include EDB BigAnimal and Clustermarket. This proves supplier adoption only.
- Licence: Apache-2.0 packaging plus PostgreSQL, tier 2, from the
  [exact image source revision](https://github.com/cloudnative-pg/postgres-containers/tree/ff34de135f29e04a841247ea9686d7a80b663005).
  The complete generated SBOM is separate evidence for the image's packages.
- Minimal removes Barman Cloud, extra extensions/locales and PostgreSQL 18
  LLVM JIT support supplied by larger flavours. The existing chart declares
  no backup plugin or optional extension. Static rendering is checked; no
  live compatibility or backup acceptance is claimed. Scan counts quantify
  the change against the previous system image.

## Closed runtime lines retained for Part C

The architect's ruling keeps current versions and complete legacy fingerprints
unchanged. No support pass or deadline extension is recorded.

| Line / current runtime | Newest public patch | Patch publication | Public support end / source | Remediation |
| --- | --- | --- | --- | --- |
| Spring Framework 6.1.13 | 6.1.21 | 2025-06-12 | Last public 6.1 release, [vendor announcement](https://spring.io/blog/2025/06/12/spring-framework-6-1-21-and-6-2-8-releases-fix-cve-2025-41234/) | IOT-WO-02 Part C, due 2026-11-19 |
| Spring Boot 3.3.4 | 3.3.13 | 2025-06-19 | 2025-06-19, [vendor announcement](https://spring.io/blog/2025/06/19/spring-boot-3-3-13-available-now/) | IOT-WO-02 Part C, due 2026-11-19 |
| Jackson 2.17.2 | 2.17.3 | 2024-11-01 | August 2025 (no exact day published), [upstream closed-branch register](https://github.com/FasterXML/jackson/wiki/Jackson-Releases) | IOT-WO-02 Part C, due 2026-11-19 |

The scan receipt lists findings by exact Maven artifact. Test-only and plugin
Jackson classpaths may move independently: they do not alter the identity
runtime's 2.17.2 libraries or their grandfathered records. Historical locations
inside those immutable legacy records are retained; fresh collector observations
report the actual current module locations and scopes.
