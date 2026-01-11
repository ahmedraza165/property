#!/usr/bin/env python3
"""
Direct test of OpenAI Vision API to diagnose the issue.
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Test coordinates from CSV
lat = 26.581144292187
lon = -81.60813552774

# Get API key
api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key present: {bool(api_key)}")
print(f"API Key prefix: {api_key[:20] if api_key else 'NOT FOUND'}...")
print()

# Get image URLs
satellite_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom=18&size=800x800&maptype=satellite&markers=color:red%7C{lat},{lon}&key={os.getenv('GOOGLE_MAPS_API_KEY')}"
street_url = f"https://maps.googleapis.com/maps/api/streetview?size=800x600&location={lat},{lon}&heading=0&fov=90&pitch=0&key={os.getenv('GOOGLE_MAPS_API_KEY')}"

print("IMAGE URLS:")
print(f"Satellite: {satellite_url}")
print(f"Street: {street_url}")
print()

# Test 1: Simple vision test with just one image
print("="*80)
print("TEST 1: Simple image description (1 image)")
print("="*80)

simple_prompt = """Look at this satellite image and tell me what you see.
Just describe the main features in 2-3 sentences."""

payload = {
    "model": "gpt-4o",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": simple_prompt},
            {"type": "image_url", "image_url": {"url": satellite_url, "detail": "high"}}
        ]
    }],
    "max_tokens": 300
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

try:
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        print(f"\n✅ SUCCESS - Response:\n{content}")
    else:
        print(f"\n❌ ERROR Response:")
        print(response.text)

except Exception as e:
    print(f"\n❌ EXCEPTION: {str(e)}")

print("\n" + "="*80)
print("TEST 2: JSON format request (what the system uses)")
print("="*80)

json_prompt = """Analyze this satellite image and respond with ONLY a JSON object:
{"description": "what you see", "has_buildings": true/false, "has_roads": true/false}"""

payload2 = {
    "model": "gpt-4o",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": json_prompt},
            {"type": "image_url", "image_url": {"url": satellite_url, "detail": "high"}}
        ]
    }],
    "max_tokens": 300,
    "temperature": 0.2
}

try:
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload2,
        timeout=30
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        print(f"\n✅ SUCCESS - Response:\n{content}")

        # Try to parse as JSON
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            print(f"\n✅ JSON Parse SUCCESS:")
            print(json.dumps(parsed, indent=2))
        except:
            print(f"\n⚠️  Could not parse as JSON")
    else:
        print(f"\n❌ ERROR Response:")
        print(response.text)

except Exception as e:
    print(f"\n❌ EXCEPTION: {str(e)}")

print("\n" + "="*80)
print("TEST 3: Property analysis request (simplified)")
print("="*80)

property_prompt = """Analyze this satellite image of a property and provide assessment.

Respond with ONLY a JSON object:
{
  "power_lines": {"visible": true/false, "confidence": 0.0-1.0},
  "road_condition": {"type": "PAVED|DIRT|GRAVEL|UNKNOWN", "confidence": 0.0-1.0},
  "nearby_structures": {"count": number, "confidence": 0.0-1.0}
}"""

payload3 = {
    "model": "gpt-4o",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": property_prompt},
            {"type": "image_url", "image_url": {"url": satellite_url, "detail": "high"}}
        ]
    }],
    "max_tokens": 500,
    "temperature": 0.2
}

try:
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload3,
        timeout=30
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        print(f"\n✅ SUCCESS - Response:\n{content}")

        # Try to parse as JSON
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            print(f"\n✅ JSON Parse SUCCESS:")
            print(json.dumps(parsed, indent=2))
        except Exception as e:
            print(f"\n⚠️  Could not parse as JSON: {e}")
    else:
        print(f"\n❌ ERROR Response:")
        print(response.text)

except Exception as e:
    print(f"\n❌ EXCEPTION: {str(e)}")

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
