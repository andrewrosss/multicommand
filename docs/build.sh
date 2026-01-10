#!/usr/bin/env bash
#
# Build script for mdbook documentation.
# Used by Vercel for deploying the docs.
#
# Usage: ./build.sh
#

set -euo pipefail

MDBOOK_VERSION="v0.5.2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Downloading mdbook ${MDBOOK_VERSION}..."
curl -sSLo mdbook.tar.gz "https://github.com/rust-lang/mdBook/releases/download/${MDBOOK_VERSION}/mdbook-${MDBOOK_VERSION}-x86_64-unknown-linux-musl.tar.gz"
tar -xzf mdbook.tar.gz

echo "Building docs..."
./mdbook build

echo "Done! Output in ./book/"
