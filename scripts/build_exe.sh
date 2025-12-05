#!/bin/bash
set -e

echo "🚀 Starting build process..."

# 1. Build Frontend
echo "📦 Building Frontend..."
cd front/app
npm ci
npm run build
cd ../..

# 2. Install Build Dependencies
echo "🔧 Installing build dependencies..."
uv pip install pyinstaller

# 3. Run PyInstaller
echo "🔨 Running PyInstaller..."
# We run from root so paths in spec file are correct
uv run pyinstaller packaging/ouffroad.spec --clean --noconfirm

echo "✅ Build complete! Executable is in dist/ouffroad"
