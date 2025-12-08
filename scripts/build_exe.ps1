Write-Host "🚀 Starting build process..."

# 1. Build Frontend
Write-Host "📦 Building Frontend..."
Push-Location front/app
npm ci
npm run build
Pop-Location

# 2. Install Build Dependencies
Write-Host "🔧 Installing build dependencies..."
uv pip install pyinstaller

# 3. Run PyInstaller
Write-Host "🔨 Running PyInstaller..."
# We run from root so paths in spec file are correct
uv run pyinstaller packaging/ouffroad.spec --clean --noconfirm

Write-Host "✅ PyInstaller build complete! Executable is in dist/ouffroad.exe"

# 4. Build Electron App
Write-Host "⚛️ Building Electron App..."
Push-Location front/electron
npm ci
npm run dist
Pop-Location

Write-Host "🎉 All builds complete!"
Write-Host "   - PyInstaller Binary: dist/ouffroad.exe"
Write-Host "   - Electron Installer: front/electron/dist/*.exe"
