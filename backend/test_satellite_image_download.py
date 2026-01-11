"""
Test script to download satellite/aerial imagery for AI analysis.
This shows the top-down view that the AI uses to detect power lines and structures.
"""

import os
import requests
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO

# Load environment variables
load_dotenv('.env')

def download_satellite_image(address: str, output_path: str):
    """Download a satellite image from Mapbox for testing."""

    mapbox_token = os.getenv('MAPBOX_ACCESS_TOKEN')
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')

    if not mapbox_token:
        print("❌ ERROR: MAPBOX_ACCESS_TOKEN not found in .env file")
        return None

    print(f"📍 Address: {address}")
    print(f"🔑 Mapbox Token: {mapbox_token[:10]}...{mapbox_token[-4:]}")
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

    # Step 2: Download Satellite image from Mapbox
    print("🛰️  Step 2: Downloading satellite imagery from Mapbox...")

    # Mapbox Static Images API
    # Higher zoom level shows more area (zoomed out)
    # Lower zoom level shows less area (zoomed in)
    zoom_level = 18  # Good balance: shows property + surroundings
    width = 800
    height = 800

    satellite_url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{longitude},{latitude},{zoom_level},0/{width}x{height}@2x"
    satellite_params = {
        "access_token": mapbox_token
    }

    try:
        image_response = requests.get(satellite_url, params=satellite_params, timeout=30)
        image_response.raise_for_status()

        # Check if we got an actual image
        content_type = image_response.headers.get('Content-Type', '')

        if 'image' not in content_type:
            print(f"❌ Received non-image response: {content_type}")
            print(f"Response: {image_response.text[:200]}")
            return None

        print(f"✅ Downloaded satellite image: {len(image_response.content)} bytes")
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

        print("📊 Satellite Image Details:")
        print(f"   Size: {width}x{height} pixels")
        print(f"   Format: {format_name}")
        print(f"   Mode: {mode}")
        print(f"   Zoom Level: {zoom_level} (18 = detailed view, 16 = wider area)")
        print(f"   File size: {len(image_response.content):,} bytes")
        print()

        # Try to display the image
        print("🖼️  Opening satellite image for preview...")
        try:
            image.show()
            print("✅ Image displayed successfully!")
        except Exception as e:
            print(f"⚠️  Could not display image automatically: {e}")
            print(f"   Please open manually: {output_path}")

        return output_path

    except Exception as e:
        print(f"❌ Satellite image download error: {e}")
        import traceback
        traceback.print_exc()
        return None


def download_both_images(address: str):
    """Download both satellite and street view images."""

    print("="*80)
    print("DOWNLOADING IMAGES FOR AI ANALYSIS")
    print("="*80)
    print()

    # Download satellite image
    satellite_path = "/Users/ahmadraza/Documents/property-anyslis/test_satellite_image.jpg"
    print("📡 PART 1: SATELLITE IMAGE (Top-down aerial view)")
    print("-"*80)
    satellite_result = download_satellite_image(address, satellite_path)

    print()
    print("="*80)

    if satellite_result:
        print()
        print("✅ SUCCESS!")
        print()
        print(f"📁 Satellite image saved to: {satellite_result}")
        print()
        print("🤖 The AI model will analyze this SATELLITE image for:")
        print("   ✓ Power lines from above (transmission lines, corridors)")
        print("   ✓ Power line shadows on the ground")
        print("   ✓ Transmission towers (metal structures)")
        print("   ✓ Buildings and houses (roof view)")
        print("   ✓ Nearby structures and density")
        print("   ✓ Property layout and surroundings")
        print("   ✓ Vegetation and cleared areas")
        print()
        print("📏 Coverage Area:")
        print("   - Zoom 18: ~300-400m radius (detailed property view)")
        print("   - Shows property + immediate surroundings")
        print("   - Can see power lines, poles, towers if present")
        print()
        print("🔍 This top-down view is PERFECT for detecting:")
        print("   - Power line corridors (cleared paths)")
        print("   - Power line shadows (thin dark lines)")
        print("   - Distance from property to power lines")
        print("   - Nearby buildings and structures")
    else:
        print()
        print("❌ FAILED to download satellite image")
        print()


if __name__ == "__main__":
    # Test with the address from your CSV
    test_address = "909 monroe ave, Lehigh Acres, FL 33972"

    download_both_images(test_address)

    print()
    print("="*80)
    print("💡 IMAGE TYPE COMPARISON")
    print("="*80)
    print()
    print("🛰️  SATELLITE VIEW (Top-down):")
    print("   ✓ Best for: Power lines from above, structures, layout")
    print("   ✓ Shows: Entire property area, surroundings, aerial perspective")
    print("   ✓ Can detect: Transmission lines, towers, power corridors, shadows")
    print()
    print("📸 STREET VIEW (Ground level):")
    print("   ✓ Best for: Utility poles, overhead wires, property condition")
    print("   ✓ Shows: Front of property, street perspective")
    print("   ✓ Can detect: Power poles, overhead lines, transformers")
    print()
    print("🎯 BEST PRACTICE: Use BOTH images for complete analysis!")
    print("   - Satellite: Detects transmission lines, power corridors, overall layout")
    print("   - Street: Detects utility poles, overhead lines, property condition")
    print()
