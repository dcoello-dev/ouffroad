#!/bin/bash
# Test orchestration script for Ouffroad
# This script runs all tests (unit + E2E) with a temporary test repository

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_REPO_DIR="$PROJECT_ROOT/.test_repository"
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"

    # Kill backend if running
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
    fi

    # Remove test repository
    if [ -d "$TEST_REPO_DIR" ]; then
        echo "Removing test repository..."
        rm -rf "$TEST_REPO_DIR"
    fi

    echo -e "${GREEN}Cleanup complete${NC}"
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Print header
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Ouffroad Test Orchestration Script  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}[0/5] Installing ouffroad...${NC}"
uv pip install .

pytest

# Step 1: Create test repository
echo -e "${YELLOW}[1/5] Creating test repository...${NC}"
mkdir -p "$TEST_REPO_DIR"/{trail,enduro,special_events,media}

# Create test storage.toml
cat > "$TEST_REPO_DIR/storage.toml" << 'EOF'
[categories.trail]
name = "Trail"
type = "track"
extensions = [".gpx", ".fit", ".kml", ".kmz"]
color = "gold"

[categories.enduro]
name = "Enduro"
type = "track"
extensions = [".gpx", ".fit", ".kml", ".kmz"]
color = "red"

[categories.special_events]
name = "Eventos"
type = "track"
extensions = [".gpx", ".fit", ".kml", ".kmz"]
color = "purple"

[categories.media]
name = "Media"
type = "media"
extensions = [".jpg", ".jpeg", ".png", ".mp4", ".mov", ".avi", ".mkv"]
EOF

mkdir -p "$TEST_REPO_DIR/trail/2024/01"
echo -e "${GREEN}✓ Test repository created at: $TEST_REPO_DIR${NC}"

# Create sample GPX file for testing
cat > "$TEST_REPO_DIR/trail/2024/01/test_track.gpx" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="40.7128" lon="-74.0060"><ele>10</ele></trkpt>
      <trkpt lat="40.7138" lon="-74.0050"><ele>12</ele></trkpt>
      <trkpt lat="40.7148" lon="-74.0040"><ele>15</ele></trkpt>
    </trkseg>
  </trk>
</gpx>
EOF

# Step 2: Run unit tests
echo -e "\n${YELLOW}[2/5] Running unit tests (Vitest)...${NC}"
cd "$PROJECT_ROOT/front/app"
npm test -- --run
echo -e "${GREEN}✓ Unit tests passed${NC}"

# Step 3: Start backend with test repository
echo -e "\n${YELLOW}[3/5] Starting backend with test repository...${NC}"
cd "$PROJECT_ROOT"

# Set environment variable for test repository
export OUFFROAD_REPOSITORY_PATH="$TEST_REPO_DIR"

# Start backend in background
ouffroad --repo $TEST_REPO_DIR > /tmp/ouffroad_test_backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:$BACKEND_PORT/api/config > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        cat /tmp/ouffroad_test_backend.log
        exit 1
    fi
    sleep 1
done

# Step 4: Run E2E tests
echo -e "\n${YELLOW}[4/5] Running E2E tests (Playwright)...${NC}"
cd "$PROJECT_ROOT/front/app"

# Check if Playwright browsers are installed
if ! npx playwright --version > /dev/null 2>&1; then
    echo -e "${YELLOW}Installing Playwright browsers...${NC}"
    npx playwright install
fi

# Run Playwright tests
npm run test:e2e
echo -e "${GREEN}✓ E2E tests passed${NC}"

# Step 5: Summary
echo -e "\n${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Test Summary                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo -e "${GREEN}✓ Unit tests: PASSED${NC}"
echo -e "${GREEN}✓ E2E tests: PASSED${NC}"
echo -e "${GREEN}✓ All tests completed successfully!${NC}"
echo ""
echo -e "Test repository location: ${BLUE}$TEST_REPO_DIR${NC}"
echo -e "Backend log: ${BLUE}/tmp/ouffroad_test_backend.log${NC}"
