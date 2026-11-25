$ErrorActionPreference = "Stop"
$ScriptPath = Join-Path $PSScriptRoot "app_publish.py"

$Candidates = @()
if (Get-Command py -ErrorAction SilentlyContinue) { $Candidates += ,@("py", "-3") }
if (Get-Command python -ErrorAction SilentlyContinue) { $Candidates += ,@("python") }
if (Get-Command python3 -ErrorAction SilentlyContinue) { $Candidates += ,@("python3") }

foreach ($Candidate in $Candidates) {
    $Exe = $Candidate[0]
    $Prefix = @($Candidate | Select-Object -Skip 1)
    & $Exe @Prefix -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)"
    if ($LASTEXITCODE -eq 0) {
        & $Exe @Prefix $ScriptPath @args
        exit $LASTEXITCODE
    }
}

[Console]::Error.WriteLine('{"ok":false,"error":"未找到 Python 3.9+，请先安装或升级 Python 3"}')
exit 127
