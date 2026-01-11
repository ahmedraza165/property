"""
Visual test with sample CSV data.
Shows images FIRST, then runs AI analysis with detailed stats.
"""

import os
import pandas as pd
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Load environment variables
load_dotenv('.env')

def get_first_csv_property():
    """Get first property from CSV."""
    csv_path = "/Users/ahmadraza/Documents/property-anyslis/backend/Export_Contacts_Cleaned Target Best Lehigh_Dec_2025_5_41_PM.csv"

    try:
        df = pd.read_csv(csv_path)
        first_row = df.iloc[0]

        # Get address components
        address = f"{first_row.get('Street Address', '')}, {first_row.get('City', '')}, {first_row.get('State', '')} {first_row.get('Zip', '')}"

        return {
            'address': address.strip(),
            'street': first_row.get('Street Address', ''),
            'city': first_row.get('City', ''),
            'state': first_row.get('State', ''),
            'zip': first_row.get('Zip', ''),
            'full_data': first_row.to_dict()
        }
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return None

def geocode_address(address):
    """Geocode address to get coordinates."""
    print(f"🌍 Geocoding: {address}")

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {'User-Agent': 'PropertyAnalysis/1.0'}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            print(f"✅ Coordinates: {lat}, {lon}")
            return lat, lon
        else:
            print("❌ No coordinates found")
            return None, None
    except Exception as e:
        print(f"❌ Geocoding error: {e}")
        return None, None

def download_marked_satellite(lat, lon, output_path):
    """Download satellite image with red marker at multiple zoom levels."""

    mapbox_token = os.getenv('MAPBOX_ACCESS_TOKEN')
    if not mapbox_token:
        print("❌ No Mapbox token")
        return None

    # Use zoom 18 for balanced view (current system default)
    zoom = 18
    marker = f"pin-s+ff0000({lon},{lat})"

    url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{marker}/{lon},{lat},{zoom},0/800x800@2x?access_token={mapbox_token}"

    print(f"📡 Downloading satellite image (zoom {zoom})...")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"✅ Saved: {output_path}")
        print(f"   Size: {len(response.content):,} bytes")
        return output_path
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def download_street_view(lat, lon, output_path):
    """Download street view image."""

    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ No Google API key")
        return None

    url = f"https://maps.googleapis.com/maps/api/streetview?size=800x600&location={lat},{lon}&key={api_key}"

    print(f"📸 Downloading street view...")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"✅ Saved: {output_path}")
        print(f"   Size: {len(response.content):,} bytes")
        return output_path
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def display_images(satellite_path, street_path):
    """Display both images for user review."""

    print()
    print("="*80)
    print("📸 SHOWING IMAGES FOR YOUR REVIEW")
    print("="*80)
    print()

    if satellite_path and os.path.exists(satellite_path):
        print("🛰️  Opening SATELLITE image...")
        try:
            img = Image.open(satellite_path)
            img.show()
            print(f"   ✓ Satellite: {satellite_path}")
        except Exception as e:
            print(f"   ❌ Could not display: {e}")

    if street_path and os.path.exists(street_path):
        print("📸 Opening STREET VIEW image...")
        try:
            img = Image.open(street_path)
            img.show()
            print(f"   ✓ Street View: {street_path}")
        except Exception as e:
            print(f"   ❌ Could not display: {e}")

    print()
    print("="*80)
    print("⏸️  PAUSED - Review the images above")
    print("="*80)
    print()
    print("What you should see:")
    print("  🛰️  SATELLITE: Red marker showing exact property location")
    print("  📸 STREET VIEW: Ground-level view of the property")
    print()

def main():
    """Main test function."""

    print("="*80)
    print("VISUAL PROPERTY ANALYSIS TEST")
    print("="*80)
    print()

    # Step 1: Get property from CSV
    print("Step 1: Reading CSV data...")
    property_data = get_first_csv_property()

    if not property_data:
        print("❌ Could not read CSV")
        return

    print(f"✅ Property: {property_data['address']}")
    print(f"   Street: {property_data['street']}")
    print(f"   City: {property_data['city']}, {property_data['state']} {property_data['zip']}")
    print()

    # Step 2: Geocode
    print("Step 2: Getting coordinates...")
    lat, lon = geocode_address(property_data['address'])

    if not lat or not lon:
        print("❌ Could not geocode address")
        return

    print()

    # Step 3: Download images
    print("Step 3: Downloading images...")
    print()

    satellite_path = "/Users/ahmadraza/Documents/property-anyslis/test_sample_satellite.jpg"
    street_path = "/Users/ahmadraza/Documents/property-anyslis/test_sample_street.jpg"

    sat_result = download_marked_satellite(lat, lon, satellite_path)
    street_result = download_street_view(lat, lon, street_path)

    # Step 4: Display images for review
    display_images(sat_result, street_result)

    # Ask user if they want to proceed
    print("Would you like to:")
    print("  1. Proceed with AI analysis using these images")
    print("  2. Change zoom level / get different images")
    print("  3. Exit")
    print()
    print("Type your choice (1/2/3) or just press ENTER to proceed with AI analysis:")

    return {
        'property': property_data,
        'coordinates': (lat, lon),
        'satellite_image': sat_result,
        'street_image': street_result
    }

if __name__ == "__main__":
    result = main()

    if result:
        print()
        print("="*80)
        print("✅ Images ready for review!")
        print("="*80)
        print()
        print("Next steps:")
        print("  1. Review the satellite image (shows red marker at property)")
        print("  2. Review the street view image (ground-level view)")
        print("  3. Let me know if you want to:")
        print("     - Proceed with AI analysis")
        print("     - Change zoom level")
        print("     - Try different angle for street view")
        print()
        print("Files saved:")
        print(f"  🛰️  {result['satellite_image']}")
        print(f"  📸 {result['street_image']}")
