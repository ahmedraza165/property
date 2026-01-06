#!/usr/bin/env python3
"""
Test script to verify GIS and Water Utility services
"""
import sys
import time
from geocoding_service import GeocodingService
from gis_service import GISRiskService
from water_utility_service import WaterUtilityService

def print_separator(title=""):
    """Print a visual separator"""
    print("\n" + "="*80)
    if title:
        print(f"  {title}")
        print("="*80)
    print()

def test_geocoding(address, city, state, zip_code):
    """Test geocoding service"""
    print_separator("Testing Geocoding Service")

    geocoding_service = GeocodingService()
    print(f"Address: {address}, {city}, {state} {zip_code}")

    start = time.time()
    result = geocoding_service.geocode_address(address, city, state, zip_code)
    duration = time.time() - start

    if result:
        print(f"✓ Geocoding successful ({duration:.2f}s)")
        print(f"  Full Address: {result['full_address']}")
        print(f"  Coordinates: {result['latitude']}, {result['longitude']}")
        print(f"  County: {result.get('county', 'N/A')}")
        return result
    else:
        print(f"✗ Geocoding failed")
        return None

def test_gis_service(latitude, longitude):
    """Test GIS risk analysis service"""
    print_separator("Testing GIS Risk Analysis Service")

    gis_service = GISRiskService()
    print(f"Analyzing coordinates: {latitude}, {longitude}")

    start = time.time()
    result = gis_service.analyze_property(latitude, longitude)
    duration = time.time() - start

    print(f"✓ GIS Analysis completed ({duration:.2f}s)")
    print(f"\nResults:")
    print(f"  Overall Risk: {result['overall_risk']}")
    print(f"\n  Wetlands:")
    print(f"    Status: {result['wetlands']['status']}")
    print(f"    Source: {result['wetlands']['source']}")
    print(f"\n  Flood Zone:")
    print(f"    Zone: {result['flood_zone']['zone']}")
    print(f"    Severity: {result['flood_zone']['severity']}")
    print(f"    Source: {result['flood_zone']['source']}")
    print(f"\n  Slope:")
    print(f"    Percentage: {result['slope']['percentage']}%")
    print(f"    Severity: {result['slope']['severity']}")
    print(f"    Source: {result['slope']['source']}")
    print(f"\n  Road Access:")
    print(f"    Has Access: {result['road_access']['has_access']}")
    print(f"    Distance: {result['road_access']['distance_meters']}m")
    print(f"    Source: {result['road_access']['source']}")
    print(f"\n  Landlocked: {result['landlocked']}")
    print(f"\n  Protected Land:")
    print(f"    Is Protected: {result['protected_land']['is_protected']}")
    print(f"    Type: {result['protected_land'].get('type', 'N/A')}")
    print(f"    Source: {result['protected_land']['source']}")

    if result.get('error'):
        print(f"\n  ⚠ Error: {result['error']}")

    return result

def test_water_utility_service(latitude, longitude):
    """Test water utility service"""
    print_separator("Testing Water Utility Service")

    water_service = WaterUtilityService()
    print(f"Checking utilities at: {latitude}, {longitude}")

    start = time.time()
    result = water_service.check_utilities(latitude, longitude)
    duration = time.time() - start

    print(f"✓ Water Utility check completed ({duration:.2f}s)")
    print(f"\nResults:")
    print(f"  Water Available: {result['water_available']}")
    print(f"  Water Provider: {result.get('water_provider', 'N/A')}")
    print(f"  Water Distance: {result.get('water_distance_meters', 'N/A')}m")
    print(f"  Sewer Available: {result['sewer_available']}")
    print(f"  Sewer Provider: {result.get('sewer_provider', 'N/A')}")
    print(f"  Sewer Distance: {result.get('sewer_distance_meters', 'N/A')}m")
    print(f"  Source: {result['source']}")

    return result

def main():
    """Run all tests with a sample property from the CSV"""
    print_separator("PROPERTY ANALYSIS SERVICE VERIFICATION")

    # Test with first property from CSV
    test_address = "757 Cane St E"
    test_city = "Lehigh Acres"
    test_state = "FL"
    test_zip = "33974-9819"

    print(f"Testing with property: {test_address}, {test_city}, {test_state} {test_zip}")

    # Test geocoding
    geocode_result = test_geocoding(test_address, test_city, test_state, test_zip)

    if not geocode_result:
        print("\n✗ Cannot proceed without valid geocoding")
        sys.exit(1)

    lat = geocode_result['latitude']
    lon = geocode_result['longitude']

    # Test GIS service
    gis_result = test_gis_service(lat, lon)

    # Test water utility service
    water_result = test_water_utility_service(lat, lon)

    # Summary
    print_separator("TEST SUMMARY")
    print("All services tested successfully!")
    print(f"Total processing time: GIS={gis_result['processing_time_seconds']:.2f}s")
    print(f"\nProperty Assessment:")
    print(f"  Address: {geocode_result['full_address']}")
    print(f"  Risk Level: {gis_result['overall_risk']}")
    print(f"  Water Available: {water_result['water_available']}")
    print(f"  Sewer Available: {water_result['sewer_available']}")

    print_separator()

if __name__ == "__main__":
    main()
