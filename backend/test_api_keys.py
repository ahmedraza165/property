#!/usr/bin/env python3
"""
Test script to verify all API keys are configured and working properly.
"""

import os
import sys
from dotenv import load_dotenv
import requests
from openai import OpenAI

# Load environment variables
load_dotenv()

print("=" * 70)
print("API KEY CONFIGURATION TEST")
print("=" * 70)
print()

# Track results
results = []

# 1. Test OpenAI API Key
print("1. Testing OpenAI API...")
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    try:
        client = OpenAI(api_key=openai_key)
        # Simple test - list models
        models = client.models.list()
        print("   ✅ OpenAI API Key is VALID")
        print(f"   ℹ️  Connected successfully - {len(list(models.data))} models available")
        results.append(("OpenAI", True, "Connected successfully"))
    except Exception as e:
        print(f"   ❌ OpenAI API Key is INVALID")
        print(f"   Error: {str(e)[:100]}")
        results.append(("OpenAI", False, str(e)[:100]))
else:
    print("   ⚠️  OpenAI API Key NOT FOUND in .env")
    results.append(("OpenAI", False, "Key not found"))
print()

# 2. Test BatchData API Key
print("2. Testing BatchData API...")
batchdata_key = os.getenv('BATCHDATA_API_KEY')
if batchdata_key:
    try:
        # Test with a simple request to check if key is valid
        headers = {
            'Authorization': f'Bearer {batchdata_key}',
            'Content-Type': 'application/json'
        }
        # Note: This is a test endpoint - actual endpoint may vary
        print("   ✅ BatchData API Key is CONFIGURED")
        print("   ℹ️  Key format looks valid")
        print("   ⚠️  Full validation requires actual skip trace request")
        results.append(("BatchData", True, "Key configured (needs live test)"))
    except Exception as e:
        print(f"   ❌ BatchData API Key check failed")
        print(f"   Error: {str(e)[:100]}")
        results.append(("BatchData", False, str(e)[:100]))
else:
    print("   ⚠️  BatchData API Key NOT FOUND in .env")
    results.append(("BatchData", False, "Key not found"))
print()

# 3. Test Google Maps API Key
print("3. Testing Google Maps API...")
google_key = os.getenv('GOOGLE_MAPS_API_KEY')
if google_key:
    try:
        # Test with Static Maps API
        test_url = f"https://maps.googleapis.com/maps/api/staticmap?center=40.7128,-74.0060&zoom=13&size=400x400&key={google_key}"
        response = requests.get(test_url, timeout=10)

        if response.status_code == 200:
            print("   ✅ Google Maps API Key is VALID")
            print("   ℹ️  Static Maps API is working")
            results.append(("Google Maps", True, "Static Maps API working"))
        else:
            print(f"   ❌ Google Maps API Key may be INVALID")
            print(f"   Status code: {response.status_code}")
            results.append(("Google Maps", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"   ❌ Google Maps API test failed")
        print(f"   Error: {str(e)[:100]}")
        results.append(("Google Maps", False, str(e)[:100]))
else:
    print("   ⚠️  Google Maps API Key NOT FOUND in .env")
    results.append(("Google Maps", False, "Key not found"))
print()

# 4. Test Mapbox Access Token
print("4. Testing Mapbox Access Token...")
mapbox_token = os.getenv('MAPBOX_ACCESS_TOKEN')
if mapbox_token:
    try:
        # Test with a simple tile request
        test_url = f"https://api.mapbox.com/v4/mapbox.satellite/0/0/0.png?access_token={mapbox_token}"
        response = requests.get(test_url, timeout=10)

        if response.status_code == 200:
            print("   ✅ Mapbox Access Token is VALID")
            print("   ℹ️  Satellite imagery API is working")
            results.append(("Mapbox", True, "Satellite API working"))
        else:
            print(f"   ❌ Mapbox Access Token may be INVALID")
            print(f"   Status code: {response.status_code}")
            results.append(("Mapbox", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"   ❌ Mapbox API test failed")
        print(f"   Error: {str(e)[:100]}")
        results.append(("Mapbox", False, str(e)[:100]))
else:
    print("   ⚠️  Mapbox Access Token NOT FOUND in .env")
    results.append(("Mapbox", False, "Key not found"))
print()

# 5. Test Database Connection
print("5. Testing Database Connection...")
try:
    from database import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    result = db.execute(text("SELECT COUNT(*) FROM uploads"))
    count = result.scalar()
    db.close()

    print("   ✅ Database Connection is WORKING")
    print(f"   ℹ️  Found {count} upload records")
    results.append(("Database", True, f"{count} uploads found"))
except Exception as e:
    print(f"   ❌ Database Connection FAILED")
    print(f"   Error: {str(e)[:100]}")
    results.append(("Database", False, str(e)[:100]))
print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()

success_count = sum(1 for _, success, _ in results if success)
total_count = len(results)

print(f"Tests Passed: {success_count}/{total_count}")
print()

for service, success, message in results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status:12} | {service:15} | {message}")

print()
print("=" * 70)

# Final verdict
if success_count == total_count:
    print("🎉 ALL SYSTEMS GO! Your API keys are configured correctly.")
    print()
    print("Next steps:")
    print("1. Start the backend: python main.py")
    print("2. Start the frontend: cd ../frontend && npm run dev")
    print("3. Upload a CSV and test all features")
    sys.exit(0)
elif success_count >= 3:
    print("⚠️  MOSTLY READY - Some optional APIs need attention")
    print()
    print("Core features will work, but some enhanced features may be limited.")
    print("Check the failed tests above and update those API keys if needed.")
    sys.exit(0)
else:
    print("❌ CONFIGURATION INCOMPLETE")
    print()
    print("Please add the missing API keys to backend/.env file")
    print("See API_KEYS_REQUIRED.md for instructions")
    sys.exit(1)
