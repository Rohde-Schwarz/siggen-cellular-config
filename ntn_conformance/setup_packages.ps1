<#
.SYNOPSIS
    Setup uv virtual environment and install all packages.
.USAGE
    .\setup_packages.ps1
#>

$ErrorActionPreference = "Stop"

# Deactivate any active venv first
if (Test-Path Function:\deactivate) { deactivate }

$venvDir = Join-Path $PWD ".venv"

# 1. Install uv
Write-Host "`n>>> pip install uv"
python -m pip install uv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 2. Create virtual environment (--clear overwrites existing .venv)
Write-Host "`n>>> uv venv --python 3.12 --clear"
python -m uv venv --python 3.12 --clear
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 3. Determine venv python
$venvPython = Join-Path (Join-Path $venvDir "Scripts") "python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Error: venv python not found at $venvPython"
    exit 1
}

# 4. Install packages
Write-Host "`n>>> uv pip install requirements"
python -m uv pip install --python $venvPython -r requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n>>> uv pip install -e .[dev]"
python -m uv pip install --python $venvPython -e ".[dev]"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 5. Install Git hooks into .githooks/ so any IDE that calls git picks them up
$preCommit = Join-Path (Join-Path $venvDir "Scripts") "pre-commit.exe"
$githooksDir = Join-Path $PWD ".githooks"

# pre-commit refuses to install when core.hooksPath is set; install to .git/hooks then copy
if (git config --local --get core.hooksPath 2>$null) {
    Write-Host "`n>>> git config --unset --local core.hooksPath"
    git config --unset --local core.hooksPath
}
Write-Host "`n>>> pre-commit install -t pre-commit -t pre-push"
& $preCommit install -t pre-commit -t pre-push
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

New-Item -ItemType Directory -Force -Path $githooksDir | Out-Null
Copy-Item -Force (Join-Path $PWD ".git\hooks\pre-commit") (Join-Path $githooksDir "pre-commit")
Copy-Item -Force (Join-Path $PWD ".git\hooks\pre-push") (Join-Path $githooksDir "pre-push")

Write-Host "`n>>> git config --local core.hooksPath .githooks"
git config --local core.hooksPath .githooks
Write-Host "`n>>> pre-commit install-hooks"
& $preCommit install-hooks
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 6. Activate the virtual environment
$activateScript = Join-Path (Join-Path $venvDir "Scripts") "Activate.ps1"
Write-Host "`n✅ Setup complete. Activating virtual environment..."
& $activateScript
