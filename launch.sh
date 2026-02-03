#!/bin/bash
# SPDX-License-Identifier: MIT

# Frigate Control Panel Launcher Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo " Starting Frigate Control Panel..."
echo "📍 Working directory: $SCRIPT_DIR"
echo ""

# Make launch script executable
chmod +x launch.sh

echo "✅ Setup complete!"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    echo " Please install Python 3:"
    echo "   sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
VENV_DIR="$SCRIPT_DIR/.venv"
PIP_PATH="$VENV_DIR/bin/pip"

if [ ! -d "$VENV_DIR" ] || [ ! -f "$PIP_PATH" ]; then
    echo " Creating Python virtual environment..."
    if ! python3 -m venv "$VENV_DIR"; then
        echo "❌ Failed to create virtual environment."
        echo " Please install python3-venv: sudo apt install python3-venv"
        exit 1
    fi
fi

echo "✅ Virtual environment ready"
echo ""

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install/upgrade required packages
echo "📦 Checking Python packages..."
pip install --quiet --upgrade pip 2>/dev/null || true
pip install --quiet PySide6 PyYAML 2>/dev/null || {
    echo "⚠️  Installing packages (this may take a moment)..."
    pip install PySide6 PyYAML || {
        echo "❌ Failed to install required packages."
        echo "📝 You may need: sudo apt install python3-dev build-essential"
        exit 1
    }
}

echo "✅ All packages ready"
echo ""
# Launch the GUI application
echo "🎮 Launching Frigate Control Panel..."
python frigate_launcher.py

echo ""
echo "👋 Application closed."
