#!/bin/bash
#
# Build script for creating macOS .app and .dmg for Wikidich Ebook Creator
#
# Usage: ./build_mac_app.sh
#

set -e  # Exit on error

echo "========================================="
echo "  Wikidich Ebook Creator - macOS Build"
echo "========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: This script must be run on macOS"
    exit 1
fi

# Get version from __init__.py
VERSION=$(python3 -c "
import re
with open('wikidich_ebook/__init__.py', 'r') as f:
    content = f.read()
    match = re.search(r'__version__\s*=\s*[\"\\']([^\"\\']*)[\"\\'\\']', content)
    print(match.group(1) if match else '2.0.0')
")
echo "📦 Building version: $VERSION"
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist
echo "✓ Clean complete"
echo ""

# Install/upgrade build dependencies
echo "📥 Installing build dependencies..."
python3 -m pip install --upgrade pyinstaller
echo "✓ Build dependencies installed"
echo ""

# Build the app with PyInstaller
echo "🔨 Building macOS app with PyInstaller..."
pyinstaller wikidich_ebook.spec --clean --noconfirm
echo "✓ App built successfully"
echo ""

# Check if app was created
APP_PATH="dist/Wikidich Ebook Creator.app"
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: App bundle was not created"
    exit 1
fi

echo "✓ App bundle created: $APP_PATH"
echo ""

# Create DMG
DMG_NAME="WikidichEbookCreator-${VERSION}.dmg"
DMG_PATH="dist/$DMG_NAME"
VOLUME_NAME="Wikidich Ebook Creator ${VERSION}"

echo "📀 Creating DMG installer..."

# Remove old DMG if exists
rm -f "$DMG_PATH"

# Create a temporary DMG
TMP_DMG="dist/tmp.dmg"
rm -f "$TMP_DMG"

# Create DMG with hdiutil
echo "  Creating disk image..."
hdiutil create -size 500m -fs HFS+ -volname "$VOLUME_NAME" "$TMP_DMG"

# Mount the DMG
echo "  Mounting disk image..."
MOUNT_DIR=$(hdiutil attach -readwrite -noverify -noautoopen "$TMP_DMG" | grep "/Volumes/" | sed 's/.*\(\/Volumes\/.*\)/\1/' | head -1)

# Copy the app to the DMG
echo "  Copying app to disk image..."
cp -R "$APP_PATH" "$MOUNT_DIR/"

# Create Applications symlink
echo "  Creating Applications symlink..."
ln -s /Applications "$MOUNT_DIR/Applications"

# Set background and icon positions (optional)
# You can customize this section if you want a custom DMG appearance

# Unmount
echo "  Unmounting disk image..."
hdiutil detach "$MOUNT_DIR"

# Convert to compressed DMG
echo "  Compressing disk image..."
hdiutil convert "$TMP_DMG" -format UDZO -o "$DMG_PATH"
rm -f "$TMP_DMG"

echo "✓ DMG created: $DMG_PATH"
echo ""

# Get file size
DMG_SIZE=$(du -h "$DMG_PATH" | awk '{print $1}')
echo "========================================="
echo "  ✅ Build Complete!"
echo "========================================="
echo ""
echo "📦 Output:"
echo "  App: $APP_PATH"
echo "  DMG: $DMG_PATH ($DMG_SIZE)"
echo ""
echo "To test the app:"
echo "  open \"$APP_PATH\""
echo ""
echo "To distribute:"
echo "  Share the DMG file: $DMG_PATH"
echo ""
echo "Users can:"
echo "  1. Download the DMG"
echo "  2. Open it and drag the app to Applications"
echo "  3. Launch from Applications folder"
echo "  4. App will auto-check for updates from GitHub"
echo ""
