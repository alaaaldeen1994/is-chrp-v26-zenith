# ============================================================================
# NEUROS-X → Zenith v31 Installer (Windows PowerShell version)
# ============================================================================
# Run this script from the ROOT of your is-chrp-v26-zenith repo.
#
# Usage (right-click → "Run with PowerShell") or in PowerShell:
#   cd C:\path\to\is-chrp-v26-zenith
#   powershell -ExecutionPolicy Bypass -File install_neuros_x.ps1
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "  NEUROS-X -> Zenith v31 Installer (Neural Age Clock)" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host ""

# --- 1. Verify we're in the Zenith repo root ---
if (-not (Test-Path "bridge_server.py")) {
    Write-Host "ERROR: bridge_server.py not found in current directory." -ForegroundColor Red
    Write-Host "Run this script from the ROOT of your is-chrp-v26-zenith repo." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Zenith repo detected (found bridge_server.py)" -ForegroundColor Green
Write-Host ""

# --- 2. Locate the integration source ---
# The script lives INSIDE neuros_integration/, so source files are in the same dir
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = $ScriptDir

if (-not (Test-Path "$SrcDir\services\neuros_substrate_service.py")) {
    Write-Host "ERROR: integration files not found next to this script." -ForegroundColor Red
    Write-Host "Expected: $SrcDir\services\neuros_substrate_service.py" -ForegroundColor Yellow
    Write-Host "Make sure you're running the script from inside the neuros_integration folder." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Integration source: $SrcDir" -ForegroundColor Green
Write-Host ""

# --- 3. Create directories if missing ---
$dirs = @("services", "routers", "database", "patches", "training", "models")
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
    }
}

# --- 4. Copy files ---
Write-Host "Copying files..." -ForegroundColor Blue
Write-Host ""

$filesToCopy = @(
    @{ src = "$SrcDir\services\neuros_substrate_service.py"; dst = "services\" },
    @{ src = "$SrcDir\services\neural_age_clock.py";         dst = "services\" },
    @{ src = "$SrcDir\routers\neural_router.py";             dst = "routers\" },
    @{ src = "$SrcDir\database\neural_models.py";            dst = "database\" },
    @{ src = "$SrcDir\patches\horvath_patch.py";             dst = "patches\" },
    @{ src = "$SrcDir\training\Zenith_v31_neural_cardiac_Training.ipynb"; dst = "training\" }
)

foreach ($f in $filesToCopy) {
    $fileName = Split-Path -Leaf $f.src
    $destPath = Join-Path $f.dst $fileName
    Copy-Item -Path $f.src -Destination $destPath -Force
    Write-Host "  [OK] $destPath" -ForegroundColor Green
}

# Copy README
Copy-Item -Path "$SrcDir\README_INTEGRATION.md" -Destination "NEUROS_X_INTEGRATION.md" -Force
Write-Host "  [OK] NEUROS_X_INTEGRATION.md" -ForegroundColor Green

Write-Host ""
Write-Host "[OK] All files copied." -ForegroundColor Green
Write-Host ""

# --- 5. Verify Python syntax ---
Write-Host "Verifying Python syntax..." -ForegroundColor Blue
$pyFiles = @(
    "services\neuros_substrate_service.py",
    "services\neural_age_clock.py",
    "routers\neural_router.py",
    "database\neural_models.py"
)
$pythonFound = $false
try {
    $null = Get-Command python -ErrorAction Stop
    $pythonFound = $true
} catch {
    try {
        $null = Get-Command python3 -ErrorAction Stop
        $pythonFound = $true
    } catch {
        Write-Host "  (python not found — skipping syntax check)" -ForegroundColor Yellow
    }
}

if ($pythonFound) {
    foreach ($f in $pyFiles) {
        $result = & python -c "import ast; ast.parse(open('$f').read())" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] $f" -ForegroundColor Green
        } else {
            Write-Host "  [!] $f (syntax issue)" -ForegroundColor Yellow
        }
    }
}
Write-Host ""

# --- 6. Show manual steps ---
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "  MANUAL STEPS (2 lines to add)" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "STEP 1: Add the router to bridge_server.py" -ForegroundColor Yellow
Write-Host "  Find the line where you include the boltz_router, and add AFTER it:"
Write-Host ""
Write-Host "  from routers.neural_router import router as neural_router" -ForegroundColor Green
Write-Host "  app.include_router(neural_router)" -ForegroundColor Green
Write-Host ""
Write-Host "STEP 2: Add DualAgeReport to services\horvath_clock.py" -ForegroundColor Yellow
Write-Host "  Open patches\horvath_patch.py and copy the DualAgeReport class"
Write-Host "  to the bottom of services\horvath_clock.py"
Write-Host ""
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "  NEXT STEPS" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Run the Colab notebook: training\Zenith_v31_neural_cardiac_Training.ipynb"
Write-Host "     (calibrates the clock on your 486k cell data)"
Write-Host ""
Write-Host "  2. Start your server: python bridge_server.py"
Write-Host ""
Write-Host "  3. Test the new endpoints:"
Write-Host "     curl http://localhost:8000/api/v1/neural/health" -ForegroundColor Green
Write-Host "     curl http://localhost:8000/api/v1/neural/panel" -ForegroundColor Green
Write-Host ""
Write-Host "  4. Read NEUROS_X_INTEGRATION.md for full docs + marketing copy."
Write-Host ""
Write-Host "[DONE] Zenith v31 is ready." -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to exit"
