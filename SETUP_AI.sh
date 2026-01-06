#!/bin/bash

# AI Imagery Analysis System - Setup Script
# This script sets up and verifies the AI analysis system

set -e  # Exit on error

echo "============================================================"
echo "AI IMAGERY ANALYSIS SYSTEM - SETUP"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check if we're in the right directory
echo "Step 1: Checking directory..."
if [ ! -f "backend/main.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the property-anyslis directory${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Directory OK${NC}"
echo ""

# Step 2: Check virtual environment
echo "Step 2: Checking Python virtual environment..."
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi
echo -e "${GREEN}✅ Virtual environment OK${NC}"
echo ""

# Step 3: Install dependencies
echo "Step 3: Installing Python dependencies..."
cd backend
source venv/bin/activate

if ! pip list | grep -q "fastapi"; then
    echo "Installing required packages..."
    pip install fastapi uvicorn sqlalchemy psycopg2-binary requests pillow python-dotenv
fi
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 4: Run database migration
echo "Step 4: Running database migration..."
if python migrate_ai_schema.py; then
    echo -e "${GREEN}✅ Database migration completed${NC}"
else
    echo -e "${RED}❌ Migration failed - check database connection${NC}"
    exit 1
fi
echo ""

# Step 5: Run tests
echo "Step 5: Running system tests..."
if python test_ai_system.py; then
    echo -e "${GREEN}✅ All tests passed${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

cd ..
echo ""

# Step 6: Check frontend
echo "Step 6: Checking frontend..."
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend dependencies not installed${NC}"
    echo "Run: cd frontend && npm install"
fi
echo ""

# Step 7: Environment variables reminder
echo "============================================================"
echo "SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "⚠️  IMPORTANT: Configure API Keys for Full Functionality"
echo ""
echo "Add these to backend/.env (optional but recommended):"
echo ""
echo "# Required for AI analysis"
echo "OPENAI_API_KEY=sk-your-key-here"
echo ""
echo "# Optional for better imagery"
echo "MAPBOX_ACCESS_TOKEN=pk-your-token-here"
echo "GOOGLE_MAPS_API_KEY=your-key-here"
echo ""
echo "See AI_QUICKSTART.md for instructions on getting API keys."
echo ""
echo "============================================================"
echo "TO START THE APPLICATION:"
echo "============================================================"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then visit: http://localhost:3000"
echo ""
echo "============================================================"
echo "✅ Setup complete! Ready to analyze properties with AI!"
echo "============================================================"
