# Starts LED Studio on Windows: backend (FastAPI) + frontend (Vite) and opens the browser.
# First run installs the Python venv and npm packages. Ctrl+C stops both servers.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Pick up tools installed after this shell was opened (winget installs only update the registry).
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
    [Environment]::GetEnvironmentVariable("Path", "User")
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

foreach ($tool in "python", "npm") {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Error "'$tool' is not installed or not on PATH. Install Python 3.13+ and Node.js 24+ first."
    }
}

if (-not (Test-Path $python)) {
    Write-Host "Creating Python environment..."
    python -m venv (Join-Path $backend ".venv")
    & $python -m pip install --quiet --upgrade pip
    & $python -m pip install --quiet -e "$backend[dev]"
}

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "Installing frontend packages..."
    npm --prefix $frontend install --silent
}

Write-Host "Starting backend on http://127.0.0.1:8765 ..."
$server = Start-Process -FilePath $python -ArgumentList "-m", "led_studio.main" `
    -WorkingDirectory $backend -NoNewWindow -PassThru

try {
    Start-Sleep -Seconds 2
    if ($server.HasExited) { Write-Error "Backend failed to start (exit code $($server.ExitCode))." }
    Start-Process "http://localhost:5173"
    Write-Host "Frontend on http://localhost:5173 - press Ctrl+C to stop everything."
    npm --prefix $frontend run dev
}
finally {
    if (-not $server.HasExited) { Stop-Process -Id $server.Id -Force }
}
