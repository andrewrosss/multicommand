#!/usr/bin/env bash
#
# Build script for mdbook documentation with mdbook-admonish support.
# Used by Vercel for deploying the docs.
#
# Usage: ./build.sh
#

set -euo pipefail

MDBOOK_VERSION="v0.5.2"
MDBOOK_ADMONISH_VERSION="v1.20.0"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Downloading mdbook ${MDBOOK_VERSION}..."
curl -sSLo mdbook.tar.gz "https://github.com/rust-lang/mdBook/releases/download/${MDBOOK_VERSION}/mdbook-${MDBOOK_VERSION}-x86_64-unknown-linux-musl.tar.gz"
tar -xzf mdbook.tar.gz

echo "Downloading mdbook-admonish ${MDBOOK_ADMONISH_VERSION}..."
curl -sSLo mdbook-admonish.tar.gz "https://github.com/tommilligan/mdbook-admonish/releases/download/${MDBOOK_ADMONISH_VERSION}/mdbook-admonish-${MDBOOK_ADMONISH_VERSION}-x86_64-unknown-linux-musl.tar.gz"
tar -xzf mdbook-admonish.tar.gz

echo "Building docs..."
export PATH="$SCRIPT_DIR:$PATH"
./mdbook build

echo "Done! Output in ./book/"
