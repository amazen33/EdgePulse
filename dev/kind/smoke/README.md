# smoke

After approved installation, in the same isolated context:

```powershell
pwsh -NoProfile -File dev/kind/smoke.ps1 -Engine RancherDesktop -OwnerChecksConfirmed
```

Checks rollout status and HTTP 200 at /actuator/health through a port-forward
bound to 127.0.0.1:18080. Stops only its own port-forward child. No login,
credential read, model, migration or throughput operation occurs. The CI
kind-smoke uses only this health subset; it is not the full fact rehearsal.
Record the duration and HTTP status only. Remaining coverage is recorded
separately, after the corresponding owner approvals.
