# Static tests: functions replace clients; no engine, kubeconfig or cluster read.
. "$PSScriptRoot/../common.ps1"
$originalConfig = $env:KUBECONFIG
$env:KUBECONFIG = Join-Path $script:State 'kubeconfig'
$global:MutationCalls = 0
function global:kubectl { $global:LASTEXITCODE = 0; 'unrelated-context' }
function global:docker { $global:MutationCalls++; throw 'Unexpected engine access' }
function global:kind { $global:MutationCalls++; throw 'Unexpected kind access' }
function global:helm { $global:MutationCalls++; throw 'Unexpected Helm access' }
try {
    foreach ($entry in @('up','install','smoke','down')) {
        $rejected = $false
        try { & "$PSScriptRoot/../$entry.ps1" -Engine CI }
        catch {
            if ($_.Exception.Message -cne 'Refusing: current context must be exactly kind-edgepulse-dev.') { throw }
            $rejected = $true
        }
        if (-not $rejected) { throw "$entry accepted the wrong context" }
        Write-Output "$entry refuses wrong context before engine access: PASS"
    }
    $env:KUBECONFIG = Join-Path $script:Repo 'unrelated-kubeconfig'
    $rejected = $false
    try { Assert-Context } catch { $rejected = $true }
    if (-not $rejected -or $global:MutationCalls -ne 0) { throw 'Isolation guard failed' }
    Write-Output 'Outside kubeconfig refused; engine calls: 0. All five guard checks PASS.'
    $env:KUBECONFIG = Join-Path $script:State 'kubeconfig'
    $global:MockServer = 'https://192.0.2.1:6443'
    function global:kubectl {
        $global:LASTEXITCODE = 0
        if ($args -contains 'current-context') { 'kind-edgepulse-dev' }
        elseif ($args -contains 'view') { $global:MockServer }
        else { $global:LastKubeArguments = @($args) }
    }
    $rejected = $false
    try { Assert-Context } catch {
        if ($_.Exception.Message -cne 'Refusing: isolated API endpoint must be loopback.') { throw }
        $rejected = $true
    }
    if (-not $rejected) { throw 'Remote endpoint accepted' }
    Write-Output 'Remote endpoint refused: PASS'
    $global:MockServer = 'https://127.0.0.1:1'
    Invoke-Kube @('get','pods','-n','edgepulse-dev')
    $expected = @('--kubeconfig',$env:KUBECONFIG,'--context','kind-edgepulse-dev','get','pods','-n','edgepulse-dev')
    if (($global:LastKubeArguments -join '|') -cne ($expected -join '|')) { throw 'kubectl arguments changed' }
    function global:kind { $global:LASTEXITCODE = 0; $global:LastKindArguments = @($args) }
    Invoke-Checked kind @('delete','cluster','--name','edgepulse-dev','--kubeconfig',$env:KUBECONFIG)
    $expected = @('delete','cluster','--name','edgepulse-dev','--kubeconfig',$env:KUBECONFIG)
    if (($global:LastKindArguments -join '|') -cne ($expected -join '|')) { throw 'kind arguments changed' }
    Write-Output 'Exact kubectl and kind command arguments preserved: two checks PASS (mock clients only).'
} finally {
    $env:KUBECONFIG = $originalConfig
    Remove-Item Function:/kubectl,Function:/docker,Function:/kind,Function:/helm
}
