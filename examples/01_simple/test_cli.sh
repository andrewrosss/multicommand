#!/usr/bin/env bash
#
# Integration test for the calculator CLI example.
# Uses `uv run` to create an isolated environment without polluting
# the current environment.
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
        echo -e "${RED}FAIL${NC}: $name (command failed)"
        echo "  Output: $output"
        ((FAILED++))
    fi
}

echo "Running calculator CLI integration tests..."
echo "Using multicommand from: $REPO_ROOT"
echo "Using example from: $SCRIPT_DIR"
echo ""

# Base command - installs multicommand from repo root and calculator from example dir
UV_CMD=(uv run --quiet --with "$REPO_ROOT" --with "$SCRIPT_DIR" python -m calculator.cli)

# Test: Help shows available commands
run_test "Help shows subcommands" "binary" \
    "${UV_CMD[@]}" --help

run_test "Help shows unary" "unary" \
    "${UV_CMD[@]}" --help

# Test: Binary operations
run_test "binary add 2 + 3 = 5" "5.0" \
    "${UV_CMD[@]}" binary add 2 3

run_test "binary subtract 10 - 4 = 6" "6.0" \
    "${UV_CMD[@]}" binary subtract 10 4

run_test "binary multiply 3 * 7 = 21" "21.0" \
    "${UV_CMD[@]}" binary multiply 3 7

run_test "binary divide 20 / 4 = 5" "5.0" \
    "${UV_CMD[@]}" binary divide 20 4

# Test: Unary operations
run_test "unary negate 42 = -42" "-42.0" \
    "${UV_CMD[@]}" unary negate 42

run_test "unary negate -5 = 5" "5.0" \
    "${UV_CMD[@]}" unary negate -- -5

# Test: Subcommand help
run_test "binary add --help shows description" "Add two numbers" \
    "${UV_CMD[@]}" binary add --help

run_test "unary negate --help shows description" "Negate a number" \
    "${UV_CMD[@]}" unary negate --help

echo ""
echo "========================================="
echo -e "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
echo "========================================="

# Exit with failure if any tests failed
[[ $FAILED -eq 0 ]]
