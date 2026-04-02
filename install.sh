#!/bin/bash
set -e

echo "[HierarchicalDatacubes] Installing using Python 3.10+..."

# Check Python 3.10 or higher
if ! command -v python3.10 &> /dev/null; then
    echo "❌ Python 3.10 not found. Please install it first:"
    echo "https://www.python.org/downloads/"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3.10 -m venv .venv

# Activate and install dependencies
echo "Installing dependencies..."
source .venv/bin/activate
python3.10 -m ensurepip --upgrade
python3.10 -m pip install --upgrade pip
python3.10 -m pip install -e .

echo
echo "✅ HierarchicalDatacubes is ready to use!"
echo "To run it:"
echo "    source .venv/bin/activate"
echo "    datacube-gui     # PyQt6 interface"
echo "    datacube-cli     # CLI benchmark tool"
