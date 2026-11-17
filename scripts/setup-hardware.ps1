param([string]$Python310 = "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe")
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (!(Test-Path -LiteralPath $Python310)) { throw "Provide -Python310 with the full path to Python 3.10 x64" }
& $Python310 -c "import sys,struct; assert sys.version_info[:2] == (3,10) and struct.calcsize('P') == 8, 'Python 3.10 x64 required'"
if ($LASTEXITCODE) { throw "Unsupported Python interpreter" }
& $Python310 -m venv .venv-hardware
if ($LASTEXITCODE) { throw "Cannot create hardware environment" }
& ".\.venv-hardware\Scripts\python.exe" -m pip install -r backend\requirements-lock-py310.txt
if ($LASTEXITCODE) { throw "Hardware dependency installation failed" }
& ".\.venv-hardware\Scripts\python.exe" -m backend.hardware_check

