param(
    [ValidateSet('RancherDesktop','DockerDesktop','CI')][string]$Engine,
    [switch]$OwnerChecksConfirmed
)
. "$PSScriptRoot/common.ps1"
Assert-Context
Assert-Engine $Engine -OwnerChecksConfirmed:$OwnerChecksConfirmed
Initialize-Tools
$timer = [Diagnostics.Stopwatch]::StartNew()
$existing = & kind get clusters
if ($LASTEXITCODE -ne 0 -or $existing -contains 'edgepulse-dev') { throw 'Refusing to reuse an existing edgepulse-dev cluster.' }
Invoke-Checked kind @('create','cluster','--name','edgepulse-dev','--config',"$PSScriptRoot/cluster.yaml",'--image',$script:Pins.kind.node,'--kubeconfig',$env:KUBECONFIG,'--wait','180s')
Assert-OwnedNode
# Mount only inside this harness-owned node container; never on the laptop.
Invoke-Checked docker @('exec','edgepulse-dev-control-plane','sh','-ec','mountpoint -q /sys/fs/bpf || mount -t bpf bpf /sys/fs/bpf')
$nodeIp = (& docker inspect edgepulse-dev-control-plane --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}') -join ''
if ($LASTEXITCODE -ne 0 -or $nodeIp.Trim() -notmatch '^\d+\.\d+\.\d+\.\d+$') { throw 'Cannot determine the owned node IP.' }
Invoke-Checked helm @('upgrade','--install','cilium',(Join-Path $script:State 'cilium.tgz'),'--kube-context',$script:Context,'--kubeconfig',$env:KUBECONFIG,'--namespace','kube-system','--values',"$PSScriptRoot/cilium-values.yaml",'--set',"k8sServiceHost=$($nodeIp.Trim())",'--wait','--timeout','10m')
# Digest-pin the operator in the checksum-verified upstream manifest.
$operator = Get-Content -LiteralPath (Join-Path $script:State 'cnpg.yaml') -Raw
$oldImage = "ghcr.io/cloudnative-pg/cloudnative-pg:$($script:Pins.cnpg.version)"
if (-not $operator.Contains($oldImage)) { throw 'CNPG upstream manifest differs; refusing transformation.' }
$operator = $operator.Replace($oldImage, $script:Pins.cnpg.image)
$operatorPath = Join-Path $script:State 'cnpg-pinned.yaml'
[IO.File]::WriteAllText($operatorPath, $operator)
Invoke-Kube @('apply','--server-side','-f',$operatorPath)
Invoke-Kube @('rollout','status','deployment/cnpg-controller-manager','-n','cnpg-system','--timeout=300s')
Invoke-Kube @('apply','-f',"$PSScriptRoot/namespace.yaml")
Write-Output "up completed locally in $([math]::Round($timer.Elapsed.TotalSeconds,1)) seconds. Evidence level T only."
