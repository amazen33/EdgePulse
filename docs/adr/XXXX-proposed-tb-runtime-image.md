# ADR XXXX (proposed): The EdgePulse ThingsBoard runtime image

**Status:** Proposed (architect, 2026-11-23), for owner decision. The number is assigned at merge (`docs/adr/README.md`; the next free number is 0029 today). Earlier exception records call this record "ADR 0029". If another ADR merges first, those references mean this record.
**Author:** Claude (architecture). **Implementer:** Codex ([IOT-WO-09](../work-orders/IOT-WO-09-tb-runtime-image.md)).
**Applies:** ADR 0014 (Twinfra ADR-0049), ADR 0020 Decision 1, ADR 0021 Decision 3 and Amendment 1, ADR 0028 Decision 3, and Twinfra ADR-0044 Decision 6 and ADR-0054 as ported to EdgePulse.
**Does not change:** any ADR 0014 or ADR 0028 gate rule, ADR 0020's no-fork rule, the ported scanners, ladder and schemas, or ADR 0014 Decision 4 (signing follows Twinfra).

Everything this record describes is a **target**. No image exists, nothing has been built, and nothing here is a runtime, deployment or milestone claim.

## Context

**The pinned core.** ThingsBoard CE 4.3.1.8 is EdgePulse's operational core (ADR 0020). Its image is
`docker.io/thingsboard/tb-node@sha256:5e2c180f3c48a9f4efd3e19d2f03c41b510ff1a935f25083657e0cf046a94872`,
with a full ADR-0054 record verified on 2026-10-30
([qualification](../../security/evidence/iot-wo-08/tb-4.3.1.8-qualification-2026-10-30.md)).
It is referenced from `charts/edgepulse-thingsboard/values.yaml` and `dev/kind/pins.json`.

**How upstream builds it** (observed 2026-11-23 in `msa/tb-node/docker/Dockerfile` and `msa/pom.xml` at tag `v4.3.1.8`, commit `ebbfc6789b81a4e04cae2711208130fb2841b31f`):
- the base is `thingsboard/openjdk25:trixie-slim`, ThingsBoard's own Debian 13 image with Debian's OpenJDK 25 packages;
- a `RUN` adds the font packages `libharfbuzz0b`, `fontconfig` and `fonts-dejavu-core`;
- `thingsboard.deb` is installed with `dpkg -i`, which puts TB under `/usr/share/thingsboard` (with `bin/thingsboard.jar`, mode 555) and creates the `thingsboard` user;
- `start-tb-node.sh` goes to `/usr/bin`, `logback.xml` to `/usr/share/thingsboard/conf`;
- `USER thingsboard`, `CMD ["start-tb-node.sh"]`.

**The findings.** The 2026-11-23 scan (PR #70, run 45132416685) shows 24 fixable findings on that digest, 4 Critical and 20 High, none KEV
(`security/evidence/vulnerability-exceptions/tb-renewal-2026-11-23.md`, added by PR #70). All of them are in Debian packages: OpenJDK 25, glibc, zlib and apt. None is in TB's own files. Debian 13 has published every fix; the upstream image has not picked them up. Docker Hub's `thingsboard/tb-node` 4.3.1 tags end at 4.3.1.8, and TB 4.4.0 and later are BUSL-1.1, which the ladder never allows.

Debian archive dates, read from `snapshot.debian.org` on 2026-11-23 (the amd64 binary's first appearance in the archive):

| Source package | Fixed version | First seen | 14-day cool-off ends |
| --- | --- | --- | --- |
| `openjdk-25` | `25.0.5.1+2-1~deb13u1` | 2026-11-19T11:09:23Z (`debian-security`) | 2026-12-03T11:09:23Z |
| `glibc` | `2.41-12+deb13u5` | 2026-11-14T14:41:01Z (`debian` pool; suite membership to be checked) | 2026-11-28T14:41:01Z |
| `zlib` | `1:1.3.dfsg+really1.3.1-1+deb13u1` | 2026-11-07T07:53:04Z (`debian-security`) | 2026-11-21T07:53:04Z |
| `apt` | `3.0.4` | 2026-11-04T12:03:37Z (`debian-security`) | 2026-11-18T12:03:37Z |

The newest Debian 13 slim base on Docker Hub, observed the same day, is `debian:trixie-20261104-slim`, pushed 2026-11-05T08:28:00Z, index digest `sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2`. It is a candidate, not yet verified by digest.

**The bridge.** The owner approved A-5 on 2026-11-23: 24 rows on the upstream digest, expiring 2026-12-23, void if TB starts anywhere, with no extension. Coverage has grown from 8 rows on 2026-11-19 to 24. A-5 condition 3 requires this record and IOT-WO-09 to be issued, and the owner set a replacement-validation target before 2026-12-23.

**The constraint.** ADR 0020 Decision 1 says TB is never forked and never modified in source. IOT-WO-08 says EdgePulse never forks, patches or rebuilds TB. The question is whether TB's unchanged files can run on an EdgePulse-maintained Debian base without breaking that rule, and how that would be proven.

## Decision

### 1. What the image is

`ghcr.io/amazen33/edgepulse-tb-node`, always referenced by digest. It holds three things:
- a Debian 13 base (Decision 2);
- the Debian packages of the upstream image, at fixed versions (Decision 2);
- ThingsBoard CE 4.3.1.8's files, copied unchanged from the upstream digest (Decision 3).

It is a **re-based distribution of the same TB build, not a TB build**. EdgePulse compiles no TB source, runs no TB Maven build, and patches, re-packs or edits no TB file, configuration or script. "Rebuild TB" in ADR 0020 and IOT-WO-08 keeps its meaning: producing TB bytes other than upstream's. That stays forbidden. Byte identity (Decision 3) is the evidence that this image does not do it. The image is not a TB customisation, so `tb-extensions/manifest.yaml` keeps its empty customisation lists and only records the runtime image as the distribution of the pinned version.

### 2. Base and JDK

1. **Base:** the Docker Official Image `docker.io/library/debian:trixie-<serial>-slim`, pinned by its `linux/amd64` manifest digest, with the index digest recorded beside it.
   - It is the same distribution and release as upstream's base.
   - Docker Official Debian images are built from `snapshot.debian.org` at a stated date, so the base has a reproducible origin.
   - `docker.io/library/debian` is already in the licence policy's `baseOSRepositories`.
2. **JDK:** Debian's own `openjdk-25-jre-headless` and `openjdk-25-jdk-headless` from Debian 13 (`trixie` or `trixie-security`), at `25.0.5.1+2-1~deb13u1` or later.
   - These are the packages upstream ships, at a fixed version. The vendor build, install path (`/usr/lib/jvm/java-25-openjdk-amd64`) and alternatives links stay the same, so `start-tb-node.sh` finds and runs the JVM the same way.
3. **Package source:** every package comes from `snapshot.debian.org` at one pinned timestamp `T`, with apt's normal signature check of Debian's signed `Release` files. A build lock lists every package as `name=version`, with the `.deb` SHA-256 from the signed `Packages` index and the archive's first-seen time.
4. **Package-set parity:** the image's Debian package names equal the upstream image's (from its `/var/lib/dpkg/status`), with `thingsboard` carried as described in Decision 3. Each version is equal to or newer than upstream's under Debian version ordering. Nothing is added. Removing a package (for example `openjdk-25-jdk-headless`) is a later, separately reviewed change with its own parity evidence.
5. **Platform:** `linux/amd64` only, the platform the gate scans. Other platforms need their own decision.
6. **Cool-off (ADR 0014),** measured at the commit that last changes the build lock, and checked by CI on every run:
   - the base serial was published at least 14 days earlier;
   - `T` is at least 14 days earlier, so every package available at `T` is at least 14 days old;
   - ADR-0049's expedite applies unchanged: the owner may waive the cool-off for a fix to a KEV-listed or actively exploited vulnerability, in the PR.
   - Changing either input restarts its clock.
   - With today's dates, the OpenJDK fix sets the floor: `T` no earlier than 2026-11-19T11:09:23Z, so the lock can't be final before 2026-12-03T11:09:23Z.
7. **Licence qualification (ADR-0054, ported):**
   - **The Debian base digest** gets its own register record, class `base-os`, with all six criteria verified from primary HTTPS sources (the Debian project's governance, security team and support dates; signed archive; the gate result).
   - **The OpenJDK packages** get an evidence record with all six criteria: the OpenJDK project's governance and update releases, and Debian's security support for them. The register has no Debian-package ecosystem, so this qualification lives in evidence and is cited by the runtime image's record. OpenJDK is `GPL-2.0-only WITH Classpath-exception-2.0`. It is used as an unmodified distribution package, a separate program, which the `base-os` class allows (Twinfra ADR-0044 Decision 6).
   - **The runtime image** gets an `oci-image` record, class `allowed`, `Apache-2.0` at image level, exactly as the upstream TB record is registered (ADR 0021 Decision 3). Each of its six criteria cites the TB, Debian base and OpenJDK evidence, and passes only if it passes for all three. It can't be `legacy-pending`.
   - **The upstream TB record** stays as it is. Its `locations` move from the chart and kind pins to the build lock.
   - No schema or ladder change. If the checker cannot accept these records as they are, Codex stops and reports.

### 3. Byte identity

1. **The TB file set**, read from the upstream image:
   - every path in `/var/lib/dpkg/info/thingsboard.list`;
   - every path under `/usr/share/thingsboard/` and `/var/log/thingsboard/`;
   - `/usr/bin/start-tb-node.sh`;
   - the dpkg records `/var/lib/dpkg/info/thingsboard.*`;
   - the `thingsboard` stanza of `/var/lib/dpkg/status`, and the `thingsboard` lines of `/etc/passwd` and `/etc/group`.
2. **The manifest:** one canonical JSON entry per path, with path, file type, mode, numeric UID and GID, size, SHA-256 for regular files and target for symlinks, plus the three text records above. It is generated offline from the image's layers, fetched by digest, with OCI whiteouts applied. No container is created. It is committed beside the build definition, and its SHA-256 is recorded in the evidence.
3. **The rule:** the runtime image's manifest equals the upstream manifest exactly, in both directions:
   - every file matches on content and metadata;
   - no path is missing;
   - no extra path exists under the TB directories;
   - the dpkg stanza and the user and group lines are byte-equal, so dpkg and the SBOM see the same `thingsboard` package as upstream.
4. **Image configuration parity:** `User`, `Cmd`, `Entrypoint`, `WorkingDir`, `ExposedPorts`, `Volumes` and `StopSignal` equal upstream's. `Env` equals upstream's except for entries in a reviewed delta list, which starts empty. Only OCI labels are added: source, revision, base digest and TB source digest.
5. **How TB files enter:** the build copies them from the upstream digest with `COPY --from` (or an equivalent layer-reading copy). It never uses the release `.deb` or TB source.
   - **No `RUN` step comes after the first TB file enters the image.** A check of the build definition enforces it, so no TB file and no TB maintainer script runs during a build.
   - The `thingsboard` user and group are created earlier, in a stage without TB files, with upstream's UID and GID.
6. **CI comparison:** a job regenerates both manifests from the registry digests on every PR that touches the build inputs, on every build on `main` and in the nightly scan. Any difference fails. Planted tests: one changed byte, a missing file, an extra file, a changed mode or owner, a `RUN` after TB files, and a different TB source digest all fail.
7. **Licence guard:** the TB source must be a `docker.io/thingsboard/tb-node` digest with an active, verified register record whose SPDX is `Apache-2.0` and whose release is in 4.3.1.x. Any 4.4.0+ release, BUSL-1.1 or other SPDX fails, on top of the ladder's existing BUSL block.
8. **Metadata changes are not allowed silently.** IOT-WO-04 may find that TB must run under an arbitrary UID with group 0 (ADR 0021 Amendment 1). Changing TB file ownership or modes for that needs an amendment to this record, which lists each delta and its parity evidence.

### 4. Build and provenance

1. **Where:** only in GitHub Actions in `amazen33/EdgePulse`, in one workflow (`.github/workflows/tb-runtime-image.yml`).
   - The runner is pinned like the other workflows, and every action is pinned by commit SHA.
   - It is triggered by `workflow_dispatch` and by merges to `main` that change the build inputs, never by `pull_request_target`, and never from a developer machine.
   - PRs build without pushing.
2. **Builder:** BuildKit through `docker buildx`, with versions pinned in the toolchain lock and registered as build tools.
   - `SOURCE_DATE_EPOCH` comes from the lock, and timestamps are rewritten to it.
   - apt runs from the snapshot at exact versions. Package lists, apt and dpkg logs, and caches are removed.
3. **Reproducibility:** two builds in separate jobs, from the same commit, must produce the same image manifest digest. If they don't, Codex stops and reports the differing paths, and the owner decides. Layer-only equality is never accepted silently.
4. **Publication:** pushed to GHCR with the publish job's short-lived `GITHUB_TOKEN` (`packages: write`), with no long-lived registry token. This is the pattern Twinfra ADR-0049 Decision 8 already names for its own images.
   - The package is **private**, so EdgePulse distributes no GPL base packages to third parties before a legal review (Twinfra ADR-0030, carried by ADR-0044's consequences).
   - Jobs that pull it get `packages: read` and nothing more.
   - Digests named in merged evidence are never deleted, and no tag is reused.
5. **Signing and provenance:** GitHub artifact attestations, one for SLSA build provenance and one for the SBOM.
   - They are Sigstore-backed and keyless, through GitHub's OIDC token, so there is no key to store. The repository is public, so the entries go to the public Rekor log.
   - Only the publish job holds `id-token: write` and `attestations: write`. It runs no scanner.
6. **Records:** an evidence pair under `security/evidence/iot-wo-09/` holds the inputs (TB source digest, base digests, `T`, the lock's SHA-256), workflow run, commit, image digest, attestation IDs and Rekor log index, the reproducibility result, the manifest hash and the scan reports.
7. **Verification:** before admission, the gate verifies the provenance attestation for the exact digest. It checks the repository, the workflow path, `refs/heads/main` and the commit that holds the lock. The verifier is pinned in the toolchain lock and registered.
8. **ADR 0014 Decision 4 is unchanged.** This covers one EdgePulse-built image. It creates no platform signing policy. When Twinfra adopts signing, this image follows Twinfra's rules. The architect reports this use to Twinfra as information, not as a proposal.

### 5. Gate integration

1. **Strict image.** The runtime image replaces the upstream digest in the chart and kind pins, so ADR 0028 Decision 3 makes it strict, and it can never be `test-harness`. Every ADR-0049 rule applies unchanged: KEV blocks, a fixable Critical blocks at once, a fixable High blocks 14 days after it is first seen, and exceptions are capped and evidenced.
2. **Admission checks**, in EdgePulse's wiring only and marked with this record. For any `ghcr.io/amazen33/edgepulse-tb-node` reference, the gate requires:
   - the provenance attestation verifies (Decision 4.7);
   - byte identity and configuration parity pass against the lock's TB source digest (Decision 3);
   - package-set parity passes (Decision 2.4);
   - every input meets the cool-off at the lock's date (Decision 2.6);
   - the register records exist (Decision 2.7).

   Each check fails closed and has a planted test.
3. **The upstream digest** stays pinned as the byte source and comparison baseline, in the build lock only. The TB refresh job scans it. The main gate scans what EdgePulse deploys or rehearses, as it does today, so exceptions on the upstream digest no longer match anything once it leaves the chart and kind pins.
4. **TB-file findings stay upstream's.** Findings in TB's own files, such as the Java libraries inside `thingsboard.jar`, are identical in both images by construction, and they keep strict treatment on the runtime digest. EdgePulse can't fix them without breaking byte identity. A fixable Critical or High there needs an upstream 4.3.1.x patch or a new, evidenced, owner-approved exception on the runtime digest. This record pre-approves none. The fix-less Spring Criticals named in the A-5 record stay report-only.
5. **TB refresh evidence and net improvement.** Today `tb_refresh_evidence.py` requires both digests to be `docker.io/thingsboard/tb-node`. It is extended, in EdgePulse's wiring only, to compare the upstream digest (baseline) with the runtime digest (candidate), using the same pinned scanners and one database snapshot in one run. It passes only if:
   - ADR-0049's net-improvement rule holds: no new fixable Critical or High identity, and strictly fewer of them;
   - findings located in the TB file set are identical in both images;
   - there are zero KEV matches;
   - every A-5 identity (package and advisory) is absent from the candidate.

   Every later rebuild compares against both the previous runtime digest and the upstream digest.
6. **Weekly watch.** The ADR-0049 weekly watch (IOT-WO-08 item 1) adds the runtime image's inputs: the newest eligible `trixie-slim` serial and new Debian 13 updates for packages in the lock. A qualifying input leads to a rebuild PR. A fixed High in the runtime image blocks after 14 days like any strict image's, and the rebuild is the way to fix it.
7. **A new upstream 4.3.1.x patch** is first qualified as IOT-WO-08 E-3 did for 4.3.1.8. The owner then chooses:
   - the upstream image itself, if it passes the strict gate without exceptions for OS or JDK findings. The runtime image exists because upstream lags, and an upstream image means less for EdgePulse to own.
   - Or a runtime image rebuilt on the new source digest, with a new manifest.

### 6. Rollback

1. **The swap is one reviewed PR.** It changes two references (chart values and kind pins) and the records. Rolling back means reverting that PR. The upstream digest stays qualified, with its verified register record, so the revert is always technically possible.
2. **Rollback is not gate-free.** The swap removes the 24 A-5 rows. A rollback brings the upstream findings back without coverage, so the gate blocks unless the owner approves new, evidenced exceptions (IOT-WO-08 item 4: renewal is never presumed). After 2026-12-23 the A-5 rows can't be reused in any case.
3. **After TB first runs (MS3 or later):** both images hold the same TB version and the same TB bytes, so switching between them needs no database or schema migration, only a values change. This is a target until runtime parity test R7 (Decision 8) proves it.
4. **Runtime image rollback:** earlier runtime digests stay in GHCR (Decision 4.4), so a bad rebuild reverts to the previous digest the same way.

### 7. What "starting TB" means for exception voiding

A-5 condition 1, like A-1 to A-4 before it, voids the rows if TB starts anywhere. This record defines the term so it can be audited.

**Starting TB** is any of these, in any environment (kind, lab, CI runner, developer machine, Twinfra or any cloud):
- creating or running a container, pod or process from the upstream image, the runtime image, or any build stage that holds TB files, whatever the command;
- executing any TB file or TB packaging script: `thingsboard.jar` or its classes, `start-tb-node.sh`, TB's install or upgrade scripts, or the `thingsboard` dpkg maintainer scripts;
- running TB's install or upgrade against any database.

**Not starting TB:**
- pulling, copying, exporting or reading layers and blobs;
- computing hashes and manifests;
- Syft, Grype and OSV-Scanner scans, which read the filesystem and execute nothing;
- building the runtime image, where TB files enter only by `COPY` and no `RUN` follows (Decision 3.5);
- pushing, attesting and verifying;
- rendering Helm charts and the static OpenShift checks;
- running the JDK or Debian tools in a build stage that holds no TB files, for example `java -version` in the JDK stage.

The gate can't detect a start, so the condition is procedural. Any start is reported to the owner the same day, and the rows it voids are removed in the next PR. The definition applies to every current and future TB bridge row that carries this condition. The first start of the runtime image needs owner approval and runtime parity tests R1 to R7 (Decision 8).

### 8. Parity tests

**Before the runtime image replaces the upstream digest.** These are static. None of them starts TB, so all can run now:

| ID | Test |
| --- | --- |
| P1 | TB file-set byte identity (Decision 3.3), both directions |
| P2 | Image configuration parity (Decision 3.4) |
| P3 | Debian package-set parity, and versions at least upstream's (Decision 2.4) |
| P4 | JDK: the fixed `openjdk-25` version at upstream's install path; `java -version` and the `release` file checked in the JDK stage only; `cacerts` and `java.security` present |
| P5 | Static linkage: every `DT_NEEDED` library of the JDK binaries and of any native library inside the TB file set resolves to a file in the image (read with an ELF reader, nothing executed); the font packages and their files are present |
| P6 | `start-tb-node.sh` dependencies: every absolute path and command it names exists in the image (static parse) |
| P7 | Scanner comparison: the extended TB refresh job passes (Decision 5.5), with zero KEV and every A-5 identity absent |
| P8 | Reproducibility: two builds give one digest (Decision 4.3) |
| P9 | Provenance verifies; the chart renders with the `twinfra` and `openshift` profiles and passes the existing static `restricted-v2` checks with the new reference |

**Runtime parity: blocked.** MS3 has not been reached, IOT-WO-04 has not started, and the kind rehearsal is paused (IOT-WO-08 Amendment 2). These tests are preconditions for the **first start of TB from this image**, not for the pin swap. Each runs both images on the same synthetic inputs and compares the results, and each run needs owner approval:

| ID | Test |
| --- | --- |
| R1 | Start to a healthy state with the same configuration and dependency versions; no startup errors that upstream doesn't also show |
| R2 | TB's own install against an empty database; the schema dumps from both images are identical |
| R3 | The REST calls `ThingsBoardPort` and the MR-2 import API set use, for a synthetic tenant, give the same responses |
| R4 | MQTT, HTTP and CoAP telemetry from a synthetic device is stored identically |
| R5 | The stock outbound Kafka node publishes the same message shape to the raw topic (ADR 0020 Decision 3) |
| R6 | Rule-node scripting and the SVG renderer (fonts) give the same results |
| R7 | Switching between the images on one database needs no migration, in both directions |

**Why swap before runtime parity.** The swap changes no running system: TB runs nowhere. The runtime image is exactly as unexercised in EdgePulse as the upstream image is today. The swap is recorded as a **static replacement**, never as runtime validation. The MS3 receipt has to include R1 to R7.

## Consequences

- If P1 to P9 pass, the 24 OS and JDK findings are cleared by a rebuild instead of exceptions, and future base findings follow the same route. This is a target until the comparison proves it.
- EdgePulse owns a build: its inputs, rebuild cadence, reproducibility, provenance and registry. The weekly watch carries that cost, and it is the price of not waiting for upstream.
- Findings in TB's own files are still upstream's to fix.
- This is EdgePulse's first published image and first use of provenance attestations, scoped to one image. Twinfra's later signing decision governs both.
- The private package means scanner jobs that pull it need `packages: read`, and Twinfra will need pull credentials at MS3, through its registry-credential pattern (Twinfra ADR-0028). Making the package public waits for the legal review.
- ADR 0021 Amendment 1's group-0 rule is not applied to TB paths here (Decision 3.8). How TB runs under OpenShift's arbitrary UID stays IOT-WO-04's finding.
- No runtime, deployment, OpenShift or milestone claim follows from this record or from P1 to P9.

## Alternatives considered

- **Keep renewing exceptions.** Rejected. Coverage grew from 8 rows to 24 in four days, renewal is never presumed, and exceptions don't reduce risk.
- **Wait for an upstream 4.3.1.x image with the fixes.** It has no date, and A-5 expires on 2026-12-23. It stays the preferred exit when it comes (Decision 5.7).
- **Move to TB 4.4.0 or later.** Rejected: BUSL-1.1 is never allowed.
- **Build TB 4.3.1.8 from its source tag.** Rejected: it is the rebuild ADR 0020 forbids, and the bytes would differ from the qualified image.
- **Install the published `thingsboard-4.3.1.8.deb`.** Rejected. It is a different artifact from the qualified image, its maintainer scripts would run during the build, and nothing guarantees it matches the image's bytes.
- **Rebase upstream's TB layers unchanged onto a new base** (for example `crane rebase`). Rejected. TB's upper layers also carry `/var/lib/dpkg/status` and `/etc/passwd` as written on the old base, so they would hide the new base's package records: dpkg and the scanners would report the old versions.
- **Derive from the upstream image and run `apt-get upgrade` on top.** Rejected, for four reasons:
  - the vulnerable OpenJDK and glibc bytes stay in the lower layers and are still distributed;
  - ThingsBoard's own base image stays inside, unqualified;
  - the upgrade runs in a stage that holds TB files, which Decision 7 treats as starting TB;
  - the base and the package set can't be controlled separately.
- **An Eclipse Temurin (Ubuntu) or distroless base.** Rejected. Temurin changes both the distribution and the JDK build, which adds parity risk for no security gain. Distroless has no shell, and `start-tb-node.sh` needs one.
- **A newer digest of ThingsBoard's `openjdk25:trixie-slim` base.** Not chosen. It has no published support policy, its tag is mutable, and it keeps upstream's cadence. IOT-WO-09 reports its status for information.

## Cross-references

ADR 0014, 0020, 0021 (with Amendment 1), 0022 (MR-2) and 0028. Twinfra ADR-0028, ADR-0030, ADR-0044, ADR-0049 and ADR-0054.
[IOT-WO-08](../work-orders/IOT-WO-08-image-and-dependency-refresh.md) (Amendments 2 and 3, A-1 to A-6), IOT-WO-04 and
[IOT-WO-09](../work-orders/IOT-WO-09-tb-runtime-image.md).
