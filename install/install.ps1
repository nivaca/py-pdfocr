<#
Installs py-pdfocr from this folder of its source, for this user, on
Windows, to run with Python (3.14 or later): no binaries are built.

    install\install.bat                     install, or update
    install\install.bat -Python C:\...\python.exe   with that Python
    install\install.bat -Uninstall          remove what it installed

(install.bat runs this script, install.ps1, with PowerShell.)

It makes a virtual environment of its own, %LOCALAPPDATA%\py-pdfocr\venv,
and installs py-pdfocr in it, with PyMuPDF from PyPI (so it needs internet
the first time); then it puts the command py-pdfocr in
%LOCALAPPDATA%\py-pdfocr\bin, and that folder on the user's PATH. Nothing
needs to be run as administrator, and nothing is put anywhere else; the
settings (%APPDATA%\py-pdfocr) and the models downloaded are never touched.
Tesseract is not installed by this (winget install UB-Mannheim.TesseractOCR).

py-pdfocr: Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
SPDX-License-Identifier: GPL-3.0-or-later (see LICENSE)
#>

param(
    [string]$Python = "",
    [switch]$Uninstall,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$Name = "py-pdfocr"
$Root = Split-Path -Parent $PSScriptRoot
$Data = Join-Path $env:LOCALAPPDATA $Name
$Venv = Join-Path $Data "venv"
$Bin = Join-Path $Data "bin"
$Command = Join-Path $Bin "$Name.cmd"

function Say($text) { Write-Host "==> $text" }

function Fail($text) {
    Write-Host "install.ps1: $text" -ForegroundColor Red
    exit 1
}

# ----------------------------------------------------------------- Python

# The full path of a Python 3.14 or later with venv and pip, run as COMMAND (an array:
# the program and its arguments, such as "py", "-3.14"), or $null.
function Test-Python([string[]]$command) {
    $program = $command[0]
    $arguments = @()
    if ($command.Count -gt 1) { $arguments = $command[1..($command.Count - 1)] }
    try {
        $out = & $program @arguments -c "import sys, venv, ensurepip; print(sys.executable) if sys.version_info >= (3, 14) else None" 2>$null
    } catch {
        return $null
    }
    if ($LASTEXITCODE -eq 0 -and $out) { return ($out | Select-Object -Last 1).Trim() }
    return $null
}

function Find-Python {
    $candidates = @(@("py", "-3.16"), @("py", "-3.15"), @("py", "-3.14"), @("python"), @("python3"))
    foreach ($candidate in $candidates) {
        if (Get-Command $candidate[0] -ErrorAction SilentlyContinue) {
            $found = Test-Python $candidate
            if ($found) { return $found }
        }
    }
    return $null
}

function No-Python {
    Write-Host "install.ps1: py-pdfocr needs Python 3.14 or later." -ForegroundColor Red
    Write-Host "  Install it from https://www.python.org/downloads/windows/ (the Python install"
    Write-Host "  manager, or the installer of 3.14), and run this again; or give it with -Python."
    exit 1
}

# ----------------------------------------------------------------- the PATH of the user

function Get-UserPath {
    $path = [Environment]::GetEnvironmentVariable("Path", "User")
    if (-not $path) { return @() }
    return @($path -split ";" | Where-Object { $_ })
}

function Set-UserPath([string[]]$parts) {
    [Environment]::SetEnvironmentVariable("Path", ($parts -join ";"), "User")
}

# ----------------------------------------------------------------- installing

function Install-PyPdfocr {
    if (-not ((Test-Path (Join-Path $Root "pyproject.toml")) -and (Test-Path (Join-Path $Root "src\py_pdfocr")))) {
        Fail "run it from the folder of py-pdfocr's source (cloned, or the zip unpacked)"
    }
    if ($Python) {
        $found = Test-Python @($Python)
        if (-not $found) { No-Python }
    } else {
        $found = Find-Python
        if (-not $found) { No-Python }
    }
    $version = & $found -c "import sys; print(sys.version.split()[0])"
    Say "Python: $found ($version)"
    Say "Making the environment: $Venv"
    New-Item -ItemType Directory -Force -Path $Data | Out-Null
    & $found -m venv --clear $Venv
    if ($LASTEXITCODE -ne 0) { Fail "the environment could not be made" }
    $venvPython = Join-Path $Venv "Scripts\python.exe"
    Say "Installing py-pdfocr and PyMuPDF in it"
    & $venvPython -m pip install --quiet --upgrade pip
    # (PyMuPDF alone, without what it brings for its analysis of layouts, onnxruntime, numpy and
    # others, some 200 MB that py-pdfocr never uses)
    & $venvPython -m pip install --quiet --no-deps "pymupdf>=1.26" "$Root"
    if ($LASTEXITCODE -ne 0) { Fail "py-pdfocr could not be installed (see the messages above)" }
    Say "Checking that it starts"
    & $venvPython -m py_pdfocr --version
    if ($LASTEXITCODE -ne 0) { Fail "py-pdfocr was installed, but doesn't start" }
    Say "Installed:"
    # (a .cmd of its own, not the folder Scripts on the PATH: that would put its python.exe and pip there too)
    New-Item -ItemType Directory -Force -Path $Bin | Out-Null
    $exe = Join-Path $Venv "Scripts\$Name.exe"
    Set-Content -Path $Command -Encoding ASCII -Value "@`"$exe`" %*"
    Write-Host "  the command: $Command"
    if ((Get-UserPath) -notcontains $Bin) {
        Set-UserPath ((Get-UserPath) + $Bin)
        Write-Host "  $Bin added to your PATH (open a new terminal to use it)"
    }
    $env:Path = "$Bin;$env:Path"
    $languages = & $exe languages 2>$null | Select-Object -First 1
    if ($languages -like "Tesseract *.*") {
        Write-Host "  tesseract: $languages"
    } else {
        Write-Host ""
        Write-Host "Tesseract is not installed, and py-pdfocr needs it to read. Install it with"
        Write-Host "  winget install UB-Mannheim.TesseractOCR"
        Write-Host "and choose the languages of your documents in its installer (or later:"
        Write-Host "py-pdfocr download spa ...)."
    }
    Write-Host ""
    Write-Host "Run it with: py-pdfocr file.pdf (see py-pdfocr --help). To update it, run this"
    Write-Host "again after updating the source; to remove it, install\install.bat -Uninstall."
}

function Uninstall-PyPdfocr {
    Say "Removing py-pdfocr"
    if (Test-Path $Bin) {
        Remove-Item -Recurse -Force $Bin
        Write-Host "  $Bin"
    }
    if ((Get-UserPath) -contains $Bin) {
        Set-UserPath (Get-UserPath | Where-Object { $_ -ne $Bin })
        Write-Host "  $Bin, from your PATH"
    }
    if (Test-Path $Venv) {
        Remove-Item -Recurse -Force $Venv
        Write-Host "  $Venv"
    }
    # (the models downloaded may be in the same folder: then it stays)
    if ((Test-Path $Data) -and -not (Get-ChildItem $Data -Force)) { Remove-Item -Force $Data }
    Write-Host "The settings and the models downloaded were kept."
}

if ($Help) {
    Get-Content $PSCommandPath | Select-Object -Skip 1 -First 19
    exit 0
}
if ($Uninstall) { Uninstall-PyPdfocr } else { Install-PyPdfocr }
