# up

Owner approval and all first-up confirmations in the [harness README](../README.md)
are required. From the repository root, after preparing the isolated context:

```powershell
pwsh -NoProfile -File dev/kind/up.ps1 -Engine RancherDesktop -OwnerChecksConfirmed
```

Use `-Engine DockerDesktop` only after its separate owner confirmations. No
engine is started or reconfigured. Refuses an existing edgepulse-dev cluster.
Creates exactly one control-plane node, Cilium and the pinned CNPG operator;
then applies the isolated namespace baseline. No ThingsBoard install occurs.
Record the output duration, not client configuration or generated Secrets.
On failure, retain state and report; down still needs separate approval.
