# Layer 4 -- `deploy/04-apps` (planned, no Helm charts exist)

Application releases: one Helm chart per service, deployed by a GitOps
controller (Argo CD is the currently named controller -- ADR 0011
Decision 3, PF-C step C7). For a full-stack profile, Layers 0-3 must be
installed first. For an `applications-only` cloud profile, those layers
must already be supplied by the environment operator and pass the external
dependency readiness checks; this repository must not install them.

**Status: planned.** As of this commit the repository contains **no Helm
chart** (no `Chart.yaml` anywhere), no values files, no Argo CD
`Application`, and no container image build. Do not describe any service as
deployable until those exist and pass the checks below.

## Rules for when charts are added

- One chart per service, in the service's own tree or under this
  directory; no shared "umbrella" chart carrying business logic (ADR 0013).
- Security context compatible with the restricted Pod Security Standard and
  with OpenShift's restricted SCC (non-root, arbitrary UID) from the first
  chart (`docs/track-c-execution-plan.md`, C7).
- No secret values in charts or values files; only references to the
  selected secrets backend (see the vault profile in `deploy/profiles/`).
- Versions and images pinned; the controller syncs from Git only -- no
  imperative `helm install` against shared environments.

## Acceptance criteria (PF-C C7)

1. `helm lint` and `helm template | kubeconform -strict` pass in CI for every
   chart.
2. The chart installs on a disposable CI cluster (k3d) and the same chart
   renders unchanged with EKS/AKS/GKE values files.
3. An Argo CD `Application` (or the approved controller's equivalent)
   deploys it to the lab cluster from Git, and rollback to the previous
   revision is rehearsed.
