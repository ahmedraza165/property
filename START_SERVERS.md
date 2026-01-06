# Quick Start Guide

## Starting the Application

### Terminal 1 - Backend (Python/FastAPI)

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: http://localhost:8000

### Terminal 2 - Frontend (Next.js)

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

## Verify Backend is Running

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","database":"connected"}
```

## Test Upload

1. Open browser to http://localhost:3000
2. Click "Upload CSV"
3. Upload the sample file from `backend/test_sample.csv`
4. Monitor processing in real-time
5. View results with filtering by County and Postal Code

## API Documentation

Once backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Features Available

### Property Analysis
- ✅ Geocoding with county extraction
- ✅ Flood zone analysis (FEMA)
- ✅ Wetlands detection (USFWS)
- ✅ Slope/terrain analysis (USGS)
- ✅ Road access & landlocked detection (OSM)
- ✅ Protected land detection (PAD-US)
- ✅ Legal description (OSM + coordinate-based)
- ✅ Water/sewer utility detection (OSM)

### Data Display
- ✅ Legal description column in results
- ✅ Water/sewer utility information
- ✅ County and postal code filters
- ✅ CSV export with all columns
- ✅ Real-time processing status
- ✅ Risk distribution insights

## Troubleshooting

### Backend won't start
- Check if port 8000 is in use: `lsof -i :8000`
- Verify dependencies: `pip install -r requirements.txt`
- Check logs for errors

### Frontend won't start
- Check if port 3000 is in use: `lsof -i :3000`
- Verify dependencies: `npm install`
- Check `.env.local` has correct API URL

### No results processing
- Check internet connectivity (APIs require network access)
- Verify geocoding service is accessible
- Check backend logs for API errors

### Geocoding failures
- US Census API might be temporarily unavailable
- Check DNS resolution
- Verify network allows HTTPS connections

## File Structure

```
property-anyslis/
├── backend/
│   ├── main.py                          # API endpoints
│   ├── geocoding_service.py             # US Census geocoding
│   ├── gis_service.py                   # GIS risk analysis
│   ├── legal_description_service.py     # Legal descriptions
│   ├── water_utility_service.py         # Water/sewer utilities
│   ├── models.py                        # Database models
│   ├── database.py                      # DB configuration
│   ├── requirements.txt                 # Python dependencies
│   ├── test_sample.csv                  # Sample test data
│   └── property_analysis.db             # SQLite database
├── frontend/
│   ├── app/
│   │   ├── page.tsx                     # Home page
│   │   ├── upload/page.tsx              # Upload page
│   │   ├── status/[jobId]/page.tsx      # Status page
│   │   └── results/[jobId]/page.tsx     # Results with filters
│   ├── lib/
│   │   ├── api.ts                       # API client
│   │   └── hooks.ts                     # React hooks
│   └── components/                      # UI components
└── IMPLEMENTATION_SUMMARY.md            # Full documentation
```
