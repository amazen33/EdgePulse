# IOT-WO-02: Licence gate, supply-chain gate and runtime baseline

**Status:** Approved for implementation (follows ADR 0014 and 0021). Start after IOT-WO-01 merges. In Codex's queue it comes after Twinfra WO-34, unless the owner says otherwise.
**Author:** Claude · **Implementer:** Codex · **Repository:** IOT-EE · **Branches:** `codex/iot-wo-02-<part>`, one PR per part.

## Part A: licence gate (ADR 0021 Decision 3)

1. Port Twinfra's licence checker and register schema from `E:\vCloud` into `security/`.
   - Copy them with attribution, and keep the same classes, SPDX evaluation, baseline and ratchet (Twinfra ADR-0030, ADR-0042 and ADR-0044).
   - Do not modify Twinfra.
2. Register every Maven dependency, at compile, runtime and test scope, from a CycloneDX SBOM. Use the CycloneDX Maven plugin (Apache-2.0), registered too. Also register every build and CI tool.
3. CI fails on unregistered or blocked components. Findings that can't be closed go into `security/licence-baseline.json` under the 90-day rule.

## Part B: supply-chain gate (ADR 0014)

1. Pin Grype, Syft and OSV-Scanner at the versions Twinfra pins.
   - OSV-Scanner scans the Maven SBOM and lockfiles.
   - Grype and Syft run against images. The first image appears with IOT-WO-04; until then the job is wired in and passes on "no images".
2. Add a nightly workflow that opens or updates **one** issue in place, and implement Twinfra's exception rules: 30, 60 and 90 days, evidence required, KEV blocks.

## Part C: runtime baseline (ADR 0021 Decision 5)

1. Move to Java 21 LTS: `maven.compiler.release` 21, CI JDK 21 (Temurin, pinned).
2. Move Spring Boot and Spring Cloud to the newest release train that is in open-source support and whose newest patch is at least 14 days old.
   - Cite the support calendar you checked in the PR.
   - **If this needs a major-version jump (Spring Boot 4 or Jakarta changes), stop and report** with the list of breakages before changing code.
3. Keep every ArchUnit rule and planted-violation test green. Change no behaviour.

## Part D: quality gate

1. Add formatting, static analysis and coverage to `mvn verify`.
   - Candidates: Spotless with google-java-format (Apache-2.0) and Error Prone (Apache-2.0).
   - Coverage: JaCoCo is EPL-2.0. Check it against Twinfra ADR-0042 (build-time tools). If it isn't permitted, report alternatives; don't add it.
2. Set the coverage threshold at the current level, so the ratchet starts from today. Add one planted-violation test per tool.

## Acceptance

- CI is green, with the licence gate, the supply-chain gate and the quality gate all blocking.
- `mvn verify` passes on Java 21.
- The PR lists every registered component with its licence class.

## Amendment 1 (2026-10-19): start now, plus implementation rulings

**Status:** Approved (owner, 2026-10-19). Item 1: "I lift the 'after Twinfra WO-34' queue order". Items 2 to 7: approved as written.

1. **Queue order lifted.** Start now. The WO-34 ordering was queue priority, not a technical dependency, and nothing here touches Twinfra.
2. **Read Twinfra, never change it.** Read the licence checker, register schema, policy, exception rules and tool pins from Twinfra's **`origin/main`** with `git -C E:/vCloud show origin/main:<path>`, after a `git -C E:/vCloud fetch`.
   - Never check out, switch, stash or edit anything in `E:\vCloud`: its working tree belongs to another task (on 2026-10-19 it was on `codex/wo-32-actionlint-syft`).
   - Record the Twinfra commit you ported from in the attribution header.
3. **Part order and PRs.** Do the parts in the order **A, B, D, C**, one PR per part on `codex/iot-wo-02-<part>`, each branched from `main` after the previous part has merged.
   - C goes last, because its Spring step may stop for an owner decision (item 6). Java 21 should not wait behind that.
   - After each PR, report and wait.
4. **Imports into the register (Part A):**
   - every entry in `contracts/migration/v1/TOOLS.md`;
   - `dev/kind/pins.json`, including the kind node, Cilium, CNPG, TB and PostgreSQL images and the Helm, kubectl and kind binaries;
   - every GitHub Action, by SHA.
   - **JUnit, JaCoCo and any EPL-2.0 component** is classified under Twinfra's policy class for test or build-time tools (`build-tool`) only if ADR-0042 and ADR-0054 permit it. Otherwise list it as a finding with alternatives, and don't change the test framework in this order.
   - Add the publication dates missing from `pins.json` (Cilium, CNPG, Helm, kubectl, PostgreSQL); this was a PR #44 review nit.
5. **Naming-gate follow-ups (from the PR #39 review), in Part D:**
   - strip the exact phrase "formerly IOT-EE" before matching, instead of exempting its whole line;
   - stop exempting `CHANGELOG.md` and `RELEASING.md` as whole files, and check every line added after this change, keeping existing history lines exempt by exact content.
   - Extend the self-tests to match.
6. **Spring (Part C).** The Spring Boot 3.x line in use (3.3.4) is likely past open-source support, so the newest supported train is probably Spring Boot 4.x. That is the work order's **stop condition**.
   - Make the Java 21 change first: `maven.compiler.release` 21 and Temurin 21 pinned in CI, with no Spring change. Open its PR.
   - Then, on a separate branch, try the Spring upgrade **without merging it**, and report the full breakage list and the support calendar you checked. The owner decides the next step.
7. **Formatting (Part D).** If google-java-format reformats existing files, put that in its own commit, "style: apply google-java-format (no behaviour change)", separate from the tooling commit, so review can treat it as mechanical. Tests and counts must be unchanged.

## Amendment 2 (architect, 2026-10-19): EPL build tools and the Maven ecosystem

**Status:** Approved (owner, 2026-10-19), together with the ADR `XXXX-proposed-build-tool-licences-and-maven-ecosystem.md`, which the owner accepted on 2026-10-19. It lands as `docs/adr/0024-build-tool-licences-and-maven-ecosystem.md`.
**Why:** Codex stopped Part A correctly on 2026-10-19, at Twinfra `0d95007`. ADR-0042's `build-tool` class omits EPL-2.0 (JUnit, JaCoCo), and Twinfra's register and checker have no `maven` ecosystem.

1. **Part A adds that ADR to `docs/adr/`** as `0024-build-tool-licences-and-maven-ecosystem.md` (accepted, next free number), word for word except the title's number, and updates `docs/adr/README.md` (next free number 0025). If 0024 is taken by then, use the next free number and say so.
2. **Port, then extend.** First a commit that ports Twinfra's checker, schema and policy unchanged, with attribution and the source commit. Then a separate commit with the two EdgePulse extensions, each marked with that ADR:
   - EPL-2.0 in the `build-tool` allow-list;
   - the `maven` ecosystem: a collector from the CycloneDX SBOM plus `mvn dependency:tree`, and the build-tool test (test scope or build plugin, not reachable from compile or runtime, not packaged).
3. **Planted-violation tests for the extensions:**
   - an EPL-2.0 dependency at `compile` scope fails;
   - the same at `test` scope passes as `build-tool`;
   - an unregistered Maven dependency fails;
   - a test-scope dependency that becomes reachable at runtime fails.
4. **No change to Twinfra, and no framework or coverage swap.** JUnit stays, and JaCoCo is allowed for Part D.

## Amendment 3 (architect, 2026-10-20): test-only modules and the Jakarta annotation exception

**Status:** Approved (owner, 2026-10-20), together with the ADR `XXXX-proposed-test-only-modules-and-jakarta-annotation-exception.md`, which the owner accepted on 2026-10-20. It lands as `docs/adr/0025-test-only-modules-and-jakarta-annotation-exception.md`.
**Why:** Part A stopped on 2026-10-20 with JUnit (EPL-2.0) at compile scope in the test-only `architecture` module, and `jakarta.annotation-api` (EPL-2.0 OR GPL-2.0 WITH Classpath-exception) shipped through Spring Boot.

1. **Continue on the existing branch.** Keep commit `eec61fa` (the unchanged port) on `codex/iot-wo-02-a`, and add the ADR 0024 and ADR 0025 extensions as the second commit.
2. **ADR 0025 in Part A.** Add it as `docs/adr/0025-…` after 0024. The index's next free number becomes 0026.
3. **Test-only modules.**
   - The register lists `architecture` and `contract-tests` as test-only.
   - The gate checks that each listed module has its Enforcer test-scope rule and that no module depends on it outside test scope.
   - Planted-violation test: a module that depends on `architecture` at compile scope fails.
4. **Jakarta exception.**
   - Register `jakarta.annotation:jakarta.annotation-api` as a named runtime exception: EPL-2.0 elected, unmodified, the upstream source URL for the exact version, and ADR 0025.
   - Planted-violation test: a different EPL-2.0 artifact at compile scope in identity still fails.
5. **Everything else stays as Amendment 2 says.** If another blocked component appears, stop and report.

## Amendment 4 (architect, 2026-10-20): build-tool licence families

**Status:** Approved (owner, 2026-10-20), together with the ADR `XXXX-proposed-build-tool-licence-families.md`, which the owner accepted on 2026-10-20. It lands as `docs/adr/0026-build-tool-licence-families.md`.
**Why:** Part A stopped a third time, on eight Maven plugin dependencies: EPL-1.0 (Aether, Sisu), and CDDL OR GPL-2.0 WITH Classpath-exception (`javax.annotation-api` 1.2, `javax.servlet-api` 3.1.0). Naming licences one by one keeps stopping the work.

1. **Add ADR 0026** after 0024 and 0025. The index's next free number becomes 0027.
2. **Implement the family rule** (ADR 0026 Decision 1) for `build-tool` only, with `OR` expressions resolved to a recorded elected option.
3. **New stop rule for this work order:** stop only for a licence in ADR 0026 Decision 2 (blocked, proprietary, account-gated, none or unknown), or for a **shipped** component outside the permitted list and the named exceptions. Register everything else under the families, and continue.
4. **Planted-violation tests,** added to Amendment 3's:
   - an EPL-1.0 plugin dependency passes as `build-tool`;
   - the same EPL-1.0 artifact reachable from a shipped classpath fails;
   - an AGPL build plugin fails;
   - a component with no licence fails.

### Ruling (architect, 2026-10-20): enterprise-grade records for existing runtime dependencies (ADR-0054)

This uses the ported checker's own `legacy-pending` mechanism. No checker change.

1. **Part A registers today's shipped (runtime) dependencies** with `enterpriseGrade: {"status": "legacy-pending", "due": "2027-04-20"}`, and lists each in `security/licence-policy.json` under `ladder.legacy` with its fingerprint, tier and the same due date. That is six months, the same backfill length Twinfra used. Build-tool and test-only entries need no enterprise-grade record.
2. **Owner approval:** the PR description lists the full legacy set (coordinates, version, tier, due date). The owner's approval of the Part A PR is the approval of that list, and the PR description records it. The due date can't be extended later.
3. **Parts B and C produce the evidence:**
   - Part B's supply-chain gate provides the `supplyChain` criterion;
   - Part C's upgraded or new runtime components need **full** ADR-0054 records (all criteria `verified`), because a changed component leaves the legacy list automatically.
   - No new runtime component may use `legacy-pending`.
4. **Watch item:** by the due date, `jakarta.annotation-api` (tier 3, ADR 0025) needs a full tier-3 record: owner approval (ADR 0025), a climbing record, `unmodified` and a notice. If the schema's tier-3 `separateUnit` requirement can't truthfully be met for a linked API JAR, report it in the Part A PR, so a follow-up ADR lands before the due date. Don't record a false value.
5. **Planted-violation tests:**
   - a legacy entry with a changed fingerprint fails;
   - a legacy entry with an extended due date fails;
   - a new runtime dependency with `legacy-pending` fails.

### Ruling (architect, 2026-10-20): known permissive forms in the build-tool class

This clarifies ADR 0026 Decision 1; no new decision. A `build-tool` component may carry any **known permissive** licence. That is one less restrictive than the families ADR 0026 already allows (for example Apache-1.1, BSD-style licences without an SPDX ID, and explicit public-domain dedications), under these conditions:
1. **Exact source evidence:** the licence or dedication text from that exact artifact version (in the JAR, the POM or the tagged source), with a link and the date read.
2. **A recorded identifier:** the SPDX ID where one exists (`Apache-1.1`). Otherwise a `LicenseRef-<name>` ID (for example `LicenseRef-dom4j-1.1`, `LicenseRef-public-domain-aopalliance`, `LicenseRef-public-domain-xz-1.9`), with the full text stored under `security/licences/`.
3. **Still blocked:** anything ADR 0026 Decision 2 blocks. A text that is ambiguous, conditional or missing counts as **unknown** and stops the work.
4. **Shipped components are unchanged:** these forms are not allowed for anything shipped without a new decision.
5. **Planted test:** a `LicenseRef-` build-tool entry without a stored text file fails.

Components covered today: `oro:oro:2.0.8` (Apache-1.1), dom4j 1.1 (BSD-style), `aopalliance:aopalliance:1.0` (public domain) and XZ for Java 1.9 (public domain). Upstream to Twinfra with ADR 0026 Decision 4.

### Ruling (architect, 2026-10-20): Maven plugin inventory scope and invocation guard

Evidence (Codex trace, 2026-10-20): `dom4j:dom4j:1.1` reaches the plugin graph only through `doxia-site-renderer:1.11.1 → velocity-tools:2.0`. The plugins that bring it in are `maven-site-plugin:3.12.1` (`site`), `maven-invoker-plugin:3.7.0` (only in the inactive `enforcerNegativeTest` profile) and `maven-dependency-plugin:3.7.0` (no bound execution). The workflows run only `mvn -version` and `mvn -B -f pom.xml verify`.

1. **Scope.** The Maven build-tool inventory covers the plugins, with their full plugin classpaths, that **gated commands execute**: every `mvn` or `./mvnw` invocation in `.github/workflows/`, with the profiles those invocations activate. That includes the licence gate's own collector commands. Plugins that Maven binds only to phases or profiles no gated command reaches are out of scope.
2. **Record the excluded set; don't hide it.** List each out-of-scope plugin in `security/maven-unexecuted-plugins.json`: coordinates, binding, reason, and the evidence date. These are not register components and get no licence class.
3. **Invocation guard (it blocks).** The licence-gate job parses every workflow `run:` step for Maven invocations, and compares their goals, phases and `-P` profiles with an allow-list in `security/licence-policy.json` (`gatedMavenCommands`). Anything new fails until the inventory is re-evaluated: for example `mvn site`, `-P enforcerNegativeTest`, or a new `dependency:` goal.
4. **The collector must not run `maven-dependency-plugin:3.7.0`.** Establish module scope and reachability from **per-module** CycloneDX BOMs (`makeBom` per module: their component scopes and dependency graph), not from the aggregate BOM's labels.
   - If per-module BOMs can't establish reachability, propose a newer `maven-dependency-plugin` whose plugin classpath contains no `dom4j:1.1`, with its graph as evidence. Don't adopt it before the architect reviews it.
   - Every plugin the collector does run is in scope (item 1) and is registered.
5. **`enforcerNegativeTest` stays a manual diagnostic.** It is not a gated command. If it is ever added to CI, the guard fails, and dom4j 1.1 comes back for a decision.
6. **Planted tests:**
   - a workflow step running `mvn site` fails the guard;
   - a step activating `-P enforcerNegativeTest` fails;
   - a new plugin bound to `verify` whose classpath holds an unregistered component fails;
   - a listed unexecuted plugin that becomes bound to `verify` fails.

### Ruling (architect, 2026-10-20): resolved-scope fallback and the Logback finding

1. **Adopt `maven-dependency-plugin:3.11.0` for the collector** (Apache-2.0, POM published 2026-05-24, no dom4j in its 51-component graph).
   - Add only its exact `dependency:tree` invocation to `gatedMavenCommands`.
   - Register its whole executed classpath under the families (ADR 0026, and the permissive ruling). If anything in it is blocked, stop.
   - `maven-dependency-plugin:3.7.0` stays in `maven-unexecuted-plugins.json`.
2. **Scope authority.** Maven's **resolved** per-module tree decides scope and reachability. CycloneDX supplies component identity, licence and hashes.
   - A component in the resolved tree but missing from the BOM fails the gate.
   - A scope disagreement where the resolved tree is clear isn't a failure: it is recorded in the gate report.
   - The planted scope-conflict test changes to assert that resolution, plus a case where the tree and BOM sets differ, which fails.
3. **Logback finding (outside Part A's scope).** The identity POM declares `ch.qos.logback:logback-classic` directly at `test` scope. Maven's nearest-wins mediation then probably removes Logback from the runtime classpath, contrary to that line's comment.
   - In the Part A PR, report the resolved scope, and whether the packaged identity artifact contains Logback.
   - **Change no behaviour in Part A.** Classify by the resolved tree.
   - The fix is a separate, owner-approved follow-up. Logback is `EPL-1.0 OR LGPL-2.1`, so shipping it needs its own runtime licence decision, like ADR 0025, before or with the fix.

### Ruling (architect, 2026-10-20): attaching Part B evidence to legacy entries

The legacy fingerprint (`licence_ladder.fingerprint`) covers every register field except `tier` and `enterpriseGrade`. The schema forbids `criteria` alongside `legacy-pending`. The checker and schema stay unchanged.

1. **Image SBOMs, with a re-fingerprint for evidence only.** For the seven images whose `image-sbom` baseline entries expire on 2027-01-18:
   - add `imageSBOM` (path and SHA-256) to the register entry;
   - update **only** that entry's `sha256` in `ladder.legacy`;
   - remove the `image-sbom:` baseline entry.
   - Its `tier` and `due` (2027-04-20) stay unchanged.
2. **Guard test.** For each re-fingerprinted entry, the old and new register entries must differ **only** by the added `imageSBOM` key: the same coordinates, digest, licence, class and tier, and the same due date in policy. A planted case that changes anything else alongside `imageSBOM` must fail. List the seven old and new fingerprints in the PR. The owner's approval of the Part B PR re-approves those seven.
3. **Supply-chain criterion evidence is not attached to legacy entries.** Store each runtime component's scan evidence under `security/evidence/supply-chain/`: the SBOM digest, the Grype and OSV results, the tool versions, the date, and the pass result under ADR-0049. When full ADR-0054 records are written (Part C, IOT-WO-06, or the backfill before 2027-04-20), their `supplyChain` criterion links to that file. This replaces the second sentence of the Part B prompt's item 3.
4. Everything else in Part B stands, including the stop rule for unfixable Critical or High findings.
