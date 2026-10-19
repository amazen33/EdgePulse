# ThingsBoard CE chart

IOT-WO-04 Amendment 3 test packaging, evidence level T only. No hosting,
OpenShift support, migration readiness or milestone acceptance is established.
This chart renders only namespaced Deployment/Job, ClusterIP Service and CNPG
Cluster resources. The harness supplies the namespace, policies and operators.
Nothing uses the frozen deploy tree.

The default and `values-twinfra.yaml` describe the future Twinfra profile;
`values-openshift.yaml` leaves UID/GID assignment to SCC and storage to the
platform default; `values-kind.yaml` uses `standard` storage locally. The local
harness samples a new non-root UID per installation; no committed profile fixes
an application UID or GID. Restricted-v2 static checks also cover initialization.
Live arbitrary-UID compatibility remains unverified until the owner-approved run.
An upstream-image incompatibility stops the run for the minimal permissions fix
specified by the amendment; do not add a privileged init container or fixed UID.

TB is `tb-node` monolith 4.3.1.6, in-memory queue, one replica, at most 4 GiB.
Its external CNPG PostgreSQL 18 instance is limited to 2 GiB. The [official TB
4.3.1.6 installation guide](https://thingsboard.io/docs/installation/ubuntu/)
uses PostgreSQL 18. Restarts lose in-flight in-memory messages. Memory limits do
not prove sufficient capacity. Both images are digest-pinned in values.yaml and
[pins.json](../../dev/kind/pins.json). Sources and licences are in the
[harness README](../../dev/kind/README.md).

CNPG generates `edgepulse-db-app`; username and password are referenced only
through Secret key selectors. No values are printed by the scripts. Initialization
uses `LOAD_DEMO=false`; change the initial system-administrator login locally
after install without recording either value. Logs and transient application
state use an emptyDir; the image root stays read-only. No host path is mounted.

The [install script](../../dev/kind/install.ps1) first creates the database,
then waits for schema initialization, then enables the application. Do not
rerun initialization against an existing database. No upgrade, authentication,
restore or default-login automation is hidden in the health smoke test.

For static checks, run `python dev/kind/tests/render_check.py --helm <helm-path>`
and `pwsh -NoProfile -File dev/kind/tests/guards.ps1` from the repository root.
No Kubernetes API is called by these checks. Live access uses loopback
port-forward only. No Ingress, Route, MQTT/LAN exposure or Argo CD is installed.
