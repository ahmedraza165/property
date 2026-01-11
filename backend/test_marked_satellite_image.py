"""
Download satellite image with marker showing the exact property location.
This helps the AI identify which building/lot is the target property.
"""

import os
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Load environment variables
load_dotenv('.env')

def download_marked_satellite_image(address: str, output_path: str):
    """Download satellite image with property marker overlay."""

    mapbox_token = os.getenv('MAPBOX_ACCESS_TOKEN')

    if not mapbox_token:
        print("❌ ERROR: MAPBOX_ACCESS_TOKEN not found in .env file")
        return None

    print(f"📍 Address: {address}")
    print()

    # Step 1: Geocode
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

    # Step 2: Download close-up satellite image (zoomed IN)
    print("🛰️  Step 2: Downloading CLOSE-UP satellite imagery...")

    # ZOOM LEVEL OPTIONS:
    # 20 = VERY CLOSE (shows ~50m radius) - structures very clear
    # 19 = Very close (shows ~100m radius) ✓ BEST FOR CLEAR STRUCTURES
    # 18 = Close (shows ~200m radius)
    # 17 = Medium (shows ~400m radius)
    # 16 = Wide (shows ~800m radius)

    zoom_level = 19  # Very close - clear structures, focused view
    width = 800
    height = 800

    # Use Mapbox Static API with simple marker overlay
    # Just one simple red dot marker at the property location
    # Format: pin-SIZE-SYMBOL+COLOR(lon,lat)

    # Create marker specification - simple small red circle
    marker_spec = f"pin-s+ff0000({longitude},{latitude})"  # Small red pin

    satellite_url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{marker_spec}/{longitude},{latitude},{zoom_level},0/{width}x{height}@2x"
    satellite_params = {
        "access_token": mapbox_token
    }

    try:
        print(f"   Zoom level: {zoom_level} (close-up view for clear structures)")
        print(f"   Image size: {width}x{height} pixels")
        print(f"   Coverage: ~100-150 meter radius")
        print(f"   Marker: Simple red dot at property center")
        print()

        image_response = requests.get(satellite_url, params=satellite_params, timeout=30)
        image_response.raise_for_status()

        content_type = image_response.headers.get('Content-Type', '')

        if 'image' not in content_type:
            print(f"❌ Received non-image response: {content_type}")
            print(f"Response: {image_response.text[:200]}")
            return None

        print(f"✅ Downloaded satellite image with marker: {len(image_response.content)} bytes")
        print()

        # Load image - marker already embedded by Mapbox
        image = Image.open(BytesIO(image_response.content))

        # Save the image directly (marker is already in the image from Mapbox)
        image.save(output_path, 'JPEG', quality=95)
        print(f"💾 Saved marked image to: {output_path}")
        print()

        # Display image info
        width, height = image.size
        format_name = image.format
        mode = image.mode

        print("📊 Final Image Details:")
        print(f"   Size: {width}x{height} pixels")
        print(f"   Format: {format_name}")
        print(f"   Mode: {mode}")
        print(f"   Zoom Level: {zoom_level} (close-up for clear structures)")
        print(f"   Marker: Simple RED dot at property center")
        print()

        # Display the image
        print("🖼️  Opening marked image for preview...")
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


if __name__ == "__main__":
    test_address = "909 monroe ave, Lehigh Acres, FL 33972"
    output_file = "/Users/ahmadraza/Documents/property-anyslis/test_marked_satellite.jpg"

    print("="*80)
    print("SATELLITE IMAGE WITH PROPERTY MARKER")
    print("="*80)
    print()

    result = download_marked_satellite_image(test_address, output_file)

    if result:
        print()
        print("="*80)
        print("✅ SUCCESS!")
        print("="*80)
        print()
        print(f"📁 Marked satellite image saved to: {result}")
        print()
        print("🎯 What the AI will see:")
        print("   ✓ Simple RED DOT marker at exact property location")
        print("   ✓ CLOSE-UP view (~100-150m radius)")
        print("   ✓ CLEAR structures - buildings, houses, roofs visible in detail")
        print("   ✓ Property boundaries and lot details")
        print("   ✓ Nearby buildings and structures")
        print("   ✓ Power lines and infrastructure (if present)")
        print()
        print("🤖 The AI can now:")
        print("   1. See which exact lot/building has the red marker")
        print("   2. See structures in HIGH DETAIL")
        print("   3. Count nearby buildings clearly")
        print("   4. Detect power line shadows or corridors")
        print("   5. Measure distances accurately from marked property")
        print()
        print("📏 Coverage Area:")
        print("   - Zoom 19 = ~100-150 meter radius (CLOSE-UP)")
        print("   - Buildings and structures visible in detail")
        print("   - Perfect for identifying exact property and immediate surroundings")
        print()
    else:
        print()
        print("="*80)
        print("❌ FAILED")
        print("="*80)
