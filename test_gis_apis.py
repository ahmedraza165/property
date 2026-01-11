#!/usr/bin/env python3
"""
Comprehensive GIS API Testing Script

Tests all free GIS APIs with real addresses to verify they work correctly.
Includes geocoding and detailed result display.
"""

import sys
import os
import requests
import json
import time
from typing import Dict, Optional, Tuple

# Add backend to path so we can import gis_service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from gis_service import GISRiskService


# Test addresses
TEST_ADDRESSES = [
    {
        "address": "909 monroe ave",
        "city": "Lehigh Acres",
        "state": "FL",
        "zip": "33972"
    },
    {
        "address": "927 Lakeside Dr",
        "city": "Lehigh Acres",
        "state": "FL",
        "zip": "33974"
    }
]


def geocode_address(address: str, city: str, state: str, zip_code: str) -> Optional[Tuple[float, float]]:
    """
    Geocode an address to lat/lon using free Nominatim API (OpenStreetMap)

    Returns: (latitude, longitude) or None
    """
    print(f"\n  → Geocoding: {address}, {city}, {state} {zip_code}")

    try:
        # Use Nominatim (OpenStreetMap) - Free, no API key required
        url = "https://nominatim.openstreetmap.org/search"

        params = {
            "street": address,
            "city": city,
            "state": state,
            "postalcode": zip_code,
            "country": "USA",
            "format": "json",
            "limit": 1
        }

        headers = {
            "User-Agent": "PropertyRiskAnalysis/1.0 (Testing)"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            results = response.json()
            if results:
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
                print(f"  ✓ Geocoded to: {lat:.6f}, {lon:.6f}")
                return (lat, lon)
            else:
                print(f"  ✗ No geocoding results found")
                return None
        else:
            print(f"  ✗ Geocoding failed: HTTP {response.status_code}")
            return None

    except Exception as e:
        print(f"  ✗ Geocoding error: {str(e)}")
        return None


def test_wetlands_api_direct(lat: float, lon: float):
    """Test wetlands APIs directly"""
    print("\n  Testing Wetlands APIs:")

    # Test ESRI Living Atlas
    try:
        print("    → ESRI Living Atlas USA Wetlands...")
        url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Wetlands/FeatureServer/0/query"

        params = {
            "geometry": f'{{"x":{lon},"y":{lat},"spatialReference":{{"wkid":4326}}}}',
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "WETLAND_TYPE",
            "returnGeometry": "false",
            "f": "json"
        }

        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                wetland_type = data["features"][0]["attributes"].get("WETLAND_TYPE", "Unknown")
                print(f"      ✓ SUCCESS - Wetland found: {wetland_type}")
            else:
                print(f"      ✓ SUCCESS - No wetlands detected")
        else:
            print(f"      ✗ FAILED - HTTP {response.status_code}")

    except Exception as e:
        print(f"      ✗ FAILED - {str(e)}")

    # Test USFWS Direct
    try:
        print("    → USFWS NWI Direct...")
        url = "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/0/query"

        params = {
            "geometry": f'{{"x":{lon},"y":{lat},"spatialReference":{{"wkid":4326}}}}',
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "WETLAND_TYPE,ATTRIBUTE",
            "returnGeometry": "false",
            "f": "json"
        }

        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                wetland_type = data["features"][0]["attributes"].get("WETLAND_TYPE", "Unknown")
                print(f"      ✓ SUCCESS - Wetland found: {wetland_type}")
            else:
                print(f"      ✓ SUCCESS - No wetlands detected")
        else:
            print(f"      ✗ FAILED - HTTP {response.status_code}")

    except Exception as e:
        print(f"      ✗ FAILED - {str(e)}")


def test_flood_api_direct(lat: float, lon: float):
    """Test flood zone APIs directly"""
    print("\n  Testing Flood Zone APIs:")

    # Test ESRI Living Atlas FEMA Flood Hazards
    try:
        print("    → ESRI Living Atlas FEMA Flood Hazards...")
        url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Flood_Hazard_Reduced_Set_gdb/FeatureServer/0/query"

        params = {
            "geometry": f'{{"x":{lon},"y":{lat},"spatialReference":{{"wkid":4326}}}}',
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF",
            "returnGeometry": "false",
            "f": "json"
        }

        response = requests.get(url, params=params, timeout=20)

        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                attrs = data["features"][0]["attributes"]
                zone = attrs.get("FLD_ZONE", "Unknown")
                subty = attrs.get("ZONE_SUBTY", "")
                sfha = attrs.get("SFHA_TF", "F")

                zone_display = f"{zone} ({subty})" if subty else zone
                sfha_display = "YES" if sfha == "T" else "NO"

                print(f"      ✓ SUCCESS - Zone: {zone_display}, SFHA: {sfha_display}")
            else:
                print(f"      ✓ SUCCESS - No flood zone data (likely Zone X)")
        else:
            print(f"      ✗ FAILED - HTTP {response.status_code}")

    except Exception as e:
        print(f"      ✗ FAILED - {str(e)}")

    # Test FEMA NFHL Direct
    try:
        print("    → FEMA NFHL Direct (Official)...")
        url = "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query"

        params = {
            "geometry": f'{{"x":{lon},"y":{lat},"spatialReference":{{"wkid":4326}}}}',
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE",
            "returnGeometry": "false",
            "f": "json"
        }

        response = requests.get(url, params=params, timeout=20)

        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                attrs = data["features"][0]["attributes"]
                zone = attrs.get("FLD_ZONE", "Unknown")
                subty = attrs.get("ZONE_SUBTY", "")
                sfha = attrs.get("SFHA_TF", "F")

                zone_display = f"{zone} ({subty})" if subty else zone
                sfha_display = "YES" if sfha == "T" else "NO"

                print(f"      ✓ SUCCESS - Zone: {zone_display}, SFHA: {sfha_display}")
            else:
                print(f"      ✓ SUCCESS - No flood zone data (likely Zone X)")
        else:
            print(f"      ✗ FAILED - HTTP {response.status_code}")

    except Exception as e:
        print(f"      ✗ FAILED - {str(e)}")


def test_elevation_api_direct(lat: float, lon: float):
    """Test elevation APIs directly"""
    print("\n  Testing Elevation APIs:")

    # Test USGS
    try:
        print("    → USGS Elevation Point Query Service...")
        url = "https://epqs.nationalmap.gov/v1/json"

        params = {
            "x": lon,
            "y": lat,
            "units": "Meters",
            "output": "json"
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            elev = data.get("value")
            if elev is not None and elev != -1000000:
                print(f"      ✓ SUCCESS - Elevation: {elev} meters")
            else:
                print(f"      ✗ FAILED - No elevation data returned")
        else:
            print(f"      ✗ FAILED - HTTP {response.status_code}")

    except Exception as e:
        print(f"      ✗ FAILED - {str(e)}")


def test_protected_areas_api_direct(lat: float, lon: float):
    """Test protected areas API directly"""
    print("\n  Testing Protected Areas API:")

    try:
        print("    → ESRI Living Atlas USA Protected Areas...")
        url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Protected_Areas/FeatureServer/0/query"

        params = {
            "geometry": f'{{"x":{lon},"y":{lat},"spatialReference":{{"wkid":4326}}}}',
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "Category,Mang_Name,Unit_Nm,d_Des_Tp",
            "returnGeometry": "false",
            "f": "json"
        }

        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                attrs = data["features"][0]["attributes"]
                category = attrs.get("Category", "Unknown")
                manager = attrs.get("Mang_Name", "Unknown")
                print(f"      ✓ SUCCESS - Protected area: {category} (Managed by {manager})")
            else:
                print(f"      ✓ SUCCESS - Not in protected area")
        else:
            print(f"      ✗ FAILED - HTTP {response.status_code}")

    except Exception as e:
        print(f"      ✗ FAILED - {str(e)}")


def print_analysis_results(results: Dict):
    """Pretty print the analysis results"""
    print("\n" + "="*80)
    print("COMPREHENSIVE PROPERTY ANALYSIS RESULTS")
    print("="*80)

    # Location
    print(f"\n📍 LOCATION:")
    loc = results.get("location", {})
    print(f"   Address: {loc.get('address', 'N/A')}")
    print(f"   Coordinates: {loc.get('latitude', 'N/A')}, {loc.get('longitude', 'N/A')}")

    # Wetlands
    print(f"\n💧 WETLANDS:")
    wetlands = results.get("wetlands", {})
    status = "YES" if wetlands.get("status") else "NO"
    print(f"   Status: {status}")
    if wetlands.get("type"):
        print(f"   Type: {wetlands.get('type')}")
    print(f"   Confidence: {wetlands.get('confidence', 'N/A')}")
    print(f"   Source: {wetlands.get('source', 'N/A')}")

    # Flood Zone
    print(f"\n🌊 FLOOD ZONE:")
    flood = results.get("flood_zone", {})
    print(f"   Zone: {flood.get('zone', 'N/A')}")
    print(f"   Severity: {flood.get('severity', 'N/A')}")
    if flood.get('in_sfha') is not None:
        sfha_status = "YES" if flood.get('in_sfha') else "NO"
        print(f"   In SFHA: {sfha_status}")
    print(f"   Confidence: {flood.get('confidence', 'N/A')}")
    print(f"   Source: {flood.get('source', 'N/A')}")

    # Slope
    print(f"\n⛰️  SLOPE:")
    slope = results.get("slope", {})
    print(f"   Percentage: {slope.get('percentage', 'N/A')}%")
    print(f"   Severity: {slope.get('severity', 'N/A')}")
    print(f"   Confidence: {slope.get('confidence', 'N/A')}")
    print(f"   Source: {slope.get('source', 'N/A')}")

    # Road Access
    print(f"\n🛣️  ROAD ACCESS:")
    road = results.get("road_access", {})
    access = "YES" if road.get("has_access") else "NO"
    print(f"   Has Access: {access}")
    print(f"   Distance: {road.get('distance_meters', 'N/A')} meters")
    print(f"   Confidence: {road.get('confidence', 'N/A')}")
    print(f"   Source: {road.get('source', 'N/A')}")

    # Protected Land
    print(f"\n🏞️  PROTECTED LAND:")
    protected = results.get("protected_land", {})
    is_protected = "YES" if protected.get("is_protected") else "NO"
    print(f"   Is Protected: {is_protected}")
    if protected.get("type"):
        print(f"   Type: {protected.get('type')}")
    print(f"   Confidence: {protected.get('confidence', 'N/A')}")
    print(f"   Source: {protected.get('source', 'N/A')}")

    # Overall Risk
    print(f"\n⚠️  OVERALL RISK: {results.get('overall_risk', 'N/A')}")
    print(f"⏱️  Processing Time: {results.get('processing_time_seconds', 'N/A')}s")

    if results.get("error"):
        print(f"\n❌ ERROR: {results['error']}")

    print("\n" + "="*80)


def main():
    """Main test function"""
    print("="*80)
    print("GIS API COMPREHENSIVE TESTING")
    print("="*80)
    print("\nTesting free GIS APIs with real addresses...")
    print("This will verify that all APIs work correctly.\n")

    service = GISRiskService()

    for i, addr_data in enumerate(TEST_ADDRESSES, 1):
        print(f"\n{'='*80}")
        print(f"TEST ADDRESS #{i}")
        print(f"{'='*80}")
        print(f"Address: {addr_data['address']}")
        print(f"City: {addr_data['city']}")
        print(f"State: {addr_data['state']}")
        print(f"ZIP: {addr_data['zip']}")

        # Geocode the address
        coords = geocode_address(
            addr_data['address'],
            addr_data['city'],
            addr_data['state'],
            addr_data['zip']
        )

        if not coords:
            print("\n⚠️  Could not geocode address. Skipping...\n")
            continue

        lat, lon = coords

        # Test APIs directly
        print("\n" + "-"*80)
        print("DIRECT API TESTS")
        print("-"*80)

        test_wetlands_api_direct(lat, lon)
        test_flood_api_direct(lat, lon)
        test_elevation_api_direct(lat, lon)
        test_protected_areas_api_direct(lat, lon)

        # Run comprehensive analysis using GISRiskService
        print("\n" + "-"*80)
        print("COMPREHENSIVE ANALYSIS (GISRiskService)")
        print("-"*80)

        results = service.analyze_property(
            latitude=lat,
            longitude=lon,
            address=f"{addr_data['address']}, {addr_data['city']}, {addr_data['state']} {addr_data['zip']}",
            city=addr_data['city'],
            state=addr_data['state']
        )

        print_analysis_results(results)

        # Rate limiting - be nice to free APIs
        if i < len(TEST_ADDRESSES):
            print("\n⏳ Waiting 2 seconds before next test (rate limiting)...")
            time.sleep(2)

    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)

    # Print summary
    print("\n📊 API SUMMARY:")
    print("  ✓ ESRI Living Atlas USA Wetlands - Free, no API key")
    print("  ✓ USFWS NWI Direct - Free, no API key")
    print("  ✓ FEMA NFHL Flood Zones - Free, no API key")
    print("  ✓ USGS Elevation Service - Free, no API key")
    print("  ✓ ESRI Protected Areas - Free, no API key")
    print("  ✓ OpenStreetMap Nominatim - Free geocoding")
    print("\n💡 All APIs tested are free and require no registration!")
    print("\n")


if __name__ == "__main__":
    main()
