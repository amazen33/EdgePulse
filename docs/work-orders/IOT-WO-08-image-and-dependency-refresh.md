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

## Amendment (2026-10-30, architect): expedite for the Brotli KEV and the TB OpenJDK Critical

**Facts (Codex, nightly scan 41029265094, 2026-10-30).** There are 4 blockers, all first seen 2026-10-23, and none has an exception. They block every PR, including #55.

| Image | Package | Advisory | Why it blocks | Fixed package |
| --- | --- | --- | --- | --- |
| kind node | `libbrotli1` 1.1.0-2+b7 | CVE-2026-111497 | Critical, **KEV** | 1.1.0-2+deb13u1 |
| TB node | `libbrotli1` 1.1.0-2+b7 | CVE-2026-111497 | Critical, **KEV** | 1.1.0-2+deb13u1 |
| TB node | `openjdk-25-jdk-headless` 25.0.4.1 | CVE-2026-91403 | Critical with a fix (TB is the strict image class) | 25.0.5+8 |
| TB node | `openjdk-25-jre-headless` 25.0.4.1 | CVE-2026-91403 | Critical with a fix | 25.0.5+8 |

**What the rules allow.** ADR 0014 and ADR 0028 permit **no exception** for a KEV, the harness included.

**Ruling:**
1. **Expedite now under the KEV rule.** The 14-day cooling-off is waived for releases that fix these findings.
2. **Codex finds the newest upstream images that contain the fixed packages.** That means a kind node image for our Kubernetes line, and a ThingsBoard 4.3.1.x `tb-node` image.
   - Package availability in Debian alone does not prove a fixed image exists; check by scanning the candidate digest.
   - If a fixed image exists, open the refresh PR (pins, register, rescan) under the net-improvement rule.
3. **No self-rebuild.** TB is never forked, patched or rebuilt (existing rule). The kind node image is not rebuilt either.
4. **If no fixed image exists for one of them,** Codex stops and reports the candidates and their dates. The owner then chooses between:
   - **(a) Keep EdgePulse merges blocked** until upstream ships a fixed image.
   - **(b) Amend ADR 0014** to allow one time-boxed KEV exception **only for images that are not shipped or deployed** (harness and dev-only), with a reachability analysis, the same 14-day leash and checkpoint as Twinfra WO-40 Amendments 10a and 10b, and owner approval.

   Option (b) needs its own ADR amendment; this work order does not grant it.
5. **The profile's vulnerability-management status is now BLOCKED,** not CONDITIONAL PASS (profile updated).

## Amendment 2 (2026-10-30, architect): partial fix available; options for what remains

**Codex's result (stop rule applied correctly).**
- **kind v1.36.4** (2026-08-26) is still the newest node image on our line. It still carries `libbrotli1` 1.1.0-2+b7, the KEV.
- **TB 4.3.1.8** (image 2026-10-26) fixes `libbrotli1` (1.1.0-2+deb13u1), but OpenJDK 25.0.4.1 remains: CVE-2026-91403, Critical; the fix needs 25.0.5+8.
- The full TB scan failed on Windows because of a filename defect in the pinned Syft, so net improvement is not yet proven.

**Ruling and owner decisions:**
1. **E-1: promote TB 4.3.1.8** (recommended), because it removes the TB KEV.
   - Run the **full scan and net-improvement check in CI on Linux**, not on Windows.
   - The OpenJDK Critical gets **one individual Critical exception per package, 30 days at most**. ADR 0014 caps exceptions by severity and requires evidence. The record states:
     - the reason: no TB 4.3.1.x image with OpenJDK 25.0.5 exists yet;
     - reachability: TB is not deployed anywhere, because MS3 is not reached;
     - a replacement duty: promote the first TB patch with the fixed JDK under the expedite rule;
     - `approvedBy` empty until the owner approves.
   - TB is never forked or rebuilt.
2. **E-2: the kind node image KEV (harness).** ADR 0028 forbids a KEV in a harness image, and no fixed kind node image exists. Options:
   - **(a), recommended: pause the kind rehearsal.**
     - Remove the kind node image from the gated inputs, and disable or skip the kind rehearsal job, until kind publishes a node image with `libbrotli1` ≥ 1.1.0-2+deb13u1.
     - The weekly watch reports when one exists; restore it within 14 days of that.
     - **No exception is needed, and ADR 0028 stays intact.**
     - The cost: chart and `dev/kind` changes are not rehearsed in kind meanwhile. Static chart checks still run.
   - **(b): amend ADR 0028** to allow one 14-day KEV exception for harness-only images that have no secrets and no write permission.
3. **If the owner accepts E-1 and E-2(a), PR #55 and every other PR can pass again.** The only remaining exceptions are the two OpenJDK ones.

**Owner decisions (2026-10-30): E-1 ACCEPTED** (promote TB 4.3.1.8; one 30-day Critical exception per OpenJDK package, proposed with `approvedBy` empty for row approval in the PR). **E-2 option (a) ACCEPTED** (pause the kind rehearsal; no KEV exception; ADR 0014 and ADR 0028 unchanged).

**Ruling (2026-10-30, architect): option 1, separate proposals; no PR-preview mechanism.**
- The exceptions schema requires a non-empty `approvedBy`, so the two OpenJDK rows go into a **separate proposal file**, the same pattern as Twinfra R12.
- CI stays red until the owner approves the exact rows in the PR. Codex then activates them, setting `approvedBy` and changing nothing else, and CI turns green.
- **No new gate mechanism and no schema change:** building one for two rows is not worth the risk.
- **The TB digest's `supplyChain` qualification** comes from the full Linux CI scan of the new digest, recorded as the criterion's evidence.
- **If the licence ladder demands more for the changed TB record** (for example full enterprise-grade records for a changed legacy fingerprint), Codex stops and reports. No criterion is recorded without evidence.

## Amendment 3 (2026-10-30, architect): the TB digest change needs a full ADR-0054 record

**Codex's stop is right.**
- TB's record is `legacy-pending`. EdgePulse's ladder (`security/licence_ladder.py`) requires all six verified criteria for any changed digest.
- EdgePulse has **no** security-fix carry-forward rule; Twinfra's ADR-0054 Amendment 1 applies to Twinfra only.

**Ruling: E-3, a full evidence review for TB under the unchanged ladder** (recommended over porting the carry-forward rule, because it produces real assurance and changes no rule).
1. Codex completes the five missing criteria for ThingsBoard CE 4.3.1.8 from **primary HTTPS sources only**: maturity, governance, activity and support, security process, adoption. Supply chain comes from the full Linux CI scan.
   - Each criterion needs a `pass` result, an HTTPS evidence link and a date, exactly as the ladder requires.
   - A criterion that the evidence does not clearly meet is recorded as **not passing**, and Codex stops.
2. The architect reviews every criterion's evidence in the PR before activation; the owner approves with the PR. This is the two-party rule.
3. **Fallback, decision E-4, only if a criterion cannot be evidenced:** port the security-fix carry-forward rule (Twinfra ADR-0054 Amendment 1) into EdgePulse as an ADR amendment and ladder change. In phase 1 the architect will propose making carry-forward a shared SEC-01 rule, because a security fix must never be harder than keeping the vulnerable version.
4. The two OpenJDK rows stay as separate proposals with `approvedBy` empty (Amendment 2 ruling).

**Owner decision (2026-10-30): E-3 ACCEPTED** (full evidence review for TB 4.3.1.8 under the unchanged ladder; E-4 fallback only if a criterion cannot be evidenced).

## Review of PR #56 (2026-10-30, architect)

**PR:** amazen33/EdgePulse#56, commit `e919644` (owner commit, no attribution line).
- **Full Linux scan** (run 41054030008): six images, the Maven graph and lockfiles; 1,024 findings; **zero KEV**.
- **TB comparison** (run 41054030074): net improvement 327 → 269, with no new fixable Critical or High identities.
- **Exactly two blocking rows:** CVE-2026-91403 (Critical, non-KEV, first seen 2026-10-23) in `openjdk-25-jdk-headless` and `openjdk-25-jre-headless` 25.0.4.1+1-1~deb13u1. The fix is 25.0.5+8-1~deb13u1, which no published TB 4.3.1.x image contains yet.
- **Other checks:** the Maven tests (214 + 61), the supply-chain tests (105), naming, release checks and OpenShift renders all pass. The licence gate fails only because `supplyChain` is pending. `java-platform-bootstrap` fails because Python 3.12.12 is missing on the Ubuntu 26.04 runner: a fault already on main, fixed by PR #55 (whose only failure is the supply-chain gate this PR clears).
- **Evidence review (E-3):** maturity, governance, activitySupport, securityProcess and adoption cite primary ThingsBoard, GitHub and Docker Hub sources. The earlier third-party adoption link is gone. **Accepted.**

**Proposal review:** `security/vulnerability-exception-proposals/iot-wo-08-tb-openjdk-2026-10-30.json`, blob `a716edf`, SHA-256 `2a14597cadf94c4365f1dbad0f446aa251f556ee9bf941d06dd6e5d6f8c953c9`.
- Each Critical gets a separate row, expiring 2026-11-19 (within the 30-day cap from first-seen), with a checkpoint on 2026-11-12 and no extension in place.
- The compensating control is that TB runs nowhere: the kind rehearsal is paused and MS3 is not reached.
- The replacement duty is to promote the first upstream TB patch with the fixed JDK. TB is never forked or rebuilt.
- **Recommendation: approve both rows**, under the conditions in A-1.

**Owner decisions:**
- **A-1:** approve both CVE-2026-91403 rows exactly as in the file with the SHA-256 above, under three conditions:
  1. Starting TB anywhere (kind rehearsal, lab or deployment) before the fixed image voids both rows.
  2. They expire on 2026-11-19 and are not extended.
  3. The two OpenJDK Highs that reach the blocking threshold on 2026-11-05 are **not** covered.
- **A-2:** Codex prepares separate proposals for those two Highs by 2026-11-03 (same pattern, empty `approvedBy`, expiry no later than 2026-11-19), unless an upstream TB patch clears them first.
  - **Approved (owner, 2026-11-02):** "I approve both rows" for proposal `security/vulnerability-exception-proposals/iot-wo-08-tb-openjdk-high-2026-10-31.json`, SHA-256 `a2df007b98c9aed735c4cb55590e004df8d9f6f82cae67b6eb591b1091c366f1`, under the A-1 conditions. No upstream TB 4.3.1.x patch clears them; IOT-WO-09 is the replacement.
- **A-3 (zlib1g, 2026-11-10):** CVE-2026-85091 (High, not KEV) gained a Debian 13 fix between the 2026-11-07 and 2026-11-09 nightlies and, first seen 2026-10-20, blocked at once on TB 4.3.1.8 and CNPG PostgreSQL 18.6. Proposal `security/vulnerability-exception-proposals/iot-wo-08-zlib-high-2026-11-10.json`: the tb-node row expires 2026-11-19 with A-1 and A-2; the CNPG row expires 2026-11-30, when IOT-WO-08 refreshes to the first qualifying CNPG digest with the fix. Deploying either image voids its row; a KEV listing voids both. Evidence: `security/evidence/vulnerability-exceptions/zlib-high-2026-11-10.md`.
  - **Approved (owner, 2026-11-11):** "I approve both rows" for SHA-256 `dfa73ed9ab5c5badf96462a446abbe87d90406c3d8c7b0a567ed9ff9c68f0fdb`.
- **A-4 (apt and zlib1g, 2026-11-12):** two non-KEV Highs not yet covered: CVE-2026-109518 (apt 3.0.3, fixed in 3.0.4, first seen 2026-11-05, blocks from 2026-11-19) and CVE-2026-76844 (zlib1g, fixed in the same deb13u1 as A-3, first seen 2026-11-06, blocks from 2026-11-20). Proposal `security/vulnerability-exception-proposals/iot-wo-08-apt-zlib-high-2026-11-12.json`, SHA-256 `e077a59c2c7c6b7c473e87071dcb0937ef16913b1ad89f45684e7b53f876e68f`: three tb-node apt rows expire 2026-11-19 with A-1 to A-3; three CNPG PostgreSQL rows expire 2026-11-30 with the A-3 PostgreSQL row. CVE-2026-76844 on tb-node starts blocking after every tb-node row has expired, so it belongs to the 2026-11-20 TB decision. Same voiding conditions as A-3. Evidence: `security/evidence/vulnerability-exceptions/apt-zlib-high-2026-11-12.md`.
  - **Approved (owner, 2026-11-12):** "I approve all six rows" for SHA-256 `e077a59c2c7c6b7c473e87071dcb0937ef16913b1ad89f45684e7b53f876e68f`.
- **Retired TB 4.3.1.6 rows (2026-11-12):** PR #56 replaced the digest but left its 19 High rows, which match no scanned input. The gate validates every row's lifetime before matching, so any row left after 2026-11-19 fails every scan from 2026-11-20 UTC. Under item 1 they leave removal-only (32 to 13 rows with A-4); `security/evidence/iot-wo-08/retired-tb-4.3.1.6-exceptions-2026-11-12.json` keeps each row and its block hash. The eight TB 4.3.1.8 rows (A-1 to A-4) still expire 2026-11-19.
- **A-5 (TB renewal, 2026-11-23):** the eight TB 4.3.1.8 rows (A-1 to A-4) expired on 2026-11-19, and since 2026-11-20 every scan stops at exception validation. Owner decision (2026-11-23): renew through new entries with fresh evidence (item 4) and remove the expired rows removal-only (`security/evidence/iot-wo-08/expired-tb-4.3.1.8-exceptions-2026-11-23.json`). The 2026-11-23 scan (PR #70, run 45132416685) blocks on 14 TB findings, with 10 more OpenJDK Highs due on 2026-12-02; the owner chose to cover all 24 in one proposal. Proposal `security/vulnerability-exception-proposals/iot-wo-08-tb-renewal-2026-11-23.json`, SHA-256 `c2b4e2416037e6c74c1d008cdc8c0eeaea5dcf8a758034c6701239eddfd8047f`: 4 Critical rows (CVE-2026-91403, CVE-2026-114820, one per package) and 20 High rows (OpenJDK, zlib1g, apt, glibc), all expiring 2026-12-23. Conditions: starting TB voids them; no extension; the owner issues the TB runtime-image work order (IOT-WO-09) and its ADR before 2026-12-23, since neither exists in the repository yet; a KEV listing voids that advisory's rows. Evidence: `security/evidence/vulnerability-exceptions/tb-renewal-2026-11-23.md`. An 8-row draft (`67a3fea5…`), written from the 2026-11-19 scan, was withdrawn before approval.
  - **Approved (owner, 2026-11-23):** "I approve A-5 and A-6" for SHA-256 `c2b4e2416037e6c74c1d008cdc8c0eeaea5dcf8a758034c6701239eddfd8047f`, as a temporary bridge with TB unstarted. Delivery deadline: issue IOT-WO-09 and its ADR in the week of 2026-11-23, with a replacement-validation target before 2026-12-23.
- **A-6 (PostgreSQL bridge, 2026-11-23):** the same scan blocks CNPG PostgreSQL 18.6 on glibc (CVE-2026-19499, CVE-2026-5435), with six krb5 Highs due on 2026-11-24/25. Owner decision (2026-11-23): bridge to 2026-12-14 while a fixed CNPG build clears cool-off. Proposal `security/vulnerability-exception-proposals/iot-wo-08-pg-bridge-2026-11-23.json`, SHA-256 `f2e811603798d360d274fda1c7850b7b8c80af36914fbfd006a634661acd7a99`: 35 High rows (8 glibc, 24 krb5, plus apt and zlib1g renewing A-3/A-4), all expiring 2026-12-14. Activation removes the four A-3/A-4 PostgreSQL rows, which the new rows supersede (the gate rejects duplicate keys). Deploying the image voids them; the CNPG refresh removes each row its scan clears. Evidence: `security/evidence/vulnerability-exceptions/pg-bridge-2026-11-23.md`.
  - **Approved (owner, 2026-11-23):** "I approve A-5 and A-6" for SHA-256 `f2e811603798d360d274fda1c7850b7b8c80af36914fbfd006a634661acd7a99`, as a temporary bridge with the image undeployed. Owner checkpoint 2026-12-07 for the fully fixed PostgreSQL route. No eligible CNPG build has the glibc or krb5 fixes yet; a partial refresh to `18.7-202611122305` (apt, zlib1g and PostgreSQL 18.7; eligible 2026-11-27) is possible first. PostgreSQL server CVEs are not seen by the pinned scanners; that coverage defect is under separate investigation.
- **PostgreSQL 18.7 partial refresh and A-7 (2026-11-23, owner decision):** no eligible CNPG build carries glibc 2.41-12+deb13u5 or krb5 1.21.3-5+deb13u2, so the pin moves to `18.7-202611122305-minimal-trixie` (`sha256:b98ae0b7…`, cool-off ends 2026-11-26T23:16:17Z). PR #72's scan (run 45137906762) clears apt and zlib1g and shows no new fixable High/Critical or KEV. The 35 A-6 rows for the old digest leave removal-only (`security/evidence/iot-wo-08/retired-pg-18.6-a6-rows-2026-11-23.json`). Proposal A-7 (`security/vulnerability-exception-proposals/iot-wo-08-pg-18.7-bridge-2026-11-23.json`, SHA-256 `1948cb7a33e2584c35f9d51a5e8cc38fa4b05885a85ea33580295e86a88b2af4`) covers the 32 glibc and krb5 Highs on the new digest until 2026-12-14, with the A-6 conditions; it is not active. The record's `supplyChain` criterion passes on the green rerun after activation (run 45668871265, 2026-11-25: zero blockers; all 32 fixable Highs matched by A-7). Evidence: `security/evidence/iot-wo-08/cnpg-postgresql-18.7-202611122305-qualification-2026-11-23.md` and `security/evidence/vulnerability-exceptions/pg-18-7-bridge-2026-11-23.md`.
  - **Approved (owner, 2026-11-25):** "Approve A-7" for SHA-256 `1948cb7a33e2584c35f9d51a5e8cc38fa4b05885a85ea33580295e86a88b2af4`. The 32 copies are active and expire 2026-12-14; deploying the image voids them.
- **A-8 (TB bundled Tomcat, 2026-11-27):** `main`'s gate on `622c51c` (run 45835115418, 2026-11-26) blocks on two new fixable Criticals in TB 4.3.1.8's bundled `tomcat-embed-core` 10.1.61 (CVE-2026-116561, CVE-2026-118028; fix 10.1.62); six Highs from the same batch block from 2026-12-10. Tomcat ships inside TB's Java archives, so only an upstream TB release can fix it; the IOT-WO-09 runtime image cannot. Owner decision (2026-11-27): bridge with A-8 and scan TB 4.3.1.9 (published 2026-11-24, cool-off ends 2026-12-08). Proposal `security/vulnerability-exception-proposals/iot-wo-08-tb-tomcat-2026-11-27.json`, SHA-256 `4f270c191a57493eb57fbd839344f6cba8fed6cfcf0710f85ba74cf080b89d2f`: 8 rows (2 Critical, 6 High), expiring 2026-12-23 with A-5. Same voiding conditions as A-5. Evidence: `security/evidence/vulnerability-exceptions/tb-tomcat-2026-11-27.md`.
  - **Approved (owner, 2026-11-27):** "Approve A-8" for SHA-256 `4f270c191a57493eb57fbd839344f6cba8fed6cfcf0710f85ba74cf080b89d2f`. The eight copies are active and expire 2026-12-23; starting TB voids them.

**Merge order after A-1:**
1. Codex sets `approvedBy` on the two rows (nothing else changes) and reruns CI.
2. Codex records `supplyChain` as `pass`, citing the green rerun.
3. The architect does a final diff review.
4. The owner merges PR #56 (`java-platform-bootstrap` red is the known main fault).
5. Codex updates PR #55 from main.
6. The owner merges PR #55 once green.

## Cilium staleness (2026-11-16, architect)

**Facts (nightly scan 43700701694, 2026-11-15, `a12e046`).** 1,227 findings, none blocked, 7 excepted. The run failed only on the ADR 0028 staleness rule: Cilium v1.20.3 (published 2026-10-15T15:26:34Z) passed 30 days unadopted on `quay.io/cilium/cilium`, `quay.io/cilium/cilium-envoy` and `quay.io/cilium/operator-generic`, which stay on 1.20.2. The check runs live on every gate run, so every PR's supply-chain gate fails from the same date. Cilium v1.20.4 (2026-10-23T14:51:39Z) blocks from 2026-11-23 UTC.

**Owner decision (2026-11-16):** record a dated owner reason for v1.20.3 on the three images, rather than adopting 1.20.4 before the 2026-11-19 exception cutoff. Reason: the harness copies Twinfra's read-only Cilium 1.20.2 lock (`module-2/artifacts.lock.json` at Twinfra `5801b8e`, same chart SHA-256), and the kind rehearsal is paused, so Cilium runs nowhere. KEV still blocks. Record: `security/evidence/iot-wo-08/cilium-1.20.3-owner-reason-2026-11-16.json`.

**Owner decision (2026-11-23):** v1.20.4 went stale on 2026-11-23 UTC; add the same dated reason for v1.20.4 on the three images rather than adopting it, and confirm the v1.20.3 wording. Twinfra's lock is unchanged (`cceab35`, byte-identical lock file). Record: `security/evidence/iot-wo-08/cilium-1.20.4-owner-reason-2026-11-23.json`.

**Still open, due before 2026-12-18 UTC:** Cilium v1.20.5 (published 2026-11-17T09:53:42Z) becomes eligible on 2026-12-01 and stale on 2026-12-18. Adopt it (pins, chart, three digests, licence admissions and the Envoy scan, moving the harness off Twinfra's lock) or record a separate dated reason for it. The CNPG operator has the same dates: 1.30.2 (published 2026-11-17T11:31:47Z) becomes eligible on 2026-12-01 and stale on 2026-12-18 UTC.

## Amendment 5 (architect, proposed 2026-11-01): retire the os-maven-plugin build extension

**Status:** Approved (owner, 2026-11-23), for PR #61.

**Facts.**
- `maven:executed-plugin-9` is the `kr.motd.maven:os-maven-plugin` 1.7.1 build extension in `services/identity/pom.xml`. Its last release was 2022-11-07, and no newer version exists to adopt under item 1.
- Its classpath carries `plexus-utils` 3.1.0 (CVE-2025-67030, High; fixed in 3.6.1 and 4.0.3; first seen 2026-10-20) and `commons-lang3` 3.5 (CVE-2025-48924, Medium, report-only).
- One approved IOT-WO-08 exception covered the High until 2026-11-19. It has expired, and while it stays in the register every gate run stops at exception validation.
- The extension only computes `os.detected.classifier` for the protoc and protoc-gen-grpc-java artifacts.

**Ruling.**
1. Replace the extension with two OS-activated profiles that set `os.detected.classifier`: `linux-x86_64` (Linux, amd64) and `windows-x86_64` (Windows, amd64). These are the classifiers `security/collect_maven.py` already inventories as code generators. Add no plugin, extension or dependency. Any other platform needs its profile and its collector classifier added together, in one reviewed change.
2. Retire the 12 `build-tool` register records found only on that classpath, removal-only, with their exact bytes kept in `security/evidence/iot-wo-08/os-maven-plugin-removal-2026-11-01.json`. No record is added or changed. The legacy set and baseline are unchanged.
3. Under item 1, remove the cleared exception (CVE-2025-67030, `maven:executed-plugin-9`). The exception regression test may allow exactly that row's removal. Every other row keeps its bytes and order.
4. Leave unchanged: the ported checker, ladder, schemas, licence classes, gate logic and other exceptions.

**Acceptance.** Green `java-platform-bootstrap`, `naming-gate` and `supply-chain-gate`. The executed-plugin inventory no longer contains os-maven-plugin or plexus-utils 3.1.0. `licence-gate` is green, or fails only on unrelated, pre-existing items. Until the other 27 expired rows leave `main` (PR #66 and the TB A-5 renewal), `supply-chain-gate` stops at exception validation; the stacked A-5 recovery branch runs this change together with them.
