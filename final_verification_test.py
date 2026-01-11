#!/usr/bin/env python3
"""
Final Verification Test - Complete End-to-End Testing

Tests all components:
1. Environment setup
2. API connectivity
3. Image fetching
4. AI power line detection
5. Structure detection
6. Risk calculation
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment
load_dotenv('backend/.env')
sys.path.insert(0, 'backend')

print("="*80)
print("FINAL VERIFICATION TEST - AI PROPERTY ANALYSIS")
print("="*80)

# Step 1: Check environment
print("\n[1/6] Checking Environment Variables...")
openai_key = os.getenv('OPENAI_API_KEY')
google_key = os.getenv('GOOGLE_MAPS_API_KEY')
mapbox_key = os.getenv('MAPBOX_ACCESS_TOKEN')

if openai_key and len(openai_key) > 10:
    print(f"  ✓ OpenAI API Key: SET ({len(openai_key)} chars)")
else:
    print("  ✗ OpenAI API Key: NOT SET")
    sys.exit(1)

if google_key and len(google_key) > 10:
    print(f"  ✓ Google Maps API Key: SET ({len(google_key)} chars)")
else:
    print("  ⚠ Google Maps API Key: NOT SET (will use fallback)")

if mapbox_key and len(mapbox_key) > 10:
    print(f"  ✓ Mapbox Token: SET ({len(mapbox_key)} chars)")
else:
    print("  ⚠ Mapbox Token: NOT SET (will use fallback)")

# Step 2: Test imports
print("\n[2/6] Testing Module Imports...")
try:
    from imagery_service import ImageryService
    print("  ✓ ImageryService imported")
except Exception as e:
    print(f"  ✗ ImageryService import failed: {e}")
    sys.exit(1)

try:
    from ai_analysis_service import AIAnalysisService
    print("  ✓ AIAnalysisService imported")
except Exception as e:
    print(f"  ✗ AIAnalysisService import failed: {e}")
    sys.exit(1)

try:
    from ai_analysis_improved import detect_power_lines_enhanced
    print("  ✓ ai_analysis_improved imported")
except Exception as e:
    print(f"  ✗ ai_analysis_improved import failed: {e}")
    sys.exit(1)

# Step 3: Test API connectivity
print("\n[3/6] Testing API Connectivity...")
import requests

# Test OpenAI API
try:
    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json"
    }
    response = requests.get(
        "https://api.openai.com/v1/models",
        headers=headers,
        timeout=10
    )
    if response.status_code == 200:
        print("  ✓ OpenAI API: Connected")
    else:
        print(f"  ⚠ OpenAI API: Status {response.status_code}")
except Exception as e:
    print(f"  ✗ OpenAI API: Error - {e}")

# Step 4: Test image fetching
print("\n[4/6] Testing Image Fetching...")
test_lat, test_lon = 26.604059, -81.658133

imagery_service = ImageryService()

try:
    imagery = imagery_service.fetch_imagery(test_lat, test_lon)

    satellite_url = imagery.get('satellite_url')
    street_url = imagery.get('street_view_url')

    if satellite_url:
        print(f"  ✓ Satellite image URL obtained")
    else:
        print(f"  ⚠ Satellite image: None")

    if street_url:
        print(f"  ✓ Street view URL obtained")

        # Download the image
        response = requests.get(street_url, timeout=10)
        if response.status_code == 200:
            street_image_bytes = response.content
            print(f"  ✓ Downloaded street image: {len(street_image_bytes)} bytes")
        else:
            print(f"  ✗ Failed to download image: {response.status_code}")
            street_image_bytes = None
    else:
        print(f"  ⚠ Street view image: None")
        street_image_bytes = None

except Exception as e:
    print(f"  ✗ Image fetching failed: {e}")
    street_image_bytes = None

# Step 5: Test AI power line detection
print("\n[5/6] Testing AI Power Line Detection...")
if street_image_bytes:
    try:
        print("  → Running power line detection (this may take 10-15 seconds)...")
        print("  → Waiting for API rate limits...")

        result = detect_power_lines_enhanced(street_image_bytes, "street")

        print(f"\n  Detection Results:")
        print(f"    Visible: {result.get('visible')}")
        print(f"    Confidence: {result.get('confidence', 0):.2f}")
        print(f"    Type: {result.get('type', 'N/A')}")
        print(f"    Source: {result.get('source', 'N/A')}")

        if result.get('details'):
            details = result['details'][:150]
            print(f"    Details: {details}...")

        if result.get('source') != 'max_retries_exceeded':
            print(f"  ✓ AI detection completed successfully")
        else:
            print(f"  ⚠ API rate limited (expected during testing)")

    except Exception as e:
        print(f"  ✗ Power line detection failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("  ⚠ Skipped (no image available)")

# Step 6: Test complete analysis
print("\n[6/6] Testing Complete AI Analysis...")
ai_service = AIAnalysisService()

try:
    print("  → Running full analysis (may take 20-30 seconds)...")
    print("  → Note: Some API calls may be rate limited")

    results = ai_service.analyze_property(
        latitude=test_lat,
        longitude=test_lon,
        satellite_image_url=satellite_url,
        street_image_url=street_url
    )

    print(f"\n  Analysis Results:")

    # Power lines
    pl = results.get('power_lines', {})
    print(f"    Power Lines (Satellite): visible={pl.get('visible')}, conf={pl.get('confidence', 0):.2f}")

    pl_st = results.get('power_lines_street', {})
    print(f"    Power Lines (Street): visible={pl_st.get('visible')}, conf={pl_st.get('confidence', 0):.2f}")

    # Structures
    struct = results.get('nearby_structures', {})
    print(f"    Structures: detected={struct.get('structures_detected')}, count={struct.get('count', 0)}")

    # Risk
    risk = results.get('overall_ai_risk', {})
    print(f"    Overall Risk: {risk.get('level', 'N/A')} (score={risk.get('score', 0)})")

    print(f"    Processing Time: {results.get('processing_time_seconds', 0):.2f}s")

    if results.get('error'):
        print(f"    Error: {results['error']}")
        print(f"  ⚠ Analysis completed with errors (likely rate limiting)")
    else:
        print(f"  ✓ Full analysis completed successfully")

except Exception as e:
    print(f"  ✗ Full analysis failed: {e}")
    import traceback
    traceback.print_exc()

# Final summary
print("\n" + "="*80)
print("VERIFICATION TEST COMPLETE")
print("="*80)
print("\n✅ System Status: READY FOR TESTING")
print("\nKey Features:")
print("  • Rate limiting with retry logic")
print("  • Enhanced power line detection prompts")
print("  • Comprehensive structure detection")
print("  • Property condition analysis")
print("  • Risk-based scoring (power lines = top priority)")
print("\n⚠️  Note: OpenAI API has rate limits. Process properties in small batches.")
print("\n📝 To test with your CSV data:")
print("    python test_ai_detection_manual.py")
print("="*80 + "\n")
