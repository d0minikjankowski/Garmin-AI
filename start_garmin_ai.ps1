param([switch]$Configure, [switch]$Force, [switch]$Recovery)
$ErrorActionPreference = 'Stop'
if ($Recovery -and $Force) { throw 'Uzyj -Recovery lub -Force osobno.' }
$secretPath = Join-Path $PSScriptRoot '.secrets.clixml'
$python = 'C:\Users\domin\Garmin-AI\.venv\Scripts\python.exe'
if ($Configure -or -not (Test-Path -LiteralPath $secretPath)) {
    $keys = @{
        OPENAI_API_KEY = Read-Host 'Klucz OpenAI (wpis ukryty)' -AsSecureString
        GARMIN_PERSONAL_API_KEY = Read-Host 'Klucz Garmin Personal API (wpis ukryty)' -AsSecureString
    }
    $keys | Export-Clixml -LiteralPath $secretPath
    Write-Host 'Klucze zapisane z szyfrowaniem Windows dla tego konta.'
    if ($Configure) { exit 0 }
}
$previousOpenAI = $env:OPENAI_API_KEY
$previousGarmin = $env:GARMIN_PERSONAL_API_KEY
try {
    $keys = Import-Clixml -LiteralPath $secretPath
    $keyNames = @('GARMIN_PERSONAL_API_KEY')
    if (-not $Recovery) { $keyNames += 'OPENAI_API_KEY' }
    foreach ($name in $keyNames) {
        if ($keys[$name] -isnot [System.Security.SecureString]) { throw 'Nieprawidlowy plik kluczy.' }
        $credential = New-Object System.Net.NetworkCredential('', $keys[$name])
        [Environment]::SetEnvironmentVariable($name, $credential.Password, 'Process')
    }
    $pythonArgs = @((Join-Path $PSScriptRoot 'garmin_ai.py'))
    if ($Recovery) {
        $pythonArgs = @((Join-Path $PSScriptRoot 'recovery_probe.py'), '--end-date', (Get-Date -Format 'yyyy-MM-dd'))
    }
    if ($Force) { $pythonArgs += '--force' }
    & $python @pythonArgs
    $result = $LASTEXITCODE
} finally {
    $env:OPENAI_API_KEY = $previousOpenAI
    $env:GARMIN_PERSONAL_API_KEY = $previousGarmin
    $credential = $null
    $keys = $null
}
exit $result
