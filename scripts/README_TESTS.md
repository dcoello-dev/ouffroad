# Test Orchestration Script

## Usage

Run all tests (unit + E2E) with a single command:

```bash
./scripts/run_all_tests.sh
```

## What it does

1. **Creates test repository** (`.test_repository/`)
   - Generates `storage.toml` with test categories
   - Creates sample GPX track for testing
   - Sets up directory structure

2. **Runs unit tests** (Vitest)
   - Tests ApiService
   - Tests Upload component
   - 15 tests total

3. **Starts backend** with test repository
   - Uses temporary repository
   - Runs on port 8000
   - Waits for backend to be ready

4. **Runs E2E tests** (Playwright)
   - Tests Sidebar functionality
   - Tests Map component
   - 10 tests total

5. **Cleanup**
   - Stops backend
   - Removes test repository
   - Cleans up processes

## Requirements

- Python environment with ouffroad installed
- Node.js with dependencies installed (`npm install` in `front/app`)
- Playwright browsers installed (script will install if missing)

## Output

The script provides colored output showing progress:
- 🟡 Yellow: Current step
- 🟢 Green: Success
- 🔴 Red: Error

Test repository location: `.test_repository/` (auto-removed after tests)
Backend log: `/tmp/ouffroad_test_backend.log`

## Environment Variables

The script sets:
- `OUFFROAD_REPOSITORY_PATH`: Points to test repository

## Troubleshooting

If tests fail:
1. Check backend log: `cat /tmp/ouffroad_test_backend.log`
2. Ensure ports 8000 and 5173 are free
3. Verify Playwright dependencies: `sudo npx playwright install-deps`
