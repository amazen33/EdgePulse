param(
    [ValidateSet('RancherDesktop','DockerDesktop','CI')][string]$Engine,
    [switch]$OwnerChecksConfirmed
)
. "$PSScriptRoot/common.ps1"
Assert-Context
Assert-Engine $Engine -OwnerChecksConfirmed:$OwnerChecksConfirmed
Initialize-Tools
Assert-OwnedNode
$timer = [Diagnostics.Stopwatch]::StartNew()
Invoke-Kube @('rollout','status','deployment/edgepulse-tb','-n','edgepulse-dev','--timeout=60s')
$argsList = @('--kubeconfig',$env:KUBECONFIG,'--context',$script:Context,'-n','edgepulse-dev','port-forward','service/edgepulse-tb','18080:8080','--address','127.0.0.1')
$start = @{FilePath=(Get-Command kubectl).Source; ArgumentList=$argsList; PassThru=$true; RedirectStandardOutput=(Join-Path $script:State 'forward.out'); RedirectStandardError=(Join-Path $script:State 'forward.err')}
if ($IsWindows) { $start.WindowStyle = 'Hidden' }
$forward = Start-Process @start
try {
    $healthy = $false
    for ($attempt=0; $attempt -lt 15; $attempt++) {
        if ($forward.HasExited) { throw 'Local port-forward exited.' }
        try {
            $response = Invoke-WebRequest 'http://127.0.0.1:18080/actuator/health' -TimeoutSec 2
            if ($response.StatusCode -eq 200) { $healthy = $true; break }
        } catch { Start-Sleep -Seconds 2 }
    }
    if (-not $healthy) { throw 'Local health endpoint did not return 200.' }
    Write-Output "Local port-forward health: HTTP 200; duration $([math]::Round($timer.Elapsed.TotalSeconds,1)) seconds."
} finally {
    # Stop only the exact port-forward child started above.
    if (-not $forward.HasExited) { Stop-Process -Id $forward.Id }
}
