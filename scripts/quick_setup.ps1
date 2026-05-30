# iMatu 3D Model Library - Quick Setup Script
# Simplified version to avoid encoding issues
# Usage: .\quick_setup.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  iMatu 3D Model Library Quick Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location G:\iMato

# Step 1: Check Python
Write-Host "[1/6] Checking Python..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match 'Python 3\.[9-9]|Python 3\.1[0-9]') {
        Write-Host " OK - $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host " WARNING - Version may not be compatible: $pythonVersion" -ForegroundColor Yellow
    }
} catch {
    Write-Host " FAILED - Python not found!" -ForegroundColor Red
    Write-Host "   Install from: https://python.org/downloads" -ForegroundColor Yellow
}

# Step 2: Check Node.js
Write-Host "[2/6] Checking Node.js..." -NoNewline
try {
    $nodeVersion = node --version 2>&1
    if ($nodeVersion -match 'v1[8-9]|v2[0-9]') {
        Write-Host " OK - $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host " WARNING - Version may not be compatible: $nodeVersion" -ForegroundColor Yellow
    }
} catch {
    Write-Host " FAILED - Node.js not found!" -ForegroundColor Red
    Write-Host "   Install from: https://nodejs.org" -ForegroundColor Yellow
}

# Step 3: Check npm
Write-Host "[3/6] Checking npm..." -NoNewline
try {
    $npmVersion = npm --version 2>&1
    Write-Host " OK - $npmVersion" -ForegroundColor Green
} catch {
    Write-Host " FAILED - npm not found!" -ForegroundColor Red
}

# Step 4: Check Blender (optional)
Write-Host "[4/6] Checking Blender (optional)..." -NoNewline
try {
    $blenderVersion = blender --version 2>&1 | Select-String "Blender" | Select-Object -First 1
    Write-Host " OK - $blenderVersion" -ForegroundColor Green
} catch {
    Write-Host " Not Found (optional)" -ForegroundColor Yellow
}

# Step 5: Install Python dependencies
Write-Host "[5/6] Installing Python dependencies..." -NoNewline
try {
    pip install requests --quiet
    Write-Host " OK - requests installed" -ForegroundColor Green
} catch {
    Write-Host " FAILED - Could not install requests" -ForegroundColor Red
}

# Step 6: Install Angular dependencies
Write-Host "[6/6] Installing Angular dependencies..." -NoNewline
try {
    npm install three @types/three --save --silent
    Write-Host " OK - three.js installed" -ForegroundColor Green
} catch {
    Write-Host " FAILED - Could not install three.js" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Creating directory structure..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$directories = @(
    "models\electronic_components",
    "models\electronic_components_lod",
    "data\kicad_models",
    "logs",
    "src\assets\models",
    "temp\conversions"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Running validation..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    python scripts\validate_3d_model_implementation.py
} catch {
    Write-Host "Validation failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review docs/LOCAL_DEPLOYMENT_GUIDE.md for detailed instructions"
Write-Host "  2. Generate model index: python scripts/kicad_model_scraper.py"
Write-Host "  3. Start Angular dev server: ng serve"
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

exit 0
