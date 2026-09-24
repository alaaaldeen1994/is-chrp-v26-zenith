#!/usr/bin/env bash
# ============================================================================
# NEUROS-X → Zenith v31 Installer
# ============================================================================
# Run this script from the ROOT of your is-chrp-v26-zenith repo.
#
# It copies the Neural Age Clock integration files to the correct locations
# and shows you the exact lines to add to bridge_server.py + horvath_clock.py.
#
# Usage:
#   cd /path/to/is-chrp-v26-zenith
#   bash install_neuros_x.sh
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  NEUROS-X → Zenith v31 Installer (Neural Age Clock)         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# --- 1. Verify we're in the Zenith repo root ---
if [ ! -f "bridge_server.py" ]; then
    echo -e "${RED}ERROR: bridge_server.py not found in current directory.${NC}"
    echo -e "${YELLOW}Run this script from the ROOT of your is-chrp-v26-zenith repo.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Zenith repo detected (found bridge_server.py)${NC}"
echo ""

# --- 2. Locate the integration source ---
# The script lives INSIDE neuros_integration/, so source files are in the same dir
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR"

if [ ! -f "$SRC_DIR/services/neuros_substrate_service.py" ]; then
    echo -e "${RED}ERROR: integration files not found next to this script.${NC}"
    echo -e "${YELLOW}Expected: $SRC_DIR/services/neuros_substrate_service.py${NC}"
    echo -e "${YELLOW}Make sure you're running the script from inside the extracted neuros_integration/ folder.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Integration source: $SRC_DIR${NC}"
echo ""

# --- 3. Create directories if missing ---
mkdir -p services routers database patches training models

# --- 4. Copy files ---
echo -e "${BLUE}Copying files...${NC}"
echo ""

# services/
cp -v "$SRC_DIR/services/neuros_substrate_service.py" services/
cp -v "$SRC_DIR/services/neural_age_clock.py" services/

# routers/
cp -v "$SRC_DIR/routers/neural_router.py" routers/

# database/
cp -v "$SRC_DIR/database/neural_models.py" database/

# patches/
cp -v "$SRC_DIR/patches/horvath_patch.py" patches/

# training notebook
cp -v "$SRC_DIR/training/Zenith_v31_neural_cardiac_Training.ipynb" training/

# README
cp -v "$SRC_DIR/README_INTEGRATION.md" ./NEUROS_X_INTEGRATION.md

echo ""
echo -e "${GREEN}✓ All files copied.${NC}"
echo ""

# --- 5. Verify Python syntax ---
echo -e "${BLUE}Verifying Python syntax...${NC}"
for f in services/neuros_substrate_service.py services/neural_age_clock.py routers/neural_router.py database/neural_models.py; do
    if python3 -c "import ast; ast.parse(open('$f').read())" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $f"
    else
        echo -e "  ${YELLOW}⚠${NC} $f (syntax check skipped — python3 not available or syntax issue)"
    fi
done
echo ""

# --- 6. Show manual steps ---
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  MANUAL STEPS (2 lines to add)                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}STEP 1: Add the router to bridge_server.py${NC}"
echo -e "  Find the line where you include the boltz_router, and add AFTER it:"
echo ""
echo -e "  ${GREEN}from routers.neural_router import router as neural_router${NC}"
echo -e "  ${GREEN}app.include_router(neural_router)${NC}"
echo ""
echo -e "${YELLOW}STEP 2: Add DualAgeReport to services/horvath_clock.py${NC}"
echo -e "  Open patches/horvath_patch.py and copy the DualAgeReport class"
echo -e "  to the bottom of services/horvath_clock.py"
echo ""
echo -e "  (Optional) Add this endpoint to bridge_server.py:"
echo -e "  ${GREEN}@app.post(\"/api/v1/horvath/dual-age\")${NC}"
echo -e "  ${GREEN}async def dual_age_endpoint(request: Request):${NC}"
echo -e "  ${GREEN}    body = await request.json()${NC}"
echo -e "  ${GREEN}    from services.horvath_clock import HorvathClock, DualAgeReport${NC}"
echo -e "  ${GREEN}    horvath = HorvathClock()${NC}"
echo -e "  ${GREEN}    return await DualAgeReport.assess(...)${NC}"
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  NEXT STEPS                                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  1. Run the Colab notebook: training/Zenith_v31_neural_cardiac_Training.ipynb"
echo -e "     (calibrates the clock on your 486k cell data)"
echo -e ""
echo -e "  2. Start your server: python bridge_server.py"
echo -e ""
echo -e "  3. Test the new endpoints:"
echo -e "     ${GREEN}curl http://localhost:8000/api/v1/neural/health${NC}"
echo -e "     ${GREEN}curl http://localhost:8000/api/v1/neural/panel${NC}"
echo -e "     ${GREEN}curl -X POST http://localhost:8000/api/v1/neural/dual-age \\${NC}"
echo -e "       ${GREEN}-H 'Content-Type: application/json' \\${NC}"
echo -e "       ${GREEN}-d '{\"expression\":{\"CHAT\":3.2},\"horvath_age\":52.3,\"chronological_age\":55}'${NC}"
echo ""
echo -e "  4. Read NEUROS_X_INTEGRATION.md for full docs + marketing copy."
echo ""
echo -e "${GREEN}Done. Zenith v31 is ready. 🚀${NC}"
