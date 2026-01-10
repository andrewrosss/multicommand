#!/usr/bin/env bash
#
# Preview docs locally on macOS.
# Downloads mdbook for macOS and serves docs with live reload.
#
# Usage: ./preview.sh
#

set -euo pipefail

MDBOOK_VERSION="v0.5.2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -x ./mdbook ]]; then
    echo "Downloading mdbook ${MDBOOK_VERSION} for macOS..."
    curl -sSLo mdbook.tar.gz "https://github.com/rust-lang/mdBook/releases/download/${MDBOOK_VERSION}/mdbook-${MDBOOK_VERSION}-aarch64-apple-darwin.tar.gz"
    tar -xzf mdbook.tar.gz
    rm mdbook.tar.gz
fi

echo "Starting mdbook serve..."
./mdbook serve --open
