#!/usr/bin/env python3
"""
Test flood zone detection with sample Lehigh Acres addresses
"""
import sys
sys.path.append('/Users/ahmadraza/Documents/property-anyslis/backend')

from gis_service import GISRiskService
from geocoding_service import GeocodingService
import csv

# Initialize services
gis = GISRiskService()
geocoder = GeocodingService()

# Read sample addresses from CSV
csv_file = "/Users/ahmadraza/Documents/property-anyslis/backend/Export_Contacts_Cleaned Target Best Lehigh_Dec_2025_5_41_PM.csv"

print("Testing Flood Zone Detection for Lehigh Acres Properties")
print("=" * 80)

with open(csv_file, 'r') as f:
    reader = csv.DictReader(f)
    count = 0
    zone_counts = {}
    total_tested = 0

    for row in reader:
        if count >= 10:  # Test first 10 properties
            break

        address = row['Street address']
        city = row['City']
        state = row['State']
        zipcode = row['Postal Code']

        # Geocode address
        print(f"\n{count + 1}. Testing: {address}, {city}, {state} {zipcode}")

        geocode_result = geocoder.geocode_address(address, city, state, zipcode)

        if geocode_result and geocode_result.get('lat') and geocode_result.get('lon'):
            lat = geocode_result['lat']
            lon = geocode_result['lon']

            print(f"   Coordinates: {lat}, {lon}")

            # Check flood zone
            flood_result = gis.check_flood_zone(lat, lon, city, state)

            print(f"   Flood Zone: {flood_result['zone']}")
            print(f"   Severity: {flood_result['severity']}")
            print(f"   Confidence: {flood_result['confidence']}")
            print(f"   Source: {flood_result['source']}")
            if 'note' in flood_result:
                print(f"   Note: {flood_result['note']}")

            # Count zones
            zone = flood_result['zone']
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
            total_tested += 1

            count += 1
        else:
            print(f"   Geocoding failed")
            count += 1

print("\n" + "=" * 80)
print("SUMMARY:")
print("-" * 80)
if total_tested > 0:
    for zone, cnt in sorted(zone_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (cnt / total_tested) * 100
        print(f"{zone}: {cnt} properties ({percentage:.1f}%)")
else:
    print("No properties successfully tested")
print("=" * 80)
