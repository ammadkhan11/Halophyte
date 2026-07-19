$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$BackendPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

if (-not (Test-Path $BackendPython)) {
    $BackendPython = "python"
}

$backend = Start-Process `
    -FilePath $BackendPython `
    -ArgumentList @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $BackendDir `
    -WindowStyle Hidden `
    -PassThru

try {
    npm.cmd run dev
}
finally {
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
}
