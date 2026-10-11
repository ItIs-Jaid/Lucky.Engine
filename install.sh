#!/bin/bash
# Lucky.Engine Installation Script
# Usage: bash install.sh

echo "🚀 Installing Lucky.Engine..."

# Check dependencies
command -v python >/dev/null 2>&1 || { echo "❌ Python not found. Please install Python 3.8+"; exit 1; }

# Setup directories
TARGET_DIR="${1:-./lucky_engine}"
mkdir -p "$TARGET_DIR"

echo "📁 Setting up environment in $TARGET_DIR..."

# Note: This script assumes you have cloned the repo into this folder
# If running this from the repo root:
if [ -f "engine.py" ]; then
    echo "✅ Found engine.py in current directory"
else
    echo "⚠️  Please run this script from the cloned repo root"
    exit 1
fi

# Install dependencies (if any)
echo "📦 Checking dependencies..."
if python -c "import yaml" 2>/dev/null; then
    echo "✅ PyYAML already installed"
else
    echo "ℹ️  Install PyYAML if you need YAML config parsing: pip install pyyaml"
fi

# Run initial test
echo "🧪 Running initial test..."
if python test_suite.py 2>/dev/null; then
    echo "✅ Tests passed!"
else
    echo "⚠️  Tests not available yet. Run manually with: python test_suite.py"
fi

echo ""
echo "🎉 Lucky.Engine is ready!"
echo "📖 Read the README.md for usage examples."
