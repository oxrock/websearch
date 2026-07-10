#!/usr/bin/env bash
# run_tests.sh - Install dependencies and run all tests for websearch package.
# Usage: ./run_tests.sh
# Output is printed to console and saved to test_output.log

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${PROJECT_ROOT}/test_output.log"

echo "============================================="
echo "🧪 WEBSEARCH PACKAGE TEST RUNNER"
echo "============================================="
echo "Project root: ${PROJECT_ROOT}"
echo "Log file: ${LOG_FILE}"
echo ""

# Redirect all output to both console and log file
exec > >(tee -a "${LOG_FILE}") 2>&1

cd "${PROJECT_ROOT}"

echo "[1/4] Installing package in editable mode with dev dependencies..."
pip install -e ".[dev]" --quiet

echo "[2/4] Running pytest unit tests..."
python -m pytest tests/ -v --tb=short

echo "[3/4] Running smoke test (live integration)..."
python smoke_test.py

echo "[4/4] Verifying import works from external context..."
python -c "from websearch import web_search, web_extract, execute_system_command; print('✅ Import successful:', web_search.__module__)"

echo ""
echo "============================================="
echo "✅ ALL TESTS COMPLETED"
echo "============================================="
echo "Full output saved to: ${LOG_FILE}"