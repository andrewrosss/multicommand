#!/usr/bin/env bash
#
# Integration test for the pre-existing subparsers example.
# Tests that multicommand correctly handles parsers that already have
# add_subparsers() called.
#
# Usage: ./test_cli.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

run_test() {
    local name="$1"
    local expected="$2"
    shift 2
    local cmd=("$@")

    # Run the command and capture output
    local output
    if output=$("${cmd[@]}" 2>&1); then
        if [[ "$output" == *"$expected"* ]]; then
            echo -e "${GREEN}PASS${NC}: $name"
            ((PASSED++))
        else
            echo -e "${RED}FAIL${NC}: $name"
            echo "  Expected to contain: $expected"
            echo "  Got: $output"
            ((FAILED++))
        fi
    else
        # Some commands (like --help) may exit non-zero, check output anyway
        if [[ "$output" == *"$expected"* ]]; then
            echo -e "${GREEN}PASS${NC}: $name"
            ((PASSED++))
        else
            echo -e "${RED}FAIL${NC}: $name (command failed)"
            echo "  Expected to contain: $expected"
            echo "  Output: $output"
            ((FAILED++))
        fi
    fi
}

echo "Running pre-existing subparsers integration tests..."
echo "Using multicommand from: $REPO_ROOT"
echo "Using example from: $SCRIPT_DIR"
echo ""

# Base command - installs multicommand from repo root and preexisting from example dir
UV_CMD=(uv run --quiet --with "$REPO_ROOT" --with "$SCRIPT_DIR" python -m preexisting.cli)

# Test: Parser creation succeeds (this was the original bug - would fail with
# "cannot have multiple subparser arguments")
run_test "Parser creates without error" "available commands" \
    "${UV_CMD[@]}" --help

# Test: Help shows both manual and discovered commands
run_test "Help shows manual command" "manual" \
    "${UV_CMD[@]}" --help

run_test "Help shows discovered command" "discovered" \
    "${UV_CMD[@]}" --help

# Test: Manual command works
run_test "Manual command doubles value" "10" \
    "${UV_CMD[@]}" manual 5

run_test "Manual command with verbose" "Verbose" \
    "${UV_CMD[@]}" --verbose manual 5

# Test: Discovered command works
run_test "Discovered command greets" "Hello, World!" \
    "${UV_CMD[@]}" discovered World

# Test: Subcommand help works
run_test "Manual command help" "A value to process" \
    "${UV_CMD[@]}" manual --help

run_test "Discovered command help" "A name to greet" \
    "${UV_CMD[@]}" discovered --help

echo ""
echo "========================================="
echo -e "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
echo "========================================="

# Exit with failure if any tests failed
[[ $FAILED -eq 0 ]]
