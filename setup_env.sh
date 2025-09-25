#!/bin/bash

# Setup script for OnGoal project environment
# This script creates and activates the virtual environment

set -e  # Exit on any error

echo "🚀 Setting up OnGoal project environment..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found. Skipping dependency installation."
fi

echo "✅ Environment setup complete!"
echo ""
echo "To activate the environment manually, run:"
echo "    source .venv/bin/activate"
echo ""
echo "To deactivate when done, run:"
echo "    deactivate"
