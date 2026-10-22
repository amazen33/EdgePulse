# IOT-WO-08: Image and dependency refresh (clears the Part B exceptions)

**Status:** Approved for implementation when the owner approves PR #48's exception list, which references this work order. **Due: 2026-11-19**: every exception that names it expires then (ADR-0049's 30-day Critical limit).
**Author:** Claude · **Implementer:** Codex, as the Enterprise Senior cloud engineer · **Branch:** `codex/iot-wo-08-refresh`
**Decision:** ADR 0014 / Twinfra ADR-0049, and IOT-WO-02 Amendment 5.

## Scope

Clear every exception in `security/vulnerability-exceptions.json` whose `workOrder` is `IOT-WO-08`: 287 entries at PR #48, mostly in the kind node, the three Cilium images, the CNPG operator, the TB image, and one executed Maven plugin.

1. **Weekly refresh check, each Monday until done.** For every affected image and package, check for a newer release at least 14 days old: kind, and its node image matching Kubernetes 1.36; Cilium at Twinfra's locked line; CNPG; TB 4.3.1.x; the Maven plugin.
   - Adopt each one as soon as it qualifies, in a small PR that rescans, removes the exceptions it clears, and updates the pins, the register (with the re-fingerprint rule, or full records where a component changes) and the evidence.
2. **The TB image:** EdgePulse never forks or rebuilds TB (ADR 0020). If no 4.3.1.x patch clears its entries by **2026-11-12**, report the remaining TB findings with reachability notes. The owner then decides: a newer TB line, or new evidenced exceptions (each Critical needs its own entry and fresh approval).
3. **The kind node and Cilium (local and CI test harness only, never deployed by EdgePulse):** if upstream hasn't published fixed releases by **2026-11-12**, report it. The owner decides between new evidenced exceptions and an ADR on how ADR-0049 applies to test-harness-only images. Don't build custom node images without a decision.
4. Exceptions are never extended in place. A renewal is a new, owner-approved entry with fresh evidence.

## Acceptance

- No `IOT-WO-08` exception remains, or each remaining one is replaced by an owner-approved entry under item 2 or 3, before 2026-11-19.
- CI is green: `java-platform-bootstrap`, `naming-gate`, `release-checks`, `licence-gate` and `supply-chain-gate`.
- Each PR lists the exceptions it removed, and the before and after counts.

## Owner checkpoints

- **2026-11-12:** a status report on what remains, with the decisions under items 2 and 3.
- **Before 2026-11-19:** approve any renewal entries.

### Ruling (architect, 2026-10-21): JSpecify in the gRPC refresh

gRPC 1.84.0 brings `org.jspecify:jspecify` (stable 1.0.1, or prerelease 0.3.0 by default) as a runtime dependency. Its published disclosure policy can't be verified, so a true ADR-0054 `securityProcess` pass isn't possible. JSpecify holds nullness annotations only, and the JVM ignores annotation types that are missing at runtime.
- **Exclude it** from the runtime graph on the gRPC dependency that brings it in. Proof: the identity tests, including transport equivalence, pass; it is absent from the resolved runtime tree; and there is no runtime licence entry.
- **Known follow-up for Part C:** Spring Framework 7 (the Spring Boot 4 line) depends on JSpecify directly. The Part C trial must report whether it can be excluded there too, or whether the owner needs to decide how ADR-0054's `securityProcess` applies to code-free annotation artifacts.

### Ruling (architect, 2026-10-21): annotation-only artifacts introduced by a refresh

This generalises the JSpecify ruling. When a refresh introduces a new runtime-reachable artifact that contains **only annotation types**, exclude it from the runtime graph instead of qualifying it. Examples: `org.codehaus.mojo:animal-sniffer-annotations`, JSpecify, and similar annotation JARs.
1. **Proof the artifact is annotation-only:** a check reads every `.class` entry in the exact JAR and confirms that each one has the `ACC_ANNOTATION` flag (or is `package-info` or `module-info`). The JAR contains nothing executable, and has no service-loader files or other resources besides licence, notice and manifest. Record the check's output in the PR.
2. **Runtime proof:** all tests pass, including transport equivalence; the artifact is absent from the resolved runtime tree and the classpath; and there is no runtime register entry.
3. **The rule covers only artifacts the refresh introduces.** Annotation artifacts already in the legacy set stay as they are. Any artifact that fails check 1 needs a full ADR-0054 record or a stop.
4. **Planted tests:**
   - excluding an artifact that contains a non-annotation class is rejected by the check;
   - an annotation-only artifact left at runtime scope still needs a record.

**Clarification (architect, 2026-10-21) to item 1:** the permitted resources also include the Maven-generated build metadata `META-INF/maven/<groupId>/<artifactId>/pom.xml` and `pom.properties`, only for the artifact's own coordinates. All other rules stay strict: `META-INF/services/*`, other resources, and any non-annotation class (an enum or an ordinary class) make the artifact ineligible.

**Error Prone annotations** (`com.google.errorprone:error_prone_annotations`; 2.50.0 contains the enum `Modifier`) isn't eligible for exclusion. In order:
- (a) If the legacy set already admits an `error_prone_annotations` version, pin that version through `dependencyManagement`, so its fingerprint doesn't change, and prove that all tests pass.
- (b) Otherwise, write a full ADR-0054 record for the new version, but only if every criterion can truthfully pass, with evidence (Google-hosted project, with its disclosure policy).
- (c) Otherwise, stop and report.

## Amendment 1 (architect, 2026-10-21): test-harness images (ADR 0028)

**Status:** Approved (owner, 2026-10-21), with ADR `XXXX-proposed-test-harness-images.md`, which the owner accepted on 2026-10-21 and which lands as 0028.

1. **One PR** (`codex/iot-wo-08-harness-class`):
   - add ADR 0028 to `docs/adr/` word for word, except the title's number and "(proposed)", and update `docs/adr/README.md` (next free number 0029);
   - implement the `test-harness` class in EdgePulse's wiring only (`tools/ci/edgepulse_supply_chain.py` or similar), marked with ADR 0028. The ported supply-chain tools and schemas stay byte-identical.
2. **Mechanical checks (ADR 0028 Decision 1):**
   - references only from `dev/kind/**`;
   - none from `charts/**` or any packaging or deploy input;
   - every workflow job that runs these images has `contents: read` and no secrets.
3. **Gate behaviour (Decision 2):**
   - KEV blocks;
   - fixed Critical and High findings are report-only (in the nightly issue and the PR summary);
   - the staleness rule: a newer eligible release unadopted for more than 30 days fails the gate.
4. **Remove** the 266 `IOT-WO-08` exceptions for the five harness images: `kindest/node`, the three Cilium images and the CNPG operator. List them in the PR. Every other exception stays unchanged.
5. **Planted tests:**
   - a harness image referenced from `charts/` fails;
   - a harness job given a secret, or `contents: write`, fails;
   - a KEV in a harness image fails;
   - a stale harness image fails;
   - a fixed High in a harness image is report-only and passes.
6. **What remains under strict ADR-0049:** TB (19 entries, with the 2026-11-12 checkpoint), the executed Maven plugin, and the IOT-WO-02 Part C entries.
