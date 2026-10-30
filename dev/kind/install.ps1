param(
    [ValidateSet('RancherDesktop','DockerDesktop','CI')][string]$Engine,
    [switch]$OwnerChecksConfirmed
)
. "$PSScriptRoot/common.ps1"
Assert-Context
Assert-RehearsalActive
Assert-Engine $Engine -OwnerChecksConfirmed:$OwnerChecksConfirmed
Initialize-Tools
Assert-OwnedNode
$timer = [Diagnostics.Stopwatch]::StartNew()
# Sample afresh, never commit a UID, never request an SCC or privileged context.
$uid = Get-Random -Minimum 1000000000 -Maximum 2000000000
$chart = Join-Path $script:Repo 'charts/edgepulse-thingsboard'
$helmArgs = @('upgrade','--install','edgepulse',$chart,'--kube-context',$script:Context,'--kubeconfig',$env:KUBECONFIG,'--namespace','edgepulse-dev','--values',"$chart/values-kind.yaml",'--set',"tb.rehearsalUid=$uid",'--timeout','15m')
Invoke-Checked helm ($helmArgs + @('--set','tb.enabled=false','--set','bootstrap.enabled=false'))
Invoke-Kube @('wait','--for=condition=Ready','cluster/edgepulse-db','-n','edgepulse-dev','--timeout=600s')
Invoke-Checked helm ($helmArgs + @('--set','tb.enabled=false','--set','bootstrap.enabled=true'))
Invoke-Kube @('wait','--for=condition=complete','job/edgepulse-tb-initialize','-n','edgepulse-dev','--timeout=900s')
Invoke-Checked helm ($helmArgs + @('--set','tb.enabled=true','--set','bootstrap.enabled=false'))
Invoke-Kube @('rollout','status','deployment/edgepulse-tb','-n','edgepulse-dev','--timeout=900s')
Write-Output "install completed with a newly sampled non-root UID in $([math]::Round($timer.Elapsed.TotalSeconds,1)) seconds."
Write-Output 'Owner must change the initial system-administrator login through the local UI. Never record either value.'
