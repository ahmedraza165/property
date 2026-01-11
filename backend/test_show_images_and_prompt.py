"""
Test script to:
1. Get one property from CSV
2. Download both satellite and street view images
3. Display both images
4. Show the exact prompt being sent to AI
"""

import os
import sys
import csv
import requests
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import json

# Load environment
load_dotenv('.env')

sys.path.insert(0, os.path.dirname(__file__))

from geocoding_service import GeocodingService
from imagery_service import ImageryService

def main():
    print("="*80)
    print("🔍 AI ANALYSIS IMAGE & PROMPT VIEWER")
    print("="*80)
    print()

    # Read first property from CSV
    csv_path = "/Users/ahmadraza/Documents/property-anyslis/backend/Export_Contacts_Cleaned Target Best Lehigh_Dec_2025_5_41_PM.csv"

    print("📄 Reading CSV file...")
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        properties = list(reader)

    # Get first property
    prop = properties[0]

    print(f"\n✅ Selected Property:")
    print(f"   Name: {prop['Name']}")
    print(f"   Address: {prop['Street address']}, {prop['City']}, {prop['State']} {prop['Postal Code']}")
    print()

    # Geocode address
    print("🌍 Geocoding address...")
    geocoding_service = GeocodingService()

    full_address = f"{prop['Street address']}, {prop['City']}, {prop['State']} {prop['Postal Code']}"
    geocode_result = geocoding_service.geocode_address(full_address)

    if not geocode_result.get('latitude'):
        print("❌ Failed to geocode address")
        return

    lat = geocode_result['latitude']
    lng = geocode_result['longitude']

    print(f"✅ Geocoded: {lat}, {lng}")
    print()

    # Get imagery
    print("📸 Downloading images...")
    imagery_service = ImageryService()

    # Get satellite image
    satellite_result = imagery_service.get_satellite_imagery(lat, lng)
    satellite_url = satellite_result.get('image_url') if satellite_result else None

    # Get street view
    street_result = imagery_service.get_street_view(lat, lng)
    street_url = street_result.get('image_url') if street_result else None

    print(f"\n🛰️  Satellite Image URL:")
    print(f"   {satellite_url}")
    print()
    print(f"📸 Street View URL:")
    print(f"   {street_url}")
    print()

    # Download and save images
    satellite_path = None
    street_path = None

    if satellite_url:
        print("⬇️  Downloading satellite image...")
        response = requests.get(satellite_url)
        if response.status_code == 200:
            satellite_path = "/Users/ahmadraza/Documents/property-anyslis/backend/test_satellite_view.jpg"
            with open(satellite_path, 'wb') as f:
                f.write(response.content)
            print(f"   ✅ Saved to: {satellite_path}")

            # Display image info
            img = Image.open(BytesIO(response.content))
            print(f"   Size: {img.size[0]}x{img.size[1]} pixels")
            print(f"   Format: {img.format}")

    print()

    if street_url:
        print("⬇️  Downloading street view image...")
        response = requests.get(street_url)
        if response.status_code == 200:
            street_path = "/Users/ahmadraza/Documents/property-anyslis/backend/test_street_view.jpg"
            with open(street_path, 'wb') as f:
                f.write(response.content)
            print(f"   ✅ Saved to: {street_path}")

            # Display image info
            img = Image.open(BytesIO(response.content))
            print(f"   Size: {img.size[0]}x{img.size[1]} pixels")
            print(f"   Format: {img.format}")

    print()
    print("="*80)
    print("🤖 AI PROMPTS USED FOR ANALYSIS")
    print("="*80)
    print()

    # Show satellite power line detection prompt
    print("1️⃣  SATELLITE IMAGE - POWER LINE DETECTION PROMPT:")
    print("-"*80)
    satellite_prompt = """LOOK EXTREMELY CAREFULLY at this satellite/aerial image for power lines, electrical cables, and utility infrastructure.

🔍 SEARCH FOR (scan the ENTIRE image systematically):
1. **POWER LINE CORRIDORS**:
   - Thin dark lines crossing the image (POWER CABLES FROM ABOVE)
   - Straight lines cutting through vegetation/trees
   - Cleared paths or gaps in tree cover (power line right-of-way)

2. **SHADOWS & LINES**:
   - Dark linear shadows on the ground (cast by cables)
   - Multiple parallel thin lines (CABLE BUNDLES)
   - Lines connecting between structures

3. **UTILITY INFRASTRUCTURE**:
   - Small dots in a line (utility poles from above)
   - Transmission towers (metal lattice structures)
   - Transformer boxes or equipment

4. **PATTERNS TO DETECT**:
   - Lines running along streets
   - Lines crossing properties
   - Multiple parallel cables (high-voltage transmission)

⚠️ **CRITICAL DETECTION RULES**:
- Cables appear as VERY THIN dark lines from satellite view
- Look for PATTERNS - multiple cables run in parallel
- Check for shadows on ground (indicates elevated cables)
- Utility poles appear as small dots along cable lines
- Even FAINT lines should be detected if they're straight and continuous

📏 **DISTANCE MEASUREMENT**:
- Estimate distance from CENTER of image to nearest power line
- Use buildings/roads as scale reference
- Report in meters

Respond with ONLY this JSON format:
{
    "visible": true or false,
    "confidence": 0.0 to 1.0,
    "distance_meters": number or null,
    "line_type": "transmission|distribution|single|multiple|none",
    "details": "EXACT description: what cables/lines you see, their location, direction, and approximate distance from image center"
}"""
    print(satellite_prompt)
    print()
    print()

    # Show street view power line detection prompt
    print("2️⃣  STREET VIEW IMAGE - POWER LINE DETECTION PROMPT:")
    print("-"*80)
    street_prompt = """You are an expert at detecting power lines, electrical cables, and utility infrastructure. Analyze this street view image with EXTREME CARE.

🔍 LOOK FOR (scan EVERY PART of the image, especially TOP 50% and SKY):
1. **CABLES & WIRES**:
   - Thin black/dark lines against sky (POWER CABLES)
   - Multiple parallel lines running horizontally (BUNDLE OF CABLES)
   - Drooping/sagging lines between poles (ELECTRICAL LINES)
   - Telephone/communication cables (thinner, lower lines)

2. **UTILITY POLES**:
   - Wooden or concrete vertical poles
   - Metal arms/crossbars on top
   - Transformers (gray/green cylindrical boxes)
   - Guy-wires supporting the pole

3. **POWER LINE POSITION**:
   - Count how many cables/lines you see
   - Identify if they run along the street in front
   - Check if they cross over the property
   - Measure approximate distance from viewpoint

⚠️ **CRITICAL DETECTION RULES**:
- Even if cables are THIN or FAINT, still detect them
- Look in the SKY area - cables show up as dark lines
- If you see utility poles, there ARE cables attached
- Multiple cables in parallel = power distribution lines
- ANY visible wires/cables should be detected as "visible": true

📍 **POSITION CATEGORIES** (relative to the property/camera):
- **"directly_above"**: Cables run directly overhead the street/property in front
- **"in_front_close"**: Cables/poles visible in front, within 10-30 meters
- **"nearby"**: Cables visible nearby but not directly in front, 30-100 meters
- **"far"**: Cables visible in distance, beyond 100 meters
- **"none"**: Absolutely NO cables, wires, or utility infrastructure anywhere

Respond with ONLY this JSON format:
{
    "visible": true or false,
    "confidence": 0.0 to 1.0,
    "type": "overhead_lines|utility_poles|transmission_tower|none",
    "position": "directly_above|in_front_close|nearby|far|none",
    "proximity": "very_close|close|moderate|far",
    "cable_count": "single|multiple|many|none",
    "details": "EXACT description: what cables/wires you see, where they are located, and their position relative to the property"
}"""
    print(street_prompt)
    print()
    print()

    # Show property condition prompt
    print("3️⃣  STREET VIEW IMAGE - PROPERTY CONDITION PROMPT:")
    print("-"*80)
    property_prompt = """Analyze this street view image and assess the property/area condition.

EVALUATE:
1. **Property Appearance**: Well-maintained, average, poor, vacant
2. **Vegetation**: Overgrown, maintained, cleared, natural
3. **Infrastructure**: Roads, sidewalks, curbs condition
4. **Surroundings**: Neighbors, general area upkeep
5. **Signs of Activity**: Lived-in, abandoned, under development

Respond ONLY with JSON:
{
    "condition": "EXCELLENT|GOOD|AVERAGE|POOR|VACANT|UNDEVELOPED",
    "maintained": true/false,
    "development_status": "developed|partially_developed|undeveloped",
    "concerns": ["list", "of", "concerns"],
    "confidence": 0.0-1.0,
    "details": "description"
}"""
    print(property_prompt)
    print()
    print()

    # Show nearby structures prompt
    print("4️⃣  SATELLITE IMAGE - NEARBY STRUCTURES PROMPT:")
    print("-"*80)
    structures_prompt = """Analyze this satellite image and identify ALL structures and buildings.

COUNT AND IDENTIFY:
1. **Houses/Residences**: Single-family homes, mobile homes
2. **Buildings**: Commercial buildings, apartments, warehouses
3. **Garages**: Detached garages, carports, sheds
4. **Driveways/Parking**: Paved areas, parking lots
5. **Swimming Pools**: Backyard pools (blue rectangles)
6. **Other Structures**: Barns, outbuildings, etc.

Respond ONLY with JSON:
{
    "structures_detected": true/false,
    "count": total_number,
    "types": ["house", "garage", "shed", etc],
    "density": "high|medium|low|none",
    "nearest_distance_meters": estimated_distance,
    "confidence": 0.0-1.0,
    "details": "detailed description"
}"""
    print(structures_prompt)
    print()
    print()

    print("="*80)
    print("✅ SUMMARY")
    print("="*80)
    print()
    print(f"Property: {prop['Street address']}, {prop['City']}, {prop['State']}")
    print(f"Coordinates: {lat}, {lng}")
    print()
    print("Images saved:")
    if satellite_path:
        print(f"  🛰️  Satellite: {satellite_path}")
    if street_path:
        print(f"  📸 Street: {street_path}")
    print()
    print("Both images are analyzed using the prompts shown above.")
    print("The AI examines:")
    print("  • Satellite image: Power lines from above, structures, development")
    print("  • Street view: Power line position (front/above/nearby), property condition")
    print()
    print("Based on power line POSITION, risk is calculated:")
    print("  • HIGH RISK: Lines in front or very close (+40 points)")
    print("  • MEDIUM RISK: Lines nearby (+25 points)")
    print("  • LOW RISK: Lines overhead/above (+15 points)")
    print()

if __name__ == "__main__":
    main()
