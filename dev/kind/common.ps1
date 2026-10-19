Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:Repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$script:State = Join-Path $script:Repo 'target/kind'
$script:Pins = Get-Content (Join-Path $PSScriptRoot 'pins.json') -Raw | ConvertFrom-Json
$script:Context = 'kind-edgepulse-dev'

function Assert-Context {
    $expected = Join-Path $script:State 'kubeconfig'
    if (-not $env:KUBECONFIG -or [IO.Path]::GetFullPath($env:KUBECONFIG) -cne $expected) {
        throw 'Refusing: KUBECONFIG must be the isolated repository target/kind/kubeconfig.'
    }
    $current = & kubectl --kubeconfig $expected config current-context
    if ($LASTEXITCODE -ne 0 -or ($current -join '').Trim() -cne $script:Context) {
        throw 'Refusing: current context must be exactly kind-edgepulse-dev.'
    }
    $server = (& kubectl --kubeconfig $expected config view --minify '-o=jsonpath={.clusters[0].cluster.server}') -join ''
    if ($LASTEXITCODE -ne 0 -or $server -cnotmatch '^https://127\.0\.0\.1:[0-9]+$') {
        throw 'Refusing: isolated API endpoint must be loopback.'
    }
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory,Position=0)][string]$Command,
        [Parameter(Mandatory,Position=1,ValueFromRemainingArguments)][string[]]$Arguments
    )
    Assert-Context
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command failed (exit $LASTEXITCODE); no automatic retry or cleanup." }
}

function Invoke-Kube {
    param([Parameter(Mandatory,Position=0,ValueFromRemainingArguments)][string[]]$Arguments)
    Invoke-Checked kubectl (@('--kubeconfig', $env:KUBECONFIG, '--context', $script:Context) + $Arguments)
}

function Assert-Engine([string]$Engine, [switch]$OwnerChecksConfirmed) {
    if ($Engine -eq 'CI') {
        if ($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_ENVIRONMENT -cne 'github-hosted') {
            throw 'CI engine selection is limited to a disposable GitHub-hosted runner.'
        }
        $expectedContext = 'default'
    } else {
        if (-not $IsWindows -or -not $OwnerChecksConfirmed) {
            throw 'Owner engine, isolated distros, memory, Kubernetes-off and licence confirmations required.'
        }
        $rancher = @(Get-Process -Name 'Rancher Desktop' -ErrorAction SilentlyContinue)
        $desktop = @(Get-Process -Name 'Docker Desktop','com.docker.backend' -ErrorAction SilentlyContinue)
        $podman = @(Get-Process -Name 'Podman Desktop','podman-desktop' -ErrorAction SilentlyContinue)
        if ($podman.Count -gt 0) { throw 'Refusing: an additional desktop engine is running.' }
        if ($rancher.Count -gt 0 -and $desktop.Count -gt 0) { throw 'Refusing: two desktop engines are running.' }
        if ($Engine -eq 'RancherDesktop') {
            if ($rancher.Count -eq 0 -or $desktop.Count -gt 0) { throw 'Rancher Desktop must be the only running engine.' }
            $settings = & rdctl list-settings | ConvertFrom-Json
            if ($LASTEXITCODE -ne 0 -or $settings.containerEngine.name -cne 'moby' -or $settings.kubernetes.enabled) {
                throw 'Rancher Desktop requires moby and built-in Kubernetes off.'
            }
            $expectedContext = 'rancher-desktop'
        } elseif ($Engine -eq 'DockerDesktop') {
            if ($desktop.Count -eq 0 -or $rancher.Count -gt 0) { throw 'Docker Desktop must be the only running engine.' }
            $settingsPath = Join-Path $env:APPDATA 'Docker/settings-store.json'
            if (-not (Test-Path -LiteralPath $settingsPath)) { throw 'Cannot establish Docker Desktop Kubernetes setting; refusing.' }
            $settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
            if ($settings.kubernetesEnabled -ne $false) { throw 'Docker Desktop built-in Kubernetes must be off.' }
            $expectedContext = 'desktop-linux'
        } else { throw 'Select RancherDesktop or DockerDesktop.' }
    }
    $current = (& docker context show) -join ''
    if ($LASTEXITCODE -ne 0 -or $current.Trim() -cne $expectedContext) { throw 'Refusing: unexpected Docker context.' }
    $endpoint = (& docker context inspect $expectedContext --format '{{.Endpoints.docker.Host}}') -join ''
    if ($LASTEXITCODE -ne 0 -or $endpoint -notmatch '^(npipe://|unix://)') { throw 'Refusing: engine endpoint must be local.' }
    $memory = (& docker info --format '{{.MemTotal}}') -join ''
    if ($LASTEXITCODE -ne 0 -or [long]$memory -lt 9GB) { throw 'Refusing: approximately 10 GiB of engine memory required.' }
    $env:KIND_EXPERIMENTAL_PROVIDER = 'docker'
}

function Get-PinnedFile([string]$Url, [string]$Path, [string]$Sha256) {
    if (-not (Test-Path -LiteralPath $Path)) { Invoke-WebRequest -Uri $Url -OutFile $Path }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Sha256) {
        throw "Public artifact checksum mismatch: $([IO.Path]::GetFileName($Path))"
    }
}

function Initialize-Tools {
    Assert-Context
    New-Item -ItemType Directory -Force -Path $script:State | Out-Null
    $platform = if ($IsWindows) { 'windows' } else { 'linux' }
    $suffix = if ($IsWindows) { '.exe' } else { '' }
    $shaProperty = $platform + 'Sha256'
    Get-PinnedFile "https://github.com/kubernetes-sigs/kind/releases/download/v$($script:Pins.kind.version)/kind-$platform-amd64" (Join-Path $script:State "kind$suffix") $script:Pins.kind.$shaProperty
    Get-PinnedFile "https://dl.k8s.io/release/v$($script:Pins.kubectl.version)/bin/$platform/amd64/kubectl$suffix" (Join-Path $script:State "kubectl$suffix") $script:Pins.kubectl.$shaProperty
    $archive = if ($IsWindows) { 'zip' } else { 'tar.gz' }
    $helmArchive = Join-Path $script:State "helm.$archive"
    Get-PinnedFile "https://get.helm.sh/helm-v$($script:Pins.helm.version)-$platform-amd64.$archive" $helmArchive $script:Pins.helm.$shaProperty
    if ($IsWindows) { Expand-Archive -LiteralPath $helmArchive -DestinationPath $script:State -Force }
    else { & tar -xzf $helmArchive -C $script:State; if ($LASTEXITCODE -ne 0) { throw 'Helm extraction failed.' } }
    Copy-Item -LiteralPath (Join-Path $script:State "$platform-amd64/helm$suffix") -Destination (Join-Path $script:State "helm$suffix") -Force
    if (-not $IsWindows) { & chmod u+x (Join-Path $script:State 'kind') (Join-Path $script:State 'kubectl') (Join-Path $script:State 'helm') }
    $env:PATH = "$script:State$([IO.Path]::PathSeparator)$env:PATH"
    Get-PinnedFile "https://helm.cilium.io/cilium-$($script:Pins.cilium.version).tgz" (Join-Path $script:State 'cilium.tgz') $script:Pins.cilium.chartSha256
    Get-PinnedFile "https://github.com/cloudnative-pg/cloudnative-pg/releases/download/v$($script:Pins.cnpg.version)/cnpg-$($script:Pins.cnpg.version).yaml" (Join-Path $script:State 'cnpg.yaml') $script:Pins.cnpg.manifestSha256
}

function Assert-OwnedNode {
    Assert-Context
    $node = (& docker inspect edgepulse-dev-control-plane --format '{{index .Config.Labels "io.x-k8s.kind.cluster"}}') -join ''
    if ($LASTEXITCODE -ne 0 -or $node.Trim() -cne 'edgepulse-dev') { throw 'Refusing: node is not owned by kind cluster edgepulse-dev.' }
    $mapping = @(& docker port edgepulse-dev-control-plane 6443/tcp)
    if ($LASTEXITCODE -ne 0 -or $mapping.Count -ne 1) { throw 'Refusing: unexpected owned-node API mapping.' }
    $server = (& kubectl --kubeconfig $env:KUBECONFIG config view --minify '-o=jsonpath={.clusters[0].cluster.server}') -join ''
    if ($LASTEXITCODE -ne 0 -or $server -cne "https://$($mapping[0].Trim())") { throw 'Refusing: kubeconfig does not point at the owned kind node.' }
}
