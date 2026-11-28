# IOT-WO-09: EdgePulse ThingsBoard runtime image (replaces the A-5 bridge)

**Status:** Proposed (architect, 2026-11-23), for owner approval with [ADR `XXXX-proposed-tb-runtime-image.md`](../adr/XXXX-proposed-tb-runtime-image.md). It is issued, under IOT-WO-08 A-5 condition 3, in the week of 2026-11-23.
**Author:** Claude · **Implementer:** Codex, as the Enterprise Senior cloud engineer · **Branches:** `codex/iot-wo-09-build` (Part A), `codex/iot-wo-09-swap` (Part B)
**Decision:** the TB runtime-image ADR (proposed); ADR 0014 / Twinfra ADR-0049; ADR 0020 Decision 1; ADR 0028 Decision 3; Twinfra ADR-0054.
**Start gate:** the owner accepts the ADR, and PR #70 (the A-5 rows and records) has merged.
**Target date:** a static replacement validated and the 24 A-5 rows removed **before 2026-12-23**, when they expire.

Everything here is a target. No image exists, and no item claims a capability until its PR merges with the evidence named below.

## Why

The 2026-11-23 scan shows 24 fixable findings (4 Critical, 20 High, none KEV) on `docker.io/thingsboard/tb-node@sha256:5e2c180f3c48a9f4efd3e19d2f03c41b510ff1a935f25083657e0cf046a94872` (TB CE 4.3.1.8). All of them are in Debian packages (OpenJDK 25, glibc, zlib and apt), and Debian 13 has published every fix. No upstream 4.3.1.x image carries them, and 4.4.0 and later are BUSL-1.1. The owner bridged the findings with A-5 until 2026-12-23 and required this work order and its ADR this week. The ADR's route: TB's files, byte-identical, on a patched Debian 13 and OpenJDK 25 base. TB itself is not forked or rebuilt.

## Rules for every item

- **Never start TB** (ADR Decision 7). Starting TB voids all 24 A-5 rows. Pulling, scanning, reading layers, building with `COPY`-only TB stages, pushing and attesting are allowed. Running any container from an image or stage that holds TB files is not.
- Never change a TB byte. If TB file parity fails, stop. Never "fix" a difference by editing TB files.
- No TB 4.4.0+ and no BUSL-1.1 component, in any form.
- The ported scanners, ladder, schemas and ADR 0014 and ADR 0028 rules stay unchanged. New checks are EdgePulse wiring, marked with the ADR.
- No `deploy/` or `.vscode/` path is committed. No force-push. Every PR lists its before and after exception and finding counts.

## Planning dates (targets)

| Date | Step |
| --- | --- |
| Week of 2026-11-23 | Owner accepts the ADR and this work order; Part A starts |
| 2026-11-28T14:41:01Z | The glibc fix (`2.41-12+deb13u5`) is eligible, if Part A finds it in the `trixie` suite (not only in proposed-updates) |
| 2026-12-03T11:09:23Z | The OpenJDK fix (`25.0.5.1+2-1~deb13u1`) is eligible. This is the earliest moment the Part A lock can be final |
| By 2026-12-08 | Part A merged; the runtime image built on `main` and attested |
| By 2026-12-12 | Part B PR open, with green P1–P9 |
| 2026-12-16 | Last comfortable merge date for Part B |
| 2026-12-23 | The A-5 rows expire. If Part B hasn't merged, the gate blocks on TB from 2026-12-24. Renewal is not presumed, and the owner decides |

## Scope

### Part A: build definition, tooling and gate wiring (no pin change)

1. **Preflight.** Report each result, and stop if a check fails.
   - The upstream digest resolves on Docker Hub. Record its configuration, its dpkg package list with versions, and its TB file set (ADR Decision 3.1), read offline from its layers.
   - Docker Hub's `thingsboard/tb-node` 4.3.1 tags still end at 4.3.1.8. If a newer 4.3.1.x patch has appeared, report it. The owner chooses between promoting it under IOT-WO-08 and continuing here.
   - Every fixed version in the A-5 table is in the `trixie` or `trixie-security` suite indices at the chosen `T`, not only in the archive pool. Record each package's first-seen time and suite.
   - Verify the base candidate by digest (`debian:trixie-20261104-slim`, index `sha256:a72b4433…`, observed 2026-11-23), or the newest `trixie-slim` serial that is at least 14 days old when Part A opens.
   - For information only: report whether ThingsBoard's `thingsboard/openjdk25:trixie-slim` has a newer digest with the fixes.
2. **Build definition** under `images/edgepulse-tb-node/`:
   - `lock.json`, holding:
     - the TB source digest;
     - the base index and `linux/amd64` digests, with their publication times;
     - the snapshot timestamp `T`;
     - every Debian package as `name=version`, with its `.deb` SHA-256 and first-seen time;
     - `SOURCE_DATE_EPOCH`;
     - the builder versions and SHA-256s.
   - The build file, with these stages, in this order:
     1. the base plus the locked packages from the snapshot (including OpenJDK and the fonts);
     2. the `thingsboard` user and group with upstream's UID and GID;
     3. `java -version` in this TB-free stage;
     4. the TB files by `COPY --from` the upstream digest, with upstream's ownership and modes, and the dpkg stanza and the passwd and group lines carried byte-identical;
     5. upstream's image configuration and the OCI labels.

     **No `RUN` after the first TB file.**
   - `tb-files.manifest.json`: the upstream TB manifest (ADR Decision 3.2).
3. **Tooling** (for example `tools/ci/tb_runtime_image.py`), with no container execution:
   - an offline OCI layer reader that applies whiteouts;
   - manifest generation and comparison;
   - configuration parity;
   - package-set parity using Debian version ordering;
   - the cool-off check against first-seen times;
   - a build-definition lint, so no `RUN` follows the TB `COPY`;
   - static ELF `DT_NEEDED` resolution (P5) and the `start-tb-node.sh` path check (P6).
4. **Planted tests**, each of which must fail. One changed TB byte; a missing TB file; an extra file under a TB directory; a changed mode or owner; a changed `User` or `Cmd`; an extra Debian package; a package older than upstream's; an input inside its 14-day cool-off; a `RUN` after the TB `COPY`; a TB source that isn't the approved 4.3.1.x digest; a TB source with any SPDX other than `Apache-2.0`; an unverifiable provenance attestation; and a reproducibility mismatch.
5. **Workflow** `.github/workflows/tb-runtime-image.yml`:
   - **On PRs:** two independent builds without pushing, then reproducibility (P8), manifest and parity checks against OCI layouts. `contents: read` only.
   - **On `main` and `workflow_dispatch`:** the same build and checks, then a separate publish job that pushes to the private `ghcr.io/amazen33/edgepulse-tb-node` with `GITHUB_TOKEN` and attests SLSA provenance and the SBOM. Only the publish job holds `packages: write`, `id-token: write` and `attestations: write`, and it runs no scanner.
   - Every action is pinned by commit SHA. New actions and tools enter the licence register (as `github-action` and build-tool records) and the toolchain lock.
6. **Gate wiring** (EdgePulse only, marked with the ADR):
   - admission checks for `ghcr.io/amazen33/edgepulse-tb-node` references (ADR Decision 5.2);
   - `tb_refresh_evidence.py` extended to compare the upstream digest with the runtime digest (ADR Decision 5.5);
   - `packages: read` on exactly the scanner jobs that pull the private image, with no other permission change;
   - the weekly watch extended to the lock's inputs (ADR Decision 5.6).

   Each change has planted tests, and the existing suites keep passing.
7. **Licence records and evidence:**
   - the Debian base `base-os` record, with all six ADR-0054 criteria;
   - the OpenJDK qualification evidence, with all six criteria;
   - build-tool and action records.

   If the checker can't accept these without a schema change, stop and report.
8. **Documents:**
   - `CLAUDE.md` and `AGENTS.md` (kept identical) add `images/` to the repository layout;
   - `security/README.md` describes the runtime-image checks;
   - `tb-extensions/manifest.yaml` corrects `pinned_at` to 4.3.1.8 and records the runtime image as the distribution of the pinned version, with the customisation lists left empty;
   - a `CHANGELOG.md` entry.

### Part B: the swap and the A-5 row removal

9. **Evidence on the built digest.** The digest built on `main`:
   - passes P1–P9 (ADR Decision 8);
   - passes a full Linux supply-chain scan and the extended TB comparison (net improvement, zero KEV, TB-file findings identical, every A-5 identity absent).

   Record it in `security/evidence/iot-wo-09/tb-runtime-image-<date>.{md,json}`: inputs, run IDs, commit, digest, attestation IDs and Rekor log index, reproducibility result, manifest hash and report hashes.
10. **The swap:**
    - replace the upstream reference in `charts/edgepulse-thingsboard/values.yaml` and `dev/kind/pins.json` with the runtime digest;
    - the upstream digest stays only in the build lock;
    - add the runtime image's register record (class `allowed`, `Apache-2.0`, all six criteria verified, never `legacy-pending`), and move the TB record's `locations` to the lock.
11. **A-5 row removal**, in the same PR:
    - first confirm, for each of the 24 rows, that its package and advisory identity is absent from the runtime image's scan and that the row matches no scanned input;
    - then remove exactly those 24 rows, removal-only, keeping their exact blocks and block hashes in `security/evidence/iot-wo-09/retired-a5-tb-rows-<date>.json`;
    - the A-5 proposal file stays immutable;
    - the harness regression test allows exactly these removals and keeps its pin on the proposal hash.

    If any identity is still present in the runtime image, don't remove that row silently. Stop and report. The owner decides between a new runtime-digest row with fresh evidence and waiting for a fixed input.
12. **Records:** in this work order, record the Part B merge as the first qualifying replacement under A-5 condition 3. Record what remains blocked (below), and add a `CHANGELOG.md` entry.

## Acceptance (targets)

- **This PR:** the owner accepts the ADR. At merge it is renamed to the next free number, with "(proposed)" dropped and `docs/adr/README.md` updated. Merging it issues this work order.
- **Part A:**
  - CI is green: `java-platform-bootstrap`, `naming-gate`, `release-checks`, `licence-gate`, `supply-chain-gate`, `tb-refresh-evidence` and the new runtime-image workflow;
  - every planted test fails as intended;
  - two builds give one digest;
  - no `RUN` follows the TB `COPY`;
  - the manifest is committed;
  - the build on `main` publishes an attested digest.
- **Part B:**
  - P1–P9 pass on the attested digest, and the gate is green with **no TB exception on the runtime digest** (any new row needs a separate owner approval);
  - the 24 A-5 rows are removed with their evidence;
  - the register records are verified;
  - it merges before 2026-12-23.
- **Every PR** states that TB was not started, and lists its exception and finding counts before and after.
- **Not acceptance:** runtime parity, deployment or any milestone. Part B is a **static replacement**.

## Blocked external verification (recorded as blocked, not passed)

- **Runtime parity R1–R7** (ADR Decision 8). MS3 has not been reached, IOT-WO-04 has not started, and the kind rehearsal is paused (IOT-WO-08 Amendment 2). They are preconditions for the first start of TB from this image, and each run needs owner approval.
- **Twinfra pulling the private image,** or mirroring it into Twinfra's registry (Twinfra ADR-0028): at MS3, under IOT-WO-04.
- **OpenShift live compatibility:** MS7 (ADR 0021 Amendment 1).
- **Legal review of distributing GPL base-OS packages:** needed before the package can be made public. It stays private until then.
- **An independent rebuild outside GitHub's runners:** not available. Reproducibility is shown between two GitHub-hosted builds only.

## Stop rules

Stop and report to the owner, without working around it, if:
- any TB byte or metadata difference appears, or a needed TB path can't be read offline;
- a needed fix is not in an eligible Debian 13 package. The KEV expedite applies only to KEV or actively exploited issues, through the owner;
- two builds differ;
- a new upstream 4.3.1.x digest appears;
- the licence checker or schema can't express the records unchanged;
- any step would need TB to start.

## Owner checkpoints

- **This week:** accept or amend the ADR and this work order. Confirm the private GHCR package (recommended) or ask for an alternative.
- **2026-12-03:** Codex confirms the final `T` and base digest, now that the OpenJDK fix is eligible.
- **Part B PR:** approve the swap and the 24-row removal. The architect reviews the evidence first (the two-party rule).
- **2026-12-16:** if Part B isn't ready, decide before the A-5 rows expire on 2026-12-23.

## Non-goals

- No TB source build, patch, re-pack, configuration change or customisation, and no TB 4.4.0+.
- No TB start, deployment, kind rehearsal resumption or Twinfra change.
- No chart change other than the image reference. No group-0 or arbitrary-UID change to TB paths (that is IOT-WO-04's finding and would need an ADR amendment).
- No change to ADR 0014 or ADR 0028 rules, the ported tools or the schemas. No signing policy for any other image. No platform other than `linux/amd64`.
- No exception for TB-file findings. Those follow ADR Decision 5.4.
