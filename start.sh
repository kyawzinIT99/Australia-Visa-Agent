#!/bin/bash

# Quick Start Script for Australia Visa AI Agent
# This script handles all setup and launches the system

echo "🚀 Australia Visa AI Agent - Quick Start"
echo "========================================"

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Clean up any stuck processes on port 5001
echo "🧹 Cleaning up ports..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

# Start the system
echo "▶️  Starting system..."
python3 run_system.py
