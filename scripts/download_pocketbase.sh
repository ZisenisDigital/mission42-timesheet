#!/bin/bash

# PocketBase Download Script
# Downloads the latest PocketBase binary for the current platform

set -e

# Configuration
POCKETBASE_VERSION="0.24.1"  # Update this to get newer versions
POCKETBASE_DIR="pocketbase"

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Map architecture names
case "$ARCH" in
    x86_64)
        ARCH="amd64"
        ;;
    aarch64|arm64)
        ARCH="arm64"
        ;;
    armv7l)
        ARCH="armv7"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Map OS names
case "$OS" in
    linux)
        OS="linux"
        BINARY_NAME="pocketbase"
        ;;
    darwin)
        OS="darwin"
        BINARY_NAME="pocketbase"
        ;;
    msys*|mingw*|cygwin*|windows*)
        OS="windows"
        BINARY_NAME="pocketbase.exe"
        ;;
    *)
        echo "Unsupported operating system: $OS"
        exit 1
        ;;
esac

# Construct download URL
POCKETBASE_FILENAME="pocketbase_${POCKETBASE_VERSION}_${OS}_${ARCH}.zip"
POCKETBASE_URL="https://github.com/pocketbase/pocketbase/releases/download/v${POCKETBASE_VERSION}/${POCKETBASE_FILENAME}"

echo "Downloading PocketBase ${POCKETBASE_VERSION} for ${OS}/${ARCH}..."
echo "URL: ${POCKETBASE_URL}"

# Create pocketbase directory if it doesn't exist
mkdir -p "$POCKETBASE_DIR"

# Download PocketBase
if command -v curl &> /dev/null; then
    curl -L -o "${POCKETBASE_DIR}/${POCKETBASE_FILENAME}" "${POCKETBASE_URL}"
elif command -v wget &> /dev/null; then
    wget -O "${POCKETBASE_DIR}/${POCKETBASE_FILENAME}" "${POCKETBASE_URL}"
else
    echo "Error: Neither curl nor wget is installed"
    exit 1
fi

# Extract PocketBase
echo "Extracting PocketBase..."
if command -v unzip &> /dev/null; then
    unzip -o "${POCKETBASE_DIR}/${POCKETBASE_FILENAME}" -d "${POCKETBASE_DIR}"
else
    echo "Error: unzip is not installed"
    exit 1
fi

# Make binary executable (Unix-like systems)
if [ "$OS" != "windows" ]; then
    chmod +x "${POCKETBASE_DIR}/${BINARY_NAME}"
fi

# Clean up zip file
rm "${POCKETBASE_DIR}/${POCKETBASE_FILENAME}"

echo ""
echo "✅ PocketBase ${POCKETBASE_VERSION} downloaded successfully!"
echo ""
echo "To start PocketBase:"
echo "  cd ${POCKETBASE_DIR}"
echo "  ./${BINARY_NAME} serve"
echo ""
echo "Admin UI will be available at: http://127.0.0.1:8090/_/"
echo ""
