param(
    [ValidateSet('RancherDesktop','DockerDesktop','CI')][string]$Engine,
    [switch]$OwnerChecksConfirmed
)
. "$PSScriptRoot/common.ps1"
Assert-Context
Assert-Engine $Engine -OwnerChecksConfirmed:$OwnerChecksConfirmed
Initialize-Tools
Assert-OwnedNode
Invoke-Checked kind @('delete','cluster','--name','edgepulse-dev','--kubeconfig',$env:KUBECONFIG)
