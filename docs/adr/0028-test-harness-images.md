# ADR 0028: Vulnerability policy for test-harness-only images

**Status:** Accepted (owner, 2026-10-21). It lands as 0028.
**Applies:** ADR 0014 and Twinfra ADR-0049 (vulnerability gate), in EdgePulse's port only. Twinfra and the ported tools are not changed. It refines, for one narrow image class, ADR-0049's "dev and production alike".

## Context

The day-one supply-chain run (IOT-WO-02 Part B, PR #48) produced an initial exception list of 303 entries, all expiring **2026-11-19**. IOT-WO-08's first refresh report (2026-10-21) shows that every image is already on its newest eligible release. **266 of the remaining 286 IOT-WO-08 exceptions belong to five images that EdgePulse uses only in its test harness:**

| Image | Exceptions | Where EdgePulse uses it |
| --- | ---: | --- |
| `kindest/node` | 168 | `dev/kind/cluster.yaml`: the disposable kind cluster's node |
| `quay.io/cilium/cilium`, `operator-generic`, `cilium-envoy` | 82 | `dev/kind/` harness CNI. On `cairo-1`, Cilium is **Twinfra's** platform image, scanned under Twinfra's gate |
| `ghcr.io/cloudnative-pg/cloudnative-pg` (operator) | 16 | `dev/kind/up.ps1`: the harness's database operator. On Twinfra, CNPG is a platform service |

These images are referenced **only** from `dev/kind/**` and the `kind-smoke` CI job. They never appear in `charts/**`, and EdgePulse never deploys them anywhere. They run in clusters that are created and destroyed per run, with synthetic data only, a loopback-only API server, no inbound network exposure, and no secrets other than those CNPG generates for the throwaway database. The CI job runs with `contents: read`, on GitHub-hosted runners that are discarded after each run.

ADR-0049's rules are built for images that serve users and hold data. Applied unchanged here, they turn upstream release timing (kind publishes node images with kind releases; Cilium patches on its own schedule) into a merge freeze for every EdgePulse PR, with no reduction in risk to anything EdgePulse ships.

## Decision

1. **A `test-harness` image class.** An image is `test-harness` only when all of the following hold. The gate checks each of them mechanically:
   - it is referenced only from `dev/kind/**` (and from the licence and supply-chain records);
   - it is not referenced from `charts/**`, from any Argo CD or Helm input, or from any path that packages or deploys EdgePulse;
   - every workflow job that runs it has only `contents: read` permissions and no repository or environment secrets.

   The class list is held in the supply-chain policy. Today it is the kind node, the three Cilium images and the CNPG operator. Adding an image needs an architect review in its PR.
2. **Gate behaviour for `test-harness` images:**
   - **A KEV-listed finding still blocks**, with no exception, exactly as for shipped images.
   - Critical and High findings with a fix are **report-only**: they are listed in the nightly issue and the PR summary, with first-seen dates. They don't block, and they need no exception entry.
   - **Staleness blocks:** if a newer eligible release (at least 14 days old) of a `test-harness` image has existed for **more than 30 days** without being adopted, the gate fails until it is adopted or the owner records a dated reason.
   - The images stay scanned on every relevant run, with SBOM evidence, and in the licence register unchanged.
3. **Everything else is unchanged:** TB, the PostgreSQL image in the chart, the identity service's Maven graph, and every image EdgePulse ships stay under ADR-0049 as written. If a `test-harness` image ever appears in a shipped path, the gate fails (check 1), and moving it back to strict needs no decision.
4. **Clean-up:** when this lands, the 266 `IOT-WO-08` exceptions for these five images are **removed**, not extended. Their findings appear instead in the report-only section, and IOT-WO-08's weekly refresh becomes the standing staleness check.
5. **Upstream:** Twinfra deploys Cilium and CNPG in production, so this class doesn't apply to Twinfra's copies of them. The architect reports the class to Twinfra as information, not as a proposed change.

## Consequences

- The supply-chain gate stops treating harness release timing as shipped risk. About 266 entries leave the exception list, and the remaining exceptions describe only what EdgePulse ships (TB, Maven, and so on).
- Residual risk is accepted and stated. A vulnerable harness image could affect a developer machine or a CI runner while a rehearsal runs. Mitigations: the runners are disposable, the CI job has read-only permissions and no secrets, local clusters are owner-approved per run, and the staleness rule forces timely refreshes.
- This is a deliberate departure from ADR-0049's "dev and production alike" for one narrow, mechanically verified class, recorded here so it isn't an implicit gap.

## Alternatives considered

- **Renew 266 exceptions every 30 to 60 days.** Rejected: hundreds of approvals of the same reasoning, which empties the meaning of an exception.
- **Build EdgePulse's own kind node images, or rebuild Cilium.** Rejected: EdgePulse would own a Kubernetes distribution build, which is the opposite of ADR 0021.
- **Drop the harness or stop scanning it.** Rejected: the harness is how MS3 work is rehearsed before Twinfra hosting, and scanning keeps the KEV block and the staleness signal.
