$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
& python -X utf8 -B (Join-Path $PSScriptRoot 'lote.py') @args
exit $LASTEXITCODE
