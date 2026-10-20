# Supply-chain gate (ADR 0014, IOT-WO-02 Part B)

This is static scanning of public, digest-pinned artifacts and the resolved
Maven graph. It grants no environment access or deployment acceptance.
The separate blocking job is `supply-chain-gate`. Existing required job names
are unchanged; the owner adds the new name to the ruleset after merge.

The byte-for-byte first port is commit `0a5a2f1`, from Twinfra
`0d950075a8bf43358d9fd406b80b67d657f804e1`; see [UPSTREAM.md](UPSTREAM.md).
The scanner engine, staging, candidate scanning and integrity tests retain
their upstream behavior. The issue writer's repository identity and the
repository-specific tests/workflows are adapted for EdgePulse. Nine tests or
helpers asserting Twinfra's own historical commits, layouts, promotions or
workflow topology are replaced by EdgePulse inventory, permission, graph and
backfill checks. No Twinfra infrastructure or old exceptions are imported.

| Tool | Version | Published | Licence / class |
| --- | --- | --- | --- |
| Syft | 1.52.0 | 2026-09-17 | Apache-2.0 / build-tool |
| Grype | 0.119.0 | 2026-09-17 | Apache-2.0 / build-tool |
| OSV-Scanner | 2.6.0 | 2026-09-14 | Apache-2.0 / build-tool |
| actionlint (upstream file-SBOM regression input) | 1.7.12 | 2026-03-30 | MIT / build-tool |

[security/toolchain.lock.json](../../security/toolchain.lock.json) retains Twinfra's exact archive,
binary and checksum-document pins. The adapter checks official checksum
documents and the 14-day minimum age, then the unchanged staging code checks
archive bytes, regular archive members and binary bytes. The file-SBOM
regression never executes actionlint. It verifies extraction, actual ELF
cataloging and a real Grype match result without weakening scanner failures.

## Commands (Linux scanner runner)

```text
python tools/ci/edgepulse_supply_chain.py verify-manifests
python tools/ci/stage_tools.py --source . --destination target/scan-tools --only syft grype osv-scanner
python -m unittest discover -s tools/ci/tests -v
mvn -B -f pom.xml verify
python security/collect_maven.py
python tools/ci/edgepulse_supply_chain.py run
```

On Windows the offline tests and Maven gates are supported, using Python or
`py -3`. Registry scanning runs on Linux CI; it never invokes a WSL distro.
The inventory reads tracked active YAML/Dockerfiles and `dev/kind/pins.json`,
normalizes registry names, rejects tags without digests and scans every
reference. Image SBOMs are cached by digest, platform and scanner checksum;
cache metadata and bytes must agree. Each run downloads a fresh Grype database
and KEV catalogue and retains scanner checksums, database metadata, inventory,
raw results and SBOMs in its artifact. SBOMs are not committed.

OSV receives every per-module all-scope CycloneDX BOM plus the executed-plugin
classpath BOMs from Part A. The same resolved-tree/BOM joins and stale-evidence
checks run first; resolved trees remain scope authority. Nothing is inferred
from CycloneDX's generic `required` label. Lockfiles use `--no-resolve`.

KEV blocks, including when an exception matches. Critical-with-fix blocks;
High-with-fix follows the PR-introduction/14-day first-seen rules. Other findings
remain visible. Exceptions must match exact identities, carry owner approval,
fit the unchanged 30/60/90-day limits and reference reviewed evidence in
`security/evidence/vulnerability-exceptions/` through `controls`. JVM records
also need a `Reachability:` call-path/classpath argument. No exceptions are
generated or fabricated. Amendment 5 applies ADR-0049 as written: findings
with no fix are report-only and never receive exceptions. Remaining fixable
findings reference IOT-WO-08 or Part C, due 2026-11-19; no KEV is excepted.

The initial list uses the upstream `pending-owner` mechanism only for a
same-repository PR from `codex/iot-wo-02-b` into `main`. A bootstrap PR pass is
not approval. Ordinary pushes, main, forks and other branches reject that
marker. The owner reviews the exact list and records approval before merge;
the approved entries must name `amazen33` rather than `pending-owner`.

## Evidence and alerts

The work order's evidence-only ruling permits adding `imageSBOM` to exactly
seven existing image entries and updating only their matching legacy hashes.
`verify_backfill` compares against immutable base `ca61776` and rejects any
other change to unchanged records, their tiers or deadlines. Amendment 5's
Tomcat and PostgreSQL replacements retire the old legacy admissions and need
full ADR-0054 records. The out-of-support Spring and Jackson lines retain
their exact runtime register values and fingerprints until Part C. Baselines remain
open until actual reviewed evidence is attached. No `supplyChain` criterion is
added to a `legacy-pending` record. Per-runtime-component scan receipts belong
under `security/evidence/supply-chain/` for future full ADR-0054 records.

Canonical reviewed CycloneDX copies omit only their document-instance UUID
and creation timestamp, preserving components, licences, relationships and
provenance. Their SHA-256 binds the reviewed content. Original scanner output
is also retained in the run artifact.

The licence job materializes these same files with `image-sboms`, using the
pinned Syft binary and integrity-checked cache. The unchanged licence checker
compares their bytes against the reviewed hashes. Expired artifact retention
cannot silently replace an SBOM or remove the evidence check.

The nightly scanner has `contents: read` and no repository secrets. A separate
main-only reporter consumes its artifact with only `issues: write`; it creates
or updates one trusted `Supply-chain scan: open findings` issue, preserving
first-seen state and refusing duplicates/untrusted reserved titles. Weekly
candidate comparisons are artifacts only; they do not create a second issue,
change locks or execute candidate code. Missing verifiable candidates remain
explicitly unavailable. The upstream watch's isolated scan/retry behavior is
retained. No exception, pin, scanner failure or required check is bypassed.

GitHub API reads use the workflow's read-only token to avoid the shared
runner's anonymous rate limit. The adapter attaches it only to HTTPS requests
to `api.github.com` and rejects mutation requests. Registry, download and
other URLs receive no GitHub token. The scanner still has no issue-write
permission; the first-seen parser and its fail-closed checks are unchanged.

The adapter generates an ignored compatibility lock at `tools/ci/toolchain.lock.json`
from the tracked security lock before the unchanged staging/verifier runs. CI
uses `security/requirements.txt`; the duplicate upstream requirements copy is
retained in the first port commit only. These paths preserve the licence
checker's existing CI-only tool boundaries.
