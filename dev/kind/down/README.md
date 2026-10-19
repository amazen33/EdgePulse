# down

Ask for separate owner approval. This removes the local rehearsal and its
database. Preserve only redacted counts/digests and approved evidence first.

```powershell
pwsh -NoProfile -File dev/kind/down.ps1 -Engine RancherDesktop -OwnerChecksConfirmed
```

Requires the isolated current context kind-edgepulse-dev, the confirmed sole
engine, and the expected kind ownership label on edgepulse-dev-control-plane.
The only deletion command is kind delete cluster --name edgepulse-dev with
the isolated kubeconfig. No context switch, other cluster cleanup, image prune
or host/distro operation is performed. Never delete state to bypass a guard.
