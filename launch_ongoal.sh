#!/bin/bash

echo "🚀 OnGoal Launcher"
echo "=================="

# Navigate to project directory
cd "$(dirname "$0")"

# Clean up any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "backend.main" 2>/dev/null || true
pkill -f "run_frontend" 2>/dev/null || true
pkill -f "uvicorn.*backend.main" 2>/dev/null || true
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :8080 | xargs kill -9 2>/dev/null || true
sleep 3

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Start backend
echo "🚀 Starting backend server..."
.venv/bin/python -m backend.main &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🌐 Starting frontend server..."
.venv/bin/python run_frontend.py &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 3

echo ""
echo "✅ OnGoal is now running!"
echo "📍 Open your browser and go to: http://localhost:8080"
echo ""
echo "🛑 To stop OnGoal, press Ctrl+C"
echo ""

# Wait for user to press Ctrl+C
trap 'echo ""; echo "🛑 Stopping OnGoal..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT

# Keep script running
while true; do
    sleep 1
done


#
