# IOT-WO-07: Delete the frozen own-infrastructure layers from `main`

**Status:** Approved (owner, 2026-10-20). **Decision:** ADR 0021 ("frozen … until the deletion work order"), and IOT-WO-01 Part C.
**Author:** Claude · **Implementer:** Codex, as the Enterprise Senior cloud engineer · **Branch:** `codex/iot-wo-07-delete-deploy`
**Start gate:** PR #46 (IOT-WO-02 Part A) has merged. Run this **before** IOT-WO-02 Part B, so Part B doesn't scan images that are about to be removed.
**Deadline it clears:** licence-baseline entries that expire on **2027-01-18**: three `image-digest` entries for `deploy/` manifests, and the `image-sbom` entries for busybox, `kube-vip` and `kube-vip-cloud-provider`.

## Why delete rather than fix

`deploy/` holds the Hyper-V, RKE2 and kube-vip layers that ADR 0021 froze. Twinfra provides deployment; EdgePulse's runtime path is the TB chart, the kind harness and, later, Twinfra's Argo CD. The full history is preserved in the tag `archive/iot-ee-own-infra` (`9bd22f2`, on `ca1f6d7`). Pinning digests in code that must never be extended would spend effort for nothing.

## Scope

1. **Preflight (report, and stop if any check fails):**
   - the tag `archive/iot-ee-own-infra` resolves to `ca1f6d7`, and `git ls-tree` on it lists `deploy/`;
   - nothing outside `deploy/` imports, executes or references a `deploy/` path functionally. List every reference by file. Prose or history references are fine.
2. **Remove** `deploy/` (61 files) with `git rm -r`, and `.github/workflows/infra.yml`.
3. **Licence gate:**
   - remove the components that only `deploy/` used from the register and policy (busybox, `kube-vip`, `kube-vip-cloud-provider`, and anything else only `deploy/` used, each listed);
   - remove the baseline entries that become obsolete: the three `image-digest` entries and their `image-sbom` entries. **Keep** the legacy entries that other code still uses.
   - The legacy fingerprints and due dates of the remaining entries don't change.
4. **Naming gate:** drop the `deploy/*` glob from `.github/naming-allowlist.txt`, and confirm the gate still passes.
5. **Documents:**
   - `CLAUDE.md` and `AGENTS.md` (kept the same): the repository layout and the gate table drop `deploy/` and the infrastructure gate, and point to the tag;
   - `README.md` and `docs/architecture.md`: the same;
   - `deploy/FROZEN.md` goes with the directory. Add a one-line note to `docs/adr/README.md` that IOT-WO-07 carried out ADR 0021's deletion.
   - Dated history documents keep their text.
6. **Required checks:** `layer0`, `ansible` and `kubernetes` are not required checks; confirm that before removing `infra.yml`. A CHANGELOG entry.

## Out of scope

The Hyper-V lab and its WSL controller: both stay untouched. The lab runs from separate pCloud worktrees on their own branches, which this change doesn't touch. The `archive/*` tags are not modified.

## Acceptance

- `mvn -B -f pom.xml verify` passes.
- CI is green: `java-platform-bootstrap`, `naming-gate`, `release-checks` and `licence-gate`.
- The baseline no longer contains the three `image-digest` entries or the removed images' `image-sbom` entries.
- The PR lists every removed register, policy and baseline entry, and every remaining `deploy/` mention with its reason.

### Clarification (architect, 2026-10-20)

Preflight item 1's stop rule **excludes `.github/workflows/infra.yml`**: item 2 already removes that workflow, which exists only to test `deploy/`. The inert, Twinfra-shaped path references in the ported `security/check_licences.py` and `security/licence_inventory.py` (absent paths such as `deploy/hyperv/…` and `deploy/kustomize/…`) are not dependencies either. **Leave them unchanged**, because the port must stay byte-identical. Every other preflight rule stands.
