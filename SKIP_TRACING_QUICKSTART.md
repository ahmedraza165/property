# Skip Tracing - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Get Your API Key

1. Visit [BatchData.com](https://batchdata.com)
2. Sign up for an account
3. Copy your API key from the dashboard

### Step 2: Configure Backend

Add your API key to `backend/.env`:

```bash
echo 'BATCHDATA_API_KEY=your_api_key_here' >> backend/.env
```

### Step 3: Start the Application

If not already running:

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Step 4: Use Skip Tracing

1. **Upload CSV** with property addresses
2. Wait for risk analysis to complete
3. Click **"Find Owners"** button on results page
4. Owner information appears automatically as it completes
5. Click **"Export CSV"** to download data including owner info

## 📊 What You Get

For each property owner:
- ✅ Full name (first, middle, last)
- ✅ Up to 3 phone numbers (primary, mobile, alternate)
- ✅ Up to 2 email addresses
- ✅ Complete mailing address
- ✅ Owner type (Individual, LLC, Trust, etc.)
- ✅ Owner-occupied status
- ✅ Confidence score (76-97% accuracy)

## 💰 Pricing

BatchData charges **$0.009 - $0.02 per property**

Example costs:
- 100 properties: ~$1.50
- 500 properties: ~$7.50
- 1,000 properties: ~$15.00
- 5,000 properties: ~$75.00

## 🎯 Pro Tips

1. **Filter first, trace second**: Only trace properties that meet your investment criteria to save money
2. **Automatic deduplication**: Already-traced properties are skipped automatically
3. **Concurrent processing**: 5 properties are processed simultaneously for speed
4. **Check confidence scores**: Higher scores = more reliable contact information

## 🔧 Troubleshooting

### "No API key configured"
→ Add `BATCHDATA_API_KEY` to `backend/.env` and restart backend

### "Owner not found"
→ Normal! Not all properties have public owner records available

### "Slow processing"
→ Check your BatchData tier and rate limits

## 📖 Full Documentation

See [SKIP_TRACING_README.md](SKIP_TRACING_README.md) for:
- Complete API reference
- Database schema details
- Advanced configuration
- Cost optimization strategies
- Compliance guidelines

## 🎉 Ready to Go!

Your skip tracing system is fully set up and production-ready. Just add your BatchData API key and start finding property owners!

**Without API Key**: The system works in fallback mode with limited public records (not recommended for production).

**With API Key**: Get 76-97% accurate owner contact information from BatchData's verified database.
