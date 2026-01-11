"""
Test script to download and display a Google Street View image.
This shows exactly what image the AI model receives for analysis.
"""

import os
import sys
import requests
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

# Load environment variables
load_dotenv('.env')

def download_street_view_image(address: str, output_path: str):
    """Download a Google Street View image for testing."""

    api_key = os.getenv('GOOGLE_MAPS_API_KEY')

    if not api_key:
        print("❌ ERROR: GOOGLE_MAPS_API_KEY not found in .env file")
        return None

    print(f"📍 Address: {address}")
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
    print()

    # Step 1: Geocode the address to get coordinates
    print("🌍 Step 1: Geocoding address...")
    geocode_url = "https://nominatim.openstreetmap.org/search"
    geocode_params = {
        "q": address,
        "format": "json",
        "limit": 1
    }

    headers = {'User-Agent': 'PropertyAnalysis/1.0'}

    try:
        geocode_response = requests.get(geocode_url, params=geocode_params, headers=headers, timeout=10)
        geocode_response.raise_for_status()
        geocode_data = geocode_response.json()

        if not geocode_data:
            print(f"❌ Could not geocode address: {address}")
            return None

        latitude = float(geocode_data[0]['lat'])
        longitude = float(geocode_data[0]['lon'])

        print(f"✅ Coordinates: {latitude}, {longitude}")
        print()

    except Exception as e:
        print(f"❌ Geocoding error: {e}")
        return None

    # Step 2: Download Street View image
    print("📸 Step 2: Downloading Google Street View image...")

    street_view_url = "https://maps.googleapis.com/maps/api/streetview"
    street_view_params = {
        "size": "640x640",
        "location": f"{latitude},{longitude}",
        "fov": 90,  # Field of view
        "pitch": 10,  # Slightly tilted up to see power lines
        "key": api_key
    }

    try:
        image_response = requests.get(street_view_url, params=street_view_params, timeout=30)
        image_response.raise_for_status()

        # Check if we got an actual image or an error
        content_type = image_response.headers.get('Content-Type', '')

        if 'image' not in content_type:
            print(f"❌ Received non-image response: {content_type}")
            print(f"Response: {image_response.text[:200]}")
            return None

        print(f"✅ Downloaded image: {len(image_response.content)} bytes")
        print(f"   Content-Type: {content_type}")
        print()

        # Save the image
        with open(output_path, 'wb') as f:
            f.write(image_response.content)

        print(f"💾 Saved to: {output_path}")
        print()

        # Display image info
        image = Image.open(BytesIO(image_response.content))
        width, height = image.size
        format_name = image.format
        mode = image.mode

        print("📊 Image Details:")
        print(f"   Size: {width}x{height} pixels")
        print(f"   Format: {format_name}")
        print(f"   Mode: {mode}")
        print(f"   File size: {len(image_response.content):,} bytes")
        print()

        # Try to display the image
        print("🖼️  Opening image for preview...")
        try:
            image.show()
            print("✅ Image displayed successfully!")
        except Exception as e:
            print(f"⚠️  Could not display image automatically: {e}")
            print(f"   Please open manually: {output_path}")

        return output_path

    except Exception as e:
        print(f"❌ Street View download error: {e}")
        return None


if __name__ == "__main__":
    # Test with the address from your CSV
    test_address = "909 monroe ave, Lehigh Acres, FL 33972"
    output_file = "/Users/ahmadraza/Documents/property-anyslis/test_street_view_image.jpg"

    print("="*80)
    print("GOOGLE STREET VIEW IMAGE TEST")
    print("="*80)
    print()

    result = download_street_view_image(test_address, output_file)

    if result:
        print()
        print("="*80)
        print("✅ SUCCESS!")
        print("="*80)
        print()
        print(f"📁 Image saved to: {result}")
        print()
        print("🤖 This is the EXACT image that the AI model will analyze for:")
        print("   - Power lines (overhead, in front, nearby, far)")
        print("   - Utility poles and transformers")
        print("   - Buildings, houses, garages")
        print("   - Property condition")
        print("   - Road condition")
        print()
        print("You can now open this image to see what the AI sees!")
    else:
        print()
        print("="*80)
        print("❌ FAILED")
        print("="*80)
        print()
        print("Could not download the Street View image.")
        print("Please check your GOOGLE_MAPS_API_KEY in backend/.env")
