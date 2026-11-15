#!/bin/bash
set -e

echo "Installing Lucky.Engine..."

if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "Python 3.8+ is required"; exit 1
fi

if [ ! -f "engine.py" ]; then
    echo "Run this script from the cloned repo root"; exit 1
fi

if [ ! -f "USER.md" ] && [ -f "examples/example-USER.md" ]; then
    cp "examples/example-USER.md" "USER.md"
fi
if [ ! -f "MEMORY-SSOT.md" ] && [ -f "examples/example-MEMORY-SSOT.md" ]; then
    cp "examples/example-MEMORY-SSOT.md" "MEMORY-SSOT.md"
fi
if [ ! -f "lucky-config.yaml" ] && [ -f "examples/example-config.yaml" ]; then
    cp "examples/example-config.yaml" "lucky-config.yaml"
fi

if [ ! -f "graph.json" ] && [ -f "USER.md" ] && [ -f "MEMORY-SSOT.md" ]; then
    "$PY" engine.py --build
fi

echo "Running tests..."
"$PY" test_suite.py
echo "Lucky.Engine ready."
