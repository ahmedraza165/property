#!/usr/bin/env python3
"""
Simple test of flood zone detection with known Lehigh Acres coordinates
"""
import sys
sys.path.append('/Users/ahmadraza/Documents/property-anyslis/backend')

from gis_service import GISRiskService

# Initialize service
gis = GISRiskService()

# Sample Lehigh Acres coordinates (center of Lehigh Acres)
# These are real coordinates in different parts of Lehigh Acres, FL
test_locations = [
    {"name": "Lehigh Acres Central", "lat": 26.6251, "lon": -81.6248},
    {"name": "Lehigh Acres North", "lat": 26.6500, "lon": -81.6300},
    {"name": "Lehigh Acres South", "lat": 26.6000, "lon": -81.6200},
    {"name": "Lehigh Acres East", "lat": 26.6250, "lon": -81.6000},
    {"name": "Lehigh Acres West", "lat": 26.6250, "lon": -81.6500},
    {"name": "Near Canal 1", "lat": 26.6320, "lon": -81.6180},
    {"name": "Near Canal 2", "lat": 26.6100, "lon": -81.6350},
    {"name": "Residential Area 1", "lat": 26.6280, "lon": -81.6220},
    {"name": "Residential Area 2", "lat": 26.6150, "lon": -81.6280},
    {"name": "Residential Area 3", "lat": 26.6380, "lon": -81.6320},
]

print("Testing Flood Zone Detection for Lehigh Acres, FL")
print("=" * 80)

zone_counts = {}

for location in test_locations:
    name = location['name']
    lat = location['lat']
    lon = location['lon']

    print(f"\nTesting: {name}")
    print(f"Coordinates: {lat}, {lon}")

    # Check flood zone
    flood_result = gis.check_flood_zone(lat, lon, "Lehigh Acres", "FL")

    print(f"   Flood Zone: {flood_result['zone']}")
    print(f"   Severity: {flood_result['severity']}")
    print(f"   Confidence: {flood_result['confidence']}")
    print(f"   Source: {flood_result['source']}")
    if 'note' in flood_result:
        print(f"   Note: {flood_result['note']}")
    if 'in_sfha' in flood_result:
        print(f"   In SFHA: {flood_result['in_sfha']}")

    # Count zones
    zone = flood_result['zone']
    zone_counts[zone] = zone_counts.get(zone, 0) + 1

print("\n" + "=" * 80)
print("SUMMARY:")
print("-" * 80)
for zone, count in sorted(zone_counts.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / len(test_locations)) * 100
    print(f"{zone}: {count} locations ({percentage:.1f}%)")
print("=" * 80)

# Print diagnostic info
print("\n" + "=" * 80)
print("DIAGNOSIS:")
print("-" * 80)
if len(set(zone_counts.keys())) == 1 and list(zone_counts.keys())[0] == "X-Shaded (estimated)":
    print("❌ ISSUE CONFIRMED: All locations showing same fallback zone")
    print("   The FEMA API is not returning data, falling back to hardcoded estimate")
    print("   Need to fix the API calls or improve fallback logic")
else:
    print("✅ Different zones detected - API appears to be working")
print("=" * 80)
