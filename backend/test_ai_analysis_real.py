#!/usr/bin/env python3
"""
Test AI analysis with real CSV data to verify what results it returns.
"""
import sys
import json
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import services
from geocoding_service import GeocodingService
from imagery_service import ImageryService
from ai_analysis_service import AIAnalysisService

async def test_real_property():
    """Test AI analysis with real property from CSV."""

    # Test address from CSV (first property)
    street = "757 Cane St E"
    city = "Lehigh Acres"
    state = "FL"
    zip_code = "33974-9819"

    test_address = f"{street}, {city}, {state} {zip_code}"
    print(f"Testing AI Analysis for: {test_address}")
    print("=" * 80)

    # Initialize services
    geocoding = GeocodingService()
    imagery = ImageryService()
    ai_service = AIAnalysisService()

    try:
        # Step 1: Geocode the address
        print("\n1. GEOCODING ADDRESS...")
        geo_result = geocoding.geocode_address(street, city, state, zip_code)

        if not geo_result or not geo_result.get('latitude'):
            print("❌ Failed to geocode address")
            return

        lat = geo_result['latitude']
        lon = geo_result['longitude']
        print(f"✅ Geocoded: ({lat}, {lon})")
        print(f"   Formatted address: {geo_result.get('formatted_address')}")

        # Step 2: Get imagery
        print("\n2. FETCHING IMAGERY...")
        imagery_result = imagery.fetch_imagery(lat, lon)

        satellite_url = imagery_result.get('satellite', {}).get('url')
        street_url_1 = imagery_result.get('street_view_1', {}).get('url')
        street_url_2 = imagery_result.get('street_view_2', {}).get('url')

        print(f"   ✅ Satellite: {satellite_url[:80] if satellite_url else 'N/A'}...")
        print(f"   ✅ Street View 1: {street_url_1[:80] if street_url_1 else 'N/A'}...")
        print(f"   ✅ Street View 2: {street_url_2[:80] if street_url_2 else 'N/A'}...")

        # Step 3: Run AI Analysis
        print("\n3. RUNNING AI ANALYSIS...")
        print("   This will call OpenAI Vision API to analyze the images...")
        print("   (May take 10-30 seconds)")

        ai_result = ai_service.analyze_property(
            latitude=lat,
            longitude=lon,
            satellite_image_url=satellite_url,
            street_image_url=street_url_1,
            street_image_url_2=street_url_2
        )

        # Step 4: Display Results
        print("\n" + "=" * 80)
        print("AI ANALYSIS RESULTS")
        print("=" * 80)

        if ai_result.get('error'):
            print(f"❌ ERROR: {ai_result['error']}")
            return

        print(f"\n⏱️  Processing Time: {ai_result.get('processing_time_seconds', 0):.2f}s")
        print(f"🤖 Model Version: {ai_result.get('model_version', 'unknown')}")

        # Power Lines Detection
        print("\n🔌 POWER LINES (Street View):")
        power_street = ai_result.get('power_lines_street', {})
        if power_street:
            print(f"   Visible: {power_street.get('visible', False)}")
            print(f"   Confidence: {power_street.get('confidence', 0):.2f}")
            print(f"   Position: {power_street.get('position', 'unknown')}")
            print(f"   Proximity: {power_street.get('proximity', 'unknown')}")
            print(f"   Type: {power_street.get('type', 'unknown')}")
            if power_street.get('details'):
                print(f"   Details: {power_street.get('details')[:100]}...")

        print("\n🛰️  POWER LINES (Satellite):")
        power_sat = ai_result.get('power_lines', {})
        if power_sat:
            print(f"   Visible: {power_sat.get('visible', False)}")
            print(f"   Confidence: {power_sat.get('confidence', 0):.2f}")
            print(f"   Distance: {power_sat.get('distance_meters', 'N/A')}m")
            if power_sat.get('details'):
                print(f"   Details: {power_sat.get('details')[:100]}...")

        # Road Condition
        print("\n🛣️  ROAD CONDITION:")
        road = ai_result.get('road_condition', {})
        if road:
            print(f"   Type: {road.get('type', 'UNKNOWN')}")
            print(f"   Confidence: {road.get('confidence', 0):.2f}")
            if road.get('details'):
                print(f"   Details: {road.get('details')[:100]}...")

        # Property Condition
        print("\n🏠 PROPERTY CONDITION:")
        prop = ai_result.get('property_condition', {})
        if prop:
            print(f"   Condition: {prop.get('condition', 'UNKNOWN')}")
            print(f"   Maintained: {prop.get('maintained', 'N/A')}")
            print(f"   Confidence: {prop.get('confidence', 0):.2f}")
            concerns = prop.get('concerns', [])
            if concerns:
                print(f"   Concerns: {', '.join(concerns)}")
            if prop.get('details'):
                print(f"   Details: {prop.get('details')[:100]}...")

        # Nearby Structures
        print("\n🏘️  NEARBY STRUCTURES:")
        structures = ai_result.get('nearby_structures', {})
        if structures:
            print(f"   Count: {structures.get('count', 0)}")
            print(f"   Density: {structures.get('density', 'unknown')}")
            print(f"   Confidence: {structures.get('confidence', 0):.2f}")
            types = structures.get('types', [])
            if types:
                print(f"   Types: {', '.join(types)}")

        # Development
        print("\n🏗️  NEARBY DEVELOPMENT:")
        dev = ai_result.get('nearby_development', {})
        if dev:
            print(f"   Type: {dev.get('type', 'UNKNOWN')}")
            print(f"   Count: {dev.get('count', 0)}")
            print(f"   Confidence: {dev.get('confidence', 0):.2f}")

        # Overall AI Risk
        print("\n⚠️  OVERALL AI RISK ASSESSMENT:")
        risk = ai_result.get('overall_ai_risk', {})
        if risk:
            print(f"   Level: {risk.get('level', 'UNKNOWN')}")
            print(f"   Score: {risk.get('score', 0):.1f}")
            print(f"   Confidence: {risk.get('confidence', 0):.2f}")
            print(f"   Power Lines Detected: {risk.get('power_lines_detected', False)}")
            factors = risk.get('factors', [])
            if factors:
                print(f"   Risk Factors ({len(factors)}):")
                for factor in factors:
                    print(f"      • {factor}")

        # Key Insights
        print("\n💡 KEY INSIGHTS:")
        insights = ai_result.get('key_insights', [])
        if insights:
            for i, insight in enumerate(insights, 1):
                print(f"   {i}. {insight}")
        else:
            print("   No key insights provided")

        # Save full result to JSON file
        output_file = "test_ai_result.json"
        with open(output_file, 'w') as f:
            json.dump(ai_result, f, indent=2)
        print(f"\n💾 Full result saved to: {output_file}")

        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_property())
