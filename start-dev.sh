#!/bin/bash

# Development startup script for Microgrid Dashboard
# This script starts both Flask backend and Next.js frontend

set -e

echo "🚀 Starting Microgrid Dashboard Development Servers"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Please create a virtual environment first:"
    echo "  python3 -m venv venv"
    exit 1
fi

# Check if Flask-CORS is installed
source venv/bin/activate
if ! pip show Flask-CORS > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Flask-CORS not found, installing...${NC}"
    pip install Flask-CORS
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend dependencies not found, installing...${NC}"
    cd frontend
    npm install
    cd ..
fi

echo ""
echo -e "${GREEN}✓ Prerequisites checked${NC}"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping servers...${NC}"
    kill $FLASK_PID 2>/dev/null || true
    kill $NEXTJS_PID 2>/dev/null || true
    echo -e "${GREEN}✓ Servers stopped${NC}"
    exit 0
}

trap cleanup INT TERM EXIT

# Start Flask backend
echo -e "${GREEN}🐍 Starting Flask backend...${NC}"
source venv/bin/activate
python app.py > flask.log 2>&1 &
FLASK_PID=$!
echo "   Flask PID: $FLASK_PID"
echo "   Logs: flask.log"

# Wait for Flask to start
echo "   Waiting for Flask to start..."
sleep 3

# Check if Flask is running
if ! kill -0 $FLASK_PID 2>/dev/null; then
    echo -e "${RED}❌ Flask failed to start!${NC}"
    echo "Check flask.log for errors"
    exit 1
fi

# Start Next.js frontend
echo ""
echo -e "${GREEN}⚛️  Starting Next.js frontend...${NC}"
cd frontend
npm run dev > ../nextjs.log 2>&1 &
NEXTJS_PID=$!
cd ..
echo "   Next.js PID: $NEXTJS_PID"
echo "   Logs: nextjs.log"

# Wait for Next.js to start
echo "   Waiting for Next.js to start..."
sleep 5

# Check if Next.js is running
if ! kill -0 $NEXTJS_PID 2>/dev/null; then
    echo -e "${RED}❌ Next.js failed to start!${NC}"
    echo "Check nextjs.log for errors"
    kill $FLASK_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Both servers started successfully!${NC}"
echo ""
echo "=================================================="
echo -e "${GREEN}🌐 Dashboard is ready!${NC}"
echo ""
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:5000"
echo ""
echo "   Flask logs:   tail -f flask.log"
echo "   Next.js logs: tail -f nextjs.log"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "=================================================="

# Wait for Ctrl+C
wait
