#!/bin/bash

echo "🚀 Starting ParcelIQ Platform..."
echo ""

# Colors for output
GREEN='\033[0.32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if backend dependencies are installed
echo -e "${BLUE}📦 Checking backend dependencies...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Install core backend dependencies (without AI/ML packages)
./venv/bin/pip install -q fastapi uvicorn[standard] sqlalchemy pandas requests python-multipart shapely geopandas geopy osmnx 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo "Installing dependencies (this may take a few minutes)..."
    ./venv/bin/pip install fastapi uvicorn[standard] sqlalchemy pandas requests python-multipart shapely geopandas geopy osmnx
fi

# Start backend
echo -e "${BLUE}🔧 Starting backend server on port 8000...${NC}"
./venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if frontend dependencies are installed
echo -e "${BLUE}📦 Checking frontend dependencies...${NC}"
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo -e "${GREEN}✓ Frontend dependencies ready${NC}"

# Start frontend
echo -e "${BLUE}🎨 Starting frontend on port 3000...${NC}"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✅ ParcelIQ is running!${NC}"
echo ""
echo "📍 Backend API:  http://localhost:8000"
echo "📍 API Docs:     http://localhost:8000/docs"
echo "📍 Frontend:     http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
