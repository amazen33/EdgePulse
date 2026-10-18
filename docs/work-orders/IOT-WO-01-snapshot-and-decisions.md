# IOT-WO-01: Safety snapshot, decision records and freeze

**Status:** Approved for implementation (owner, 2026-10-14: decisions D-1 "Option A" and D-2 "licence gate applies"; the snapshot push follows the architect's recommendation, which the owner delegated).
**Author:** Claude · **Implementer:** Codex · **Repository:** `D:\project\IOT-EE` (`github.com/amazen33/IOT-EE`)
**Decisions:** ADR 0014, 0020, 0021 (Accepted) and 0022 (Proposed), drafted in `E:\vcloud-handoff\iot-ee\adr\`.
**Review:** `E:\vcloud-handoff\reviews\iot-ee-review-2026-10-14.md`

**Out of bounds:** Twinfra (`E:\vCloud`), the pCloud repository, the Hyper-V lab and its WSL controller. Nothing here is deployed.

## Part A: safety snapshot. Do this first; nothing else touches the working tree before it.

The working tree on `docs/reconcile-roadmap-and-direction` holds 83 uncommitted changes from 2026-09-26: 28 modified, 7 deleted and 48 untracked. They exist only on this disk.

1. **Check before committing.**
   - Run a secret scan over every changed and untracked file. Use a pinned scanner, or the repository's own checks if they exist.
   - Confirm that `deploy/01-k8s-engine/rke2-ansible/inventory/hosts.ini`, which is tracked and modified, contains only RFC 5737 example addresses. If it contains real addresses, **leave it out** and report.
   - Leave out `.vscode/`.
   - Leave out `IOT.jpg` and report its size. The owner decides whether to keep it.
   - Report any other file you leave out, with the reason.
2. Create the branch `wip/reconcile-snapshot-2026-09-26` from the current `HEAD` (`7dde126`) and commit everything else as one commit: `wip: snapshot of uncommitted reconcile work (not for merge)`.
3. Create the annotated tag `archive/reconcile-snapshot-2026-09-26` on that commit.
4. **Push the branch and tag after the owner approves the push.** Open no PR, or only a draft titled "DO NOT MERGE".
5. Report the commit hash, the file count and the list of excluded files.

Then the **owner merges PR #29** (caller authorization), unchanged. Two conditions, at the owner's request (2026-10-14):
- the pre-merge test has passed: `E:\vcloud-handoff\receipts\iot-ee-pr29-pre-merge-test-2026-10-14.md`, done;
- the milestone plan `E:\vcloud-handoff\iot-ee\MILESTONES.md` is approved.

## Part B: decision records (one PR, `codex/iot-wo-01-decisions`, from `main` after #29)

1. **Add the ADRs**, numbered under `docs/adr/README.md`:
   - `0014-supply-chain-scanning.md`;
   - `0020-tb-ce-operational-core.md`;
   - `0021-twinfra-platform-and-licence-gate.md`;
   - `0022-migration-manager-integration.md` (Accepted by the owner on 2026-10-14);
   - `0023-product-names.md` (Accepted by the owner on 2026-10-14). The rename itself is IOT-WO-05.

   Copy them from the handoff pack word for word. Copy this work order to `docs/work-orders/`, the review to `docs/reviews/`, and `E:\vcloud-handoff\iot-ee\MILESTONES.md` to `MILESTONES.md` at the repository root. The milestone plan replaces the roadmap sections in `README.md` and `CLAUDE.md`, which then point to it.
2. **Accepted ADRs are not edited.** In `docs/adr/README.md`:
   - record that 0019 Decision 4 is superseded by 0020;
   - update the next free number;
   - list the **withdrawn drafts** under "Withdrawn drafts (kept in tag `archive/reconcile-snapshot-2026-09-26`)".
3. **Bring from the snapshot to `main` only what survives:**

   | Snapshot item | Disposition |
   | --- | --- |
   | Drafts withdrawn by ADR 0020: tb-ce-kafka-bridge, pre-tb-ce-anomaly-review, mqtt-broker-and-cross-region-recovery | Stay in the tag only |
   | Drafts withdrawn by ADR 0021: private-cloud-infrastructure, private-cloud-platform-options, kubernetes-options-and-platform-tool-roles, deployment-layers-tool-catalog-and-profiles, cilium-network-and-workload-security, observability-installation-sequence | Stay in the tag only |
   | milestone-naming-and-roadmap | Stays in the tag. The backlog is replaced by the IOT-EE epics in the handoff pack |
   | migration-studio-cdc-and-tenant-rules; `docs/legacy-migration-execution-plan.md` | Move to `main` with a banner: "Moved to migration-manager's scope by ADR 0022; kept as its input specification." |
   | identity-authorization-and-privileged-access; end-to-end-identity-and-entity-traceability; platform-communication-direction; service-api-and-payment-provider-boundaries; resilience-and-workflow-patterns | Move to `main` as `XXXX-proposed-*`, unchanged (application-level) |
   | ai-and-device-adapter-boundaries; device-adapter-contract-and-capability-negotiation | Move to `main` with a banner: "Needs revision for ADR 0020: devices connect to TB CE transports." |
   | config-studio; ai-integration-port-and-controls; tenant-device-map-and-location; workflow-engine-selection; roles-and-privileged-environment-access | Move to `main` with a banner: "Deferred until after the TB CE core runs on Twinfra." |
   | `docs/enterprise-readiness-review.md`, `docs/spikes/**` | Move to `main`. Give the review a banner: "Dated 2026-09-26; superseded in part by ADR 0020–0022." |
   | `docs/event-processing-topology.md`, `docs/ai-device-traceability.md`, `docs/inventory/**`, `docs/compliance/**`, `tools/**` | Move a file to `main` only if it doesn't contradict ADR 0020 or 0021. Otherwise it stays in the tag. List each file with a one-line reason in the PR |
   | `contracts/ai`, `contracts/device`, `contracts/deploy` | Stay in the tag. Contracts come through IOT-WO-03 |
   | `deploy/02-cluster-addons`, `deploy/03-observability`, `deploy/catalog`, `deploy/profiles`, `deploy/checks`, the RKE2, Hyper-V and kube-vip changes | Stay in the tag (frozen by ADR 0021) |
   | `deploy/04-apps` | Move to `main` only if it holds a Helm or Argo CD skeleton with no infrastructure assumptions. Otherwise it stays in the tag; report which |
   | Modified `CLAUDE.md`, `README.md`, `docs/*.md`, workflows | Use them as input for step 4. Do not copy them over `main` wholesale |

4. **Update the pointer documents** to match ADR 0014 and 0020–0022:
   - **`CLAUDE.md`:**
     - roadmap: M1 and M9 move to migration-manager; add the migration-readiness epic;
     - plug-and-play: TB CE is the core;
     - the stage checklist's deployment artifacts become "Helm chart and Argo CD Application for Twinfra";
     - the Trivy paragraph becomes ADR 0014.
   - **`README.md`:** status and platform table.
   - **`docs/architecture.md`:** the data path from ADR 0020 Decision 7.
   - **`docs/requirements-addendum.md`:** a header note naming the amending ADRs. Leave the body unchanged.
   - **`docs/test-plan.md`:** mark the M1 and M9 rows "moved to migration-manager (ADR 0022)".

## Part C: freeze and archive (one PR, `codex/iot-wo-01-freeze`)

1. Tag `archive/iot-ee-own-infra` on `main`.
   - Add `deploy/FROZEN.md`, and a one-line banner in each frozen layer's README, saying the code is frozen by ADR 0021 and must not be extended.
   - Keep `infra.yml`'s static checks running until the deletion work order.
2. Tag `archive/python-spec-final`, then remove `spec/` from `main`.
   - Remove the Python spec gate from CI and `CLAUDE.md`.
   - Everything that referenced `spec/` now points to the tag.
   - The M1 Python module stays reachable for migration-manager through the tag.

## Acceptance

- The snapshot branch and tag are on the remote, and the hash and excluded-file list are reported.
- `mvn -f pom.xml verify` passes and CI is green on both PRs.
- `main` holds no withdrawn draft.
- `git grep -n -i -E "trivy|rke2|kube-vip|lgtm|grafana|emqx|minio|redpanda|opentofu"` outside `docs/adr/`, `docs/reviews/`, the banners and `deploy/` frozen layers returns no hits, or each hit is listed and justified in the PR.
- Every disposition in step 3 is listed in the PR description.

## Status (2026-10-14, Claude with the owner; Codex on hold)

- **Part A: done.** Branch `wip/reconcile-snapshot-2026-09-26` (`6095c9c`) and its tag are on `amazen33/EdgePulse`.
- **PR #29: merged** as `4fc105a`. It was re-tested on the current `main` first: Java 211/211, Python 437 OK.
- **Correction to the review:** `main` already contains PRs #30–#35, merged on 2026-09-27/28. They hold the standalone Layer 0–2 packages (Hyper-V, RKE2, kube-vip) and their lab evidence. Part C's freeze (`archive/iot-ee-own-infra`) covers them as well.
- **Release streams:** PR #36 set the pom version to 2.0.0 and added RELEASING.md, CHANGELOG.md, compatibility.yaml and the rulesets.
- **Still open:** Part B (decision records and draft dispositions), Part C (freeze and archive), then IOT-WO-05 (rename).
