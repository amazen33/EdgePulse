# Pin review, 2026-10-20

IOT-WO-02 Amendment 5; static public-artifact review. No cluster, application,
model or environment was run. The age cutoff is 2026-10-06 UTC.

| Input | Decision | Primary publication evidence |
| --- | --- | --- |
| kind node, Kubernetes 1.36 minor | Retain `v1.36.4`, digest `099e049362a1526b2db71494e1947aae99bd16290d7c895f2b7ea312e3cbfaed`; newest published node in that minor | [Docker Hub tag API](https://hub.docker.com/v2/repositories/kindest/node/tags?page_size=100&name=v1.36&ordering=last_updated), published 2026-08-26; [kind 0.33.0](https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0) |
| Cilium agent | Retain 1.20.2 and its published digest | [1.20.2 release](https://github.com/cilium/cilium/releases/tag/v1.20.2), 2026-09-16. [1.20.3](https://github.com/cilium/cilium/releases/tag/v1.20.3), 2026-10-15, is only five days old |
| Cilium operator | Retain the matching 1.20.2 operator-generic digest | Same release publishes digest `64d8798350e8569b8e7622563fed6e44dce2625f311e4651b774816516c744fc` |
| Cilium Envoy | Retain the proxy digest selected by the newest eligible Cilium release, 1.20.2 | [Version-matched Helm values](https://github.com/cilium/cilium/blob/v1.20.2/install/kubernetes/cilium/values.yaml); proxy build `v1.37.6-1789133542-cbec91f666af0bf742da986d43832932dbb26b82`. No independently incompatible proxy is substituted |
| CNPG operator | Retain 1.30.1 and its release manifest/image digest | [Latest release](https://github.com/cloudnative-pg/cloudnative-pg/releases/tag/v1.30.1), 2026-09-23; no later stable release in the checked release list |
| ThingsBoard | Retain 4.3.1.6 and its existing immutable image | [Official releases](https://github.com/thingsboard/thingsboard/releases), 4.3.1.6 published 2026-09-29. No newer 4.3.1.x patch exists. 4.4 is outside the approved patch line; no source is forked or rebuilt |
| PostgreSQL | Replace system flavour with `18.6-202610050823-minimal-trixie`, digest `37ade18dbdddba430858c72725aceeec66f33fa5333e82ea1df4942f6c1c83a3` | [Official dated image tags](https://github.com/cloudnative-pg/postgres-containers/pkgs/container/postgresql); image revision `ff34de135f29e04a841247ea9686d7a80b663005`, OCI creation 2026-10-05T08:23:19Z. October 12 and 19 builds are too young |

The PostgreSQL comparison uses the same scanner versions and October 20
database: 420 → 311 total findings; 5 → 1 Critical; 111 → 86 High.
Critical/High falls from 116 to 87 (29 fewer, 25%). All remaining 87 have no
available fix; none receives an exception. This quantifies this dated image
and flavour change together, not a claim of identical-build flavour isolation.

All seven current image digests and their reviewed SBOM hashes are in
[image-backfills-2026-10-20.json](image-backfills-2026-10-20.json).
All newly resolved Maven components, exact versions, publication dates,
licence elections and classes are in
[remediation-publications-2026-10-20.json](remediation-publications-2026-10-20.json).
Tomcat 10.1.60 is aged; the owner's KEV cooling-off waiver is not needed.

The build upgrades Compiler 3.16.0, Surefire 3.6.0, Enforcer 3.6.3, Jar 3.5.1,
Resources 3.5.0, Help 3.5.2 and CycloneDX 2.9.3. Explicit plugin-realm patches
include BeanUtils 1.11.0, jsoup 1.23.2, Plexus Utils 3.6.2/4.1.0, Maven
core/compat 3.9.11 and CycloneDX core 11.0.1 with Jackson 2.18.11.
Every standalone BOM wrapper uses that same patched collector realm.
The resolved graph, not an assumed plugin POM, determines the register.

Test-only updates are AssertJ 3.27.7, JSON-smart 2.5.2, Logback 1.5.38 and
contract-tests' Jackson 2.18.11. Logback stays at test scope and is absent
from the thin identity artifact. No logging-backend change is made here.
Identity's Spring Boot, Spring Framework, Jackson and gRPC versions stay
unchanged. No public patch in another minor is smuggled into its runtime.
