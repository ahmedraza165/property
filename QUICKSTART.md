# QuickStart Guide - ParcelIQ

Get ParcelIQ up and running in 5 minutes.

## Prerequisites
- Node.js 18+ installed
- Python 3.11+ installed
- PostgreSQL running (or use SQLite for testing)

## Quick Setup

### 1. Backend (Terminal 1)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up database (uses SQLite by default for quick testing)
# For PostgreSQL, update .env with DATABASE_URL
python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"

# Start backend server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run at: http://localhost:8000
API docs at: http://localhost:8000/docs

### 2. Frontend (Terminal 2)

```bash
# Navigate to frontend (from project root)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run at: http://localhost:3000

## Test the Application

1. Open browser to http://localhost:3000
2. Click "Upload CSV"
3. Use the sample CSV from `backend/Export_Contacts_Cleaned Target Best Lehigh_Dec_2025_5_41_PM.csv`
4. Drag and drop the file or click to browse
5. Click "Start Analysis"
6. Watch real-time processing status
7. View detailed results with risk analysis

## Features to Try

- **Dashboard**: View overview and recent uploads
- **Upload**: Test drag-and-drop CSV upload
- **Status**: Watch animated processing progress
- **Results**:
  - Sort by address or risk
  - Filter by risk level (Low/Medium/High)
  - Search by address
  - Expand rows for details
  - Export results as CSV

## Production Build

### Backend
```bash
cd backend
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend
```bash
cd frontend
npm run build
npm start
```

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Check if port 8000 is available
- Verify all dependencies installed: `pip list`

### Frontend won't start
- Check Node version: `node --version` (need 18+)
- Delete `node_modules` and `.next`, then run `npm install` again
- Check if port 3000 is available

### Can't connect to backend
- Verify backend is running at http://localhost:8000
- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Check browser console for CORS errors

### Database errors
- For quick testing, the backend uses SQLite by default
- For production, configure PostgreSQL in `backend/.env`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check API docs at http://localhost:8000/docs
- Customize branding and theme in `frontend/app/globals.css`
- Configure external API keys for GIS services

## Need Help?

- Check the API documentation: http://localhost:8000/docs
- Review example CSV format in backend folder
- Ensure all required CSV columns are present

---

**You're all set! Start analyzing properties with ParcelIQ.**
