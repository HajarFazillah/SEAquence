#!/bin/bash
# Talkativ AI - Startup Script

echo "========================================"
echo "       TALKATIV AI SERVER"
echo "========================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "No .env file found!"
    echo "   Creating from .env.example..."
    cp .env.example .env
    echo "   Please edit .env with API keys, do not leak!!!"
fi

# Check Python
echo "Python: $(python3 --version)"

# Install dependencies if needed
if [ "$1" == "--install" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt --break-system-packages
fi

# Run server
echo ""
echo "Starting server at http://127.0.0.1:8000"
echo "API docs at http://127.0.0.1:8000/docs"
echo ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
