# Quick Start Guide - AI Property Analysis

## 5-Minute Setup

### Step 1: Set Environment Variables

Create `backend/.env`:

```bash
# Minimum required setup (choose one)
OPENAI_API_KEY=sk-your-key-here

# OR for free tier (limited features)
# No key required - will use heuristic fallback
```

Optional (better imagery quality):
```bash
MAPBOX_ACCESS_TOKEN=pk.your-token-here
GOOGLE_MAPS_API_KEY=your-key-here
```

### Step 2: Install & Run

**Backend:**
```bash
cd backend
pip install fastapi uvicorn sqlalchemy psycopg2-binary requests pillow
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Step 3: Use the System

1. **Upload CSV** → http://localhost:3000/upload
2. **Wait for processing** → View status page
3. **View results** → Click "View Results"
4. **Run AI Analysis** → Click "Run AI Analysis" button
5. **View AI insights** → Expand property rows to see AI detections

## What Gets Analyzed

✅ **Automatically (Phase 1):**
- Wetlands, flood zones, slope
- Road access, protected land
- Geocoding and legal descriptions

🤖 **AI Analysis (Phase 2):**
- Road conditions (paved/dirt/gravel)
- Power line detection
- Development classification
- Satellite + street imagery

## API Keys - How to Get Them

### OpenAI (Recommended - Easiest Setup)
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy and paste into `.env`
4. **Cost:** ~$0.02 per property

### Mapbox (Optional - Better Imagery)
1. Go to https://account.mapbox.com/
2. Create free account
3. Copy default public token
4. **Free:** 50,000 requests/month

### Google Maps (Alternative)
1. Go to https://console.cloud.google.com/
2. Enable "Maps Static API" and "Street View API"
3. Create API key
4. **Free:** $200 credit/month

## Example CSV Format

```csv
Contact ID,First Name,Last Name,Street Address,City,State,Postal Code
001,John,Doe,123 Main St,Tampa,FL,33601
002,Jane,Smith,456 Oak Ave,Orlando,FL,32801
```

## Processing Times

| Properties | Phase 1 (GIS) | Phase 2 (AI) |
|-----------|---------------|--------------|
| 10        | ~30 seconds   | ~2 minutes   |
| 100       | ~5 minutes    | ~20 minutes  |
| 1,000     | ~50 minutes   | ~5 hours     |

*Times assume OpenAI API with 3 concurrent workers*

## Common Issues

**"No module named 'fastapi'"**
```bash
pip install -r backend/requirements.txt
```

**"Connection refused" on frontend**
```bash
# Make sure backend is running on port 8000
cd backend && python main.py
```

**"AI analysis returns 'Unknown'"**
```bash
# Set OPENAI_API_KEY in backend/.env
export OPENAI_API_KEY=your-key-here
```

**Images not loading**
```bash
# Add imagery provider API key
export MAPBOX_ACCESS_TOKEN=your-token-here
```

## Next Steps

- Read [AI_ANALYSIS_README.md](./AI_ANALYSIS_README.md) for detailed documentation
- Configure production ML models for cost savings
- Customize risk scoring thresholds
- Add custom property attributes

## Architecture Summary

```
User Uploads CSV
    ↓
Backend Processes Addresses
    ↓
Phase 1: GIS Analysis (free APIs)
    - Geocoding
    - Wetlands, flood, slope
    - Road access
    ↓
User Triggers AI Analysis
    ↓
Phase 2: AI Analysis (requires API keys)
    - Fetch satellite/street imagery
    - Classify road conditions
    - Detect power lines
    - Analyze development
    ↓
Results Displayed in Frontend
    - Risk badges
    - Interactive maps
    - Expandable property details
    - AI insights with confidence scores
```

## Support

- **Logs:** Check terminal running `python main.py`
- **Database:** PostgreSQL connection in `backend/database.py`
- **Debug:** Add `logger.info()` statements in service files
- **API Test:** http://localhost:8000/docs (FastAPI Swagger UI)

---

Ready to analyze properties! 🏡🤖
