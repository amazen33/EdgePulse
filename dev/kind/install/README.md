# install

Request separate owner approval after successful up. Keep the same engine and
isolated context. Example for the confirmed preferred engine:

```powershell
pwsh -NoProfile -File dev/kind/install.ps1 -Engine RancherDesktop -OwnerChecksConfirmed
```

Installs the CNPG Cluster, waits for Ready, initializes a new TB database and
starts TB under a newly sampled UID. Credentials stay in CNPG's generated
Secret. Do not rerun on an initialized database. Never print Secret YAML,
client environment, application logs or a default login. Through a loopback
port-forward, the owner changes the initial system-administrator login without
recording either value. Record durations and status only. Any image arbitrary-UID
failure stops for the minimal permissions fix; never relax the security context.
