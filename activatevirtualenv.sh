#!/bin/bash

# Simple activation script for OnGoal project
# Usage: source activatevirtualenv.sh

if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run setup_env.sh first."
    return 1 2>/dev/null || exit 1
fi

echo "🔌 Activating OnGoal virtual environment..."
source .venv/bin/activate

echo "✅ Virtual environment activated!"
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
