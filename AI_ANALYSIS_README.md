# AI Imagery Analysis System - Documentation

## Overview

This system implements AI-powered property analysis using satellite and street-level imagery to detect:
- **Road Conditions** - Paved, dirt, gravel, or poor condition roads
- **Power Lines** - Detection and proximity measurement of electrical infrastructure
- **Nearby Development** - Classification of surrounding area (residential, commercial, industrial, agricultural, undeveloped)

## Architecture

### Backend Components

#### 1. Database Models (`models.py`)

**AIAnalysisResult Table**
```python
- satellite_image_url, street_image_url: Image URLs
- satellite_image_source, street_image_source: Provider names (Mapbox, Google, etc.)
- road_condition_type: PAVED, DIRT, GRAVEL, POOR, UNKNOWN
- road_condition_confidence: 0.0 - 1.0
- power_lines_visible: Boolean
- power_line_confidence: 0.0 - 1.0
- power_line_distance_meters: Distance in meters
- power_line_geometry: GeoJSON polygon data
- nearby_dev_type: RESIDENTIAL, COMMERCIAL, INDUSTRIAL, AGRICULTURAL, UNDEVELOPED
- nearby_dev_count: Number of structures detected
- ai_risk_level: LOW, MEDIUM, HIGH
- ai_risk_confidence: 0.0 - 1.0
- model_version: Version tracking for AI models
```

**ImageCache Table**
- Caches imagery to avoid redundant API calls
- Stores latitude, longitude, image_type, url, and source
- 30-day default cache lifetime

#### 2. Imagery Service (`imagery_service.py`)

**Supported Image Providers:**

**Satellite Imagery:**
1. **Mapbox Satellite** (Primary)
   - Requires: `MAPBOX_ACCESS_TOKEN` environment variable
   - Free tier: 50,000 requests/month
   - High-quality satellite imagery

2. **Google Maps Static API** (Secondary)
   - Requires: `GOOGLE_MAPS_API_KEY` environment variable
   - Satellite view with high resolution

3. **OpenStreetMap** (Fallback)
   - No API key required
   - Returns map view instead of satellite

**Street-Level Imagery:**
1. **Mapillary** (Primary)
   - Requires: `MAPILLARY_CLIENT_TOKEN` environment variable
   - Open-source street imagery

2. **Google Street View** (Secondary)
   - Requires: `GOOGLE_MAPS_API_KEY` environment variable
   - Checks availability before fetching

**Key Features:**
- Automatic caching in database
- Fallback chain for reliability
- Geographic coordinate-based image retrieval
- Configurable zoom levels and dimensions

#### 3. AI Analysis Service (`ai_analysis_service.py`)

**AI Model Integration Options:**

**Current Implementation:**
- OpenAI Vision API (GPT-4 Vision)
- Requires: `OPENAI_API_KEY` environment variable
- Provides text-based analysis of imagery

**Production Alternatives:**
1. **Local PyTorch/TensorFlow Models**
   - Custom-trained road condition classifier
   - YOLO/Faster R-CNN for power line detection
   - ResNet/EfficientNet for development classification

2. **Cloud AI Services:**
   - AWS Rekognition
   - Azure Computer Vision
   - Google Cloud Vision API

3. **Specialized Models:**
   - RoadNet for road condition analysis
   - PowerLineNet for infrastructure detection
   - LandCover models for development classification

**Analysis Pipeline:**
```
1. Download Images → 2. Road Condition Analysis → 3. Power Line Detection
→ 4. Development Classification → 5. Overall Risk Calculation → 6. Store Results
```

**Risk Calculation:**
- Road condition: DIRT (+30 pts), GRAVEL (+20), POOR (+25)
- Power lines: <50m (+25), <100m (+15), visible (+10)
- Development: UNDEVELOPED (+20), INDUSTRIAL (+15)
- Risk levels: <25 = LOW, 25-49 = MEDIUM, 50+ = HIGH

#### 4. API Endpoints (`main.py`)

**POST `/analyze-ai/{job_id}`**
- Triggers AI analysis for all properties in a job
- Runs in background with ThreadPoolExecutor
- Concurrency: 3 workers (GPU/API rate limit consideration)
- Returns immediately with status

**GET `/ai-results/{job_id}`**
- Retrieves all AI analysis results for a job
- Returns imagery URLs, detections, and confidence scores

**GET `/results/{job_id}`** (Updated)
- Now includes `ai_analysis` field in each property result
- LEFT JOIN ensures results return even without AI data

### Frontend Components

#### 1. AI Insights Panel (`components/ai-insights-panel.tsx`)

Standalone component for detailed AI analysis display:
- Satellite and street imagery with source labels
- Road condition classification with color coding
- Power line detection with distance estimates
- Development analysis with structure counts
- Confidence scoring for all detections
- Processing metadata (model version, analysis time)

#### 2. Results Page Integration (`app/results/[jobId]/page.tsx`)

**New Features:**
- "Run AI Analysis" button to trigger analysis
- AI analysis section in expandable property rows
- Inline imagery display (satellite + street view)
- Detection badges for road condition, power lines, development
- AI risk level with confidence percentage

**User Flow:**
1. Upload CSV and process properties
2. Click "Run AI Analysis" button on results page
3. Wait for background processing (3 properties/minute with OpenAI API)
4. Refresh page to see AI results
5. Expand property rows to view detailed AI analysis

#### 3. API Client Updates (`lib/api.ts`)

Updated `AIAnalysis` interface to match backend response:
```typescript
imagery: { satellite: {url, source}, street: {url, source} }
road_condition: { type, confidence }
power_lines: { visible, confidence, distance_meters, geometry }
nearby_development: { type, count, confidence }
overall_risk: { level, confidence }
```

#### 4. React Query Hooks (`lib/hooks.ts`)

`useTriggerAIAnalysis()` - Mutation hook for triggering AI analysis
- Invalidates job results on success
- Handles loading and error states

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Database
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/property_analysis

# Required: Choose at least one imagery provider
MAPBOX_ACCESS_TOKEN=your_mapbox_token_here          # Recommended
GOOGLE_MAPS_API_KEY=your_google_api_key_here        # Alternative

# Optional: Street view imagery
MAPILLARY_CLIENT_TOKEN=your_mapillary_token_here    # Optional

# AI Analysis: Choose one
OPENAI_API_KEY=your_openai_api_key_here             # GPT-4 Vision (easiest)
# OR configure local ML models (see Production Deployment below)
```

### 2. Database Migration

```bash
cd backend

# The tables will be created automatically on first run
# Alternatively, create them explicitly:
python -c "from models import Base; from database import engine; Base.metadata.create_all(bind=engine)"
```

### 3. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 4. Run the Application

**Backend:**
```bash
cd backend
python main.py
# Runs on http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:3000
```

## Usage Guide

### 1. Process Properties

1. Navigate to http://localhost:3000
2. Upload CSV file with property addresses
3. Wait for geocoding and GIS analysis to complete

### 2. Run AI Analysis

1. Go to results page for your upload
2. Click "Run AI Analysis" button
3. Wait for background processing (time depends on property count)
4. Refresh the page to see results

### 3. View AI Results

1. Expand any property row in the results table
2. Scroll to "AI-Powered Analysis" section
3. View:
   - Satellite and street imagery
   - Road condition classification
   - Power line detections
   - Development analysis
   - Overall AI risk assessment

### 4. Export Results

Click "Export CSV" to download results including AI analysis data.

## API Rate Limits & Performance

### Imagery APIs

**Mapbox:**
- Free tier: 50,000 requests/month
- Rate limit: No strict limit, but recommended <100/min
- Caching: 30 days by default

**Google Maps:**
- Free tier: $200 credit/month (~28,000 requests)
- Rate limit: 50 requests/second
- Quota: Track usage in Google Cloud Console

**OpenAI Vision:**
- GPT-4 Vision pricing: $0.01/image (1024x1024)
- Rate limit: Varies by tier (default: 100 requests/min)
- Cost estimate: ~$0.02 per property (2 images)

### Performance Optimization

**Image Caching:**
- All images cached in `ImageCache` table
- Cache hit ratio typically >80% for duplicate properties
- Manual cache clearing: `DELETE FROM image_cache WHERE fetched_at < NOW() - INTERVAL '30 days';`

**Concurrent Processing:**
- Default: 3 concurrent AI analyses
- Adjustable in `main.py`: `max_workers = 3`
- Recommendation: 3-5 for cloud APIs, 10+ for local models

**Batch Processing Time Estimates:**
- 100 properties: ~30-50 minutes (with OpenAI API)
- 1,000 properties: ~5-8 hours
- 10,000 properties: ~50-80 hours

## Production Deployment

### 1. Using Local ML Models (Recommended for Scale)

**Replace OpenAI API with custom models:**

```python
# In ai_analysis_service.py

import torch
from torchvision import models, transforms

class AIAnalysisService:
    def __init__(self):
        # Load pre-trained models
        self.road_model = self._load_road_classifier()
        self.powerline_model = self._load_object_detector()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def _load_road_classifier(self):
        # Load custom road condition classifier
        model = models.resnet50(pretrained=False)
        model.fc = torch.nn.Linear(model.fc.in_features, 5)  # 5 classes
        model.load_state_dict(torch.load('models/road_classifier.pth'))
        model.to(self.device)
        model.eval()
        return model

    def _classify_road_with_ai(self, image_bytes):
        # Use local model instead of OpenAI
        image = Image.open(io.BytesIO(image_bytes))
        transform = transforms.Compose([...])
        input_tensor = transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.road_model(input_tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probs, 1)

        classes = ['PAVED', 'DIRT', 'GRAVEL', 'POOR', 'UNKNOWN']
        return {
            'type': classes[predicted.item()],
            'confidence': confidence.item(),
            'source': 'local_model'
        }
```

**Benefits:**
- No API costs (only initial model training)
- Faster processing (GPU inference ~100ms vs 2-5s API call)
- Higher concurrency (10-20 workers)
- No rate limits
- Full control over model updates

### 2. Model Training

**Road Condition Classifier:**
```python
# Training data structure:
# dataset/
#   train/
#     paved/
#     dirt/
#     gravel/
#     poor/
#   val/
#     paved/
#     ...

# Train with PyTorch/Fastai
from fastai.vision.all import *

dls = ImageDataLoaders.from_folder(
    'dataset',
    valid_pct=0.2,
    item_tfms=Resize(224)
)

learn = vision_learner(dls, resnet50, metrics=accuracy)
learn.fine_tune(10)
learn.export('road_classifier.pkl')
```

**Power Line Detector:**
- Use YOLO v8 or Faster R-CNN
- Annotate training data with bounding boxes
- Train on power line infrastructure images
- Export model for inference

### 3. GPU Configuration

**Docker Deployment:**
```dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y python3-pip
COPY requirements.txt .
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
RUN pip install -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

# Run with GPU support
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Run container:**
```bash
docker run --gpus all -p 8000:8000 property-analysis-ai
```

### 4. Horizontal Scaling

**Queue-based processing with Celery:**

```python
# tasks.py
from celery import Celery

celery_app = Celery('tasks', broker='redis://localhost:6379/0')

@celery_app.task
def process_property_ai_task(property_id, upload_id):
    return process_single_property_ai(property_id, upload_id)

# main.py
@app.post("/analyze-ai/{job_id}")
async def trigger_ai_analysis(job_id: str, db: Session = Depends(get_db)):
    properties = db.query(Property).filter(...).all()

    # Queue tasks
    for prop in properties:
        process_property_ai_task.delay(prop.id, job_id)

    return {"message": "AI analysis queued"}
```

**Deploy multiple workers:**
```bash
# Start 10 Celery workers with GPU access
celery -A tasks worker --concurrency=10 --pool=threads
```

## Monitoring & Debugging

### 1. Check Processing Status

```python
# In Python shell
from database import SessionLocal
from models import AIAnalysisResult

db = SessionLocal()

# Count completed analyses
completed = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.error_message == None
).count()

# Check error rate
errors = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.error_message != None
).all()

for error in errors:
    print(f"Property {error.property_id}: {error.error_message}")
```

### 2. Logs

```bash
# Backend logs (in terminal running main.py)
INFO:root:Starting AI analysis for 100 properties
INFO:root:AI analysis completed for property 1/100
...

# Check for errors
grep "ERROR" backend.log
```

### 3. Database Queries

```sql
-- Check AI analysis coverage
SELECT
    COUNT(DISTINCT p.id) as total_properties,
    COUNT(DISTINCT ai.id) as analyzed_properties,
    ROUND(COUNT(DISTINCT ai.id)::numeric / COUNT(DISTINCT p.id) * 100, 2) as coverage_pct
FROM properties p
LEFT JOIN ai_analysis_results ai ON p.id = ai.property_id
WHERE p.upload_id = 'YOUR_JOB_ID';

-- View AI risk distribution
SELECT
    ai_risk_level,
    COUNT(*) as count,
    ROUND(AVG(ai_risk_confidence), 2) as avg_confidence
FROM ai_analysis_results
GROUP BY ai_risk_level
ORDER BY count DESC;

-- Find high-confidence power line detections
SELECT
    p.full_address,
    ai.power_line_distance_meters,
    ai.power_line_confidence
FROM ai_analysis_results ai
JOIN properties p ON ai.property_id = p.id
WHERE ai.power_lines_visible = true
  AND ai.power_line_confidence > 0.8
ORDER BY ai.power_line_distance_meters ASC;
```

## Troubleshooting

### Issue: "AI analysis started but no results"

**Solution:**
1. Check backend logs for errors
2. Verify API keys are set correctly
3. Ensure database connection is stable
4. Check if properties have valid coordinates

### Issue: "Image URLs not loading in frontend"

**Solution:**
1. Verify imagery provider API keys
2. Check CORS settings if using external image hosts
3. Confirm image URLs in database are accessible
4. Try different imagery provider

### Issue: "Low AI confidence scores"

**Solution:**
1. Image quality may be poor (zoom level, resolution)
2. Try different imagery providers
3. Consider training custom models on your specific use case
4. Adjust confidence thresholds in risk calculation

### Issue: "Slow processing speed"

**Solution:**
1. Increase `max_workers` in `process_ai_analysis()`
2. Use local ML models instead of API calls
3. Implement GPU acceleration
4. Add more caching layers
5. Use batch processing for images

## Future Enhancements

### 1. Additional AI Features

- **Roof Condition Analysis** - Detect roof age, material, damage
- **Vegetation Coverage** - Measure tree coverage, landscaping
- **Flood Risk from Imagery** - Detect proximity to water bodies
- **Historical Change Detection** - Compare imagery over time
- **3D Building Detection** - Extract building height and volume

### 2. Model Improvements

- **Ensemble Models** - Combine multiple models for better accuracy
- **Active Learning** - Allow users to correct predictions, retrain
- **Confidence Calibration** - Improve reliability of confidence scores
- **Multi-modal Fusion** - Combine imagery with GIS data

### 3. Performance Optimizations

- **Image Preprocessing Pipeline** - Resize, normalize before storage
- **Vector Similarity Search** - Find similar properties instantly
- **Real-time Processing** - Stream results as they complete
- **Incremental Updates** - Only reprocess changed properties

## Cost Analysis

### OpenAI Vision API (Current)
- **Per Property:** ~$0.02 (2 images @ $0.01 each)
- **100 properties:** $2.00
- **1,000 properties:** $20.00
- **10,000 properties:** $200.00

### Local GPU Model (Recommended for >1,000 properties)
- **Hardware:** NVIDIA RTX 4090 (~$1,600)
- **Processing:** 100 properties/hour
- **Cost per property:** $0.00 (after initial investment)
- **Break-even:** ~8,000 properties vs OpenAI

### Google Cloud Vision API
- **Per Image:** $0.0015 (first 1,000), $0.0006 (1,000-5M)
- **100 properties:** $0.30
- **1,000 properties:** $2.40
- **10,000 properties:** $15.00

## Security Considerations

1. **API Key Protection:**
   - Never commit API keys to version control
   - Use environment variables or secret managers
   - Rotate keys regularly

2. **Image Storage:**
   - Consider privacy when storing property images
   - Implement access controls on image URLs
   - Set expiration times for cached images

3. **Rate Limiting:**
   - Implement user-level rate limits
   - Monitor for abuse patterns
   - Set maximum properties per upload

4. **Data Validation:**
   - Sanitize all input coordinates
   - Validate image URLs before fetching
   - Check file sizes before processing

## Support & Contact

For questions or issues:
1. Check logs in `backend/` directory
2. Review this documentation
3. Consult codebase comments in service files
4. File issues in project repository

---

**Last Updated:** 2025
**Version:** 1.0
**Author:** Property Analysis System
