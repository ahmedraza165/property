#!/usr/bin/env python3
"""
Simple test to verify AI detection works with actual property data.
"""

import os
import sys

# Load environment variables from backend/.env
from dotenv import load_dotenv
load_dotenv('backend/.env')

# Add backend to path
sys.path.insert(0, 'backend')

from ai_analysis_improved import detect_power_lines_enhanced
import requests
import base64

# Test addresses from CSV
TEST_COORDINATES = [
    {"address": "Lehigh Acres, FL", "lat": 26.604059, "lon": -81.658133},
    {"address": "Lehigh Acres, FL", "lat": 26.577682, "lon": -81.684448},
]

def get_google_street_view(lat, lon, api_key):
    """Get Google Street View image."""
    url = f"https://maps.googleapis.com/maps/api/streetview"
    params = {
        "size": "600x400",
        "location": f"{lat},{lon}",
        "key": api_key
    }

    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
        return response.content
    return None

print("="*80)
print("SIMPLE AI DETECTION TEST")
print("="*80)

# Check API keys
openai_key = os.getenv('OPENAI_API_KEY')
google_key = os.getenv('GOOGLE_MAPS_API_KEY')

print(f"\n✓ OpenAI API Key: {'SET' if openai_key else 'NOT SET'}")
print(f"✓ Google Maps API Key: {'SET' if google_key else 'NOT SET'}")

if not openai_key:
    print("\n❌ ERROR: OPENAI_API_KEY not set in environment")
    print("Please set it in backend/.env file")
    sys.exit(1)

if not google_key:
    print("\n⚠️  WARNING: GOOGLE_MAPS_API_KEY not set - will use OpenStreetMap")

# Test on first property
test_prop = TEST_COORDINATES[0]
print(f"\n{'='*80}")
print(f"Testing: {test_prop['address']}")
print(f"Coordinates: {test_prop['lat']}, {test_prop['lon']}")
print(f"{'='*80}")

# Get street view image
print("\n📸 Fetching Google Street View image...")
if google_key:
    street_img = get_google_street_view(test_prop['lat'], test_prop['lon'], google_key)
    if street_img:
        print(f"✓ Downloaded {len(street_img)} bytes")

        # Test power line detection
        print("\n🔌 Analyzing for power lines...")
        try:
            result = detect_power_lines_enhanced(street_img, "street")

            print("\n" + "="*80)
            print("POWER LINE DETECTION RESULTS")
            print("="*80)
            print(f"Visible: {result.get('visible')}")
            print(f"Confidence: {result.get('confidence', 0):.2f}")
            print(f"Type: {result.get('type', 'N/A')}")
            print(f"Proximity: {result.get('proximity', 'N/A')}")
            print(f"Source: {result.get('source', 'N/A')}")
            print(f"\nDetails: {result.get('details', 'N/A')}")
            print("="*80)

            if result.get('visible'):
                print("\n✅ SUCCESS - Power lines detected!")
            else:
                print("\n❌ No power lines detected")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Failed to download street view image")
else:
    print("❌ Cannot test without Google Maps API key")

print("\n" + "="*80)
print("Test complete")
print("="*80 + "\n")
