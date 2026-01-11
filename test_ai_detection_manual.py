#!/usr/bin/env python3
"""
Manual AI Detection Testing Script

Tests power line detection and property analysis on real CSV data
with proper rate limiting and comprehensive logging.
"""

import sys
import os
import time
import csv
import requests
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from imagery_service import ImageryService
    from ai_analysis_service import AIAnalysisService
except ImportError as e:
    logger.error(f"Failed to import services: {e}")
    sys.exit(1)


def geocode_address(address: str, city: str, state: str, zip_code: str) -> tuple:
    """Geocode an address using Nominatim."""
    try:
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
        headers = {"User-Agent": "PropertyAnalysisTest/1.0"}

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            results = response.json()
            if results:
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
                logger.info(f"✓ Geocoded: {address} -> ({lat:.6f}, {lon:.6f})")
                return (lat, lon)

        logger.warning(f"✗ Could not geocode: {address}")
        return (None, None)

    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return (None, None)


def test_single_property(
    address: str,
    city: str,
    state: str,
    zip_code: str,
    imagery_service: ImageryService,
    ai_service: AIAnalysisService,
    delay_seconds: float = 3.0
) -> Dict:
    """
    Test AI detection on a single property.

    Args:
        address: Street address
        city: City
        state: State
        zip_code: ZIP code
        imagery_service: Imagery service instance
        ai_service: AI analysis service instance
        delay_seconds: Delay between properties to avoid rate limits

    Returns:
        Analysis results dictionary
    """
    logger.info("="*80)
    logger.info(f"TESTING: {address}, {city}, {state} {zip_code}")
    logger.info("="*80)

    # Geocode
    lat, lon = geocode_address(address, city, state, zip_code)

    if not lat or not lon:
        return {
            "address": address,
            "error": "geocoding_failed"
        }

    time.sleep(1)  # Rate limit geocoding

    # Get imagery
    logger.info("Fetching imagery...")
    try:
        imagery = imagery_service.fetch_imagery(lat, lon)

        satellite_url = imagery.get("satellite_url")
        street_url = imagery.get("street_view_url")

        if satellite_url:
            logger.info(f"  Satellite: {satellite_url[:80]}...")
        else:
            logger.warning("  No satellite imagery")

        if street_url:
            logger.info(f"  Street View: {street_url[:80]}...")
        else:
            logger.warning("  No street view imagery")

    except Exception as e:
        logger.error(f"Failed to get imagery: {e}")
        return {
            "address": address,
            "error": "imagery_failed"
        }

    # Wait before AI analysis to avoid rate limits
    logger.info(f"Waiting {delay_seconds}s before AI analysis...")
    time.sleep(delay_seconds)

    # Run AI analysis
    logger.info("Running AI analysis...")
    try:
        results = ai_service.analyze_property(
            latitude=lat,
            longitude=lon,
            satellite_image_url=satellite_url,
            street_image_url=street_url
        )

        # Print results
        print_results(address, results)

        return {
            "address": address,
            "lat": lat,
            "lon": lon,
            "results": results
        }

    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return {
            "address": address,
            "error": f"ai_failed: {str(e)}"
        }


def print_results(address: str, results: Dict):
    """Pretty print analysis results."""
    print("\n" + "="*80)
    print(f"RESULTS FOR: {address}")
    print("="*80)

    # Power lines
    power_lines = results.get("power_lines", {})
    power_lines_street = results.get("power_lines_street", {})

    print(f"\n🔌 POWER LINES (SATELLITE):")
    print(f"   Visible: {power_lines.get('visible', False)}")
    print(f"   Confidence: {power_lines.get('confidence', 0.0):.2f}")
    print(f"   Distance: {power_lines.get('distance_meters', 'N/A')} meters")
    print(f"   Source: {power_lines.get('source', 'N/A')}")
    if power_lines.get('details'):
        print(f"   Details: {power_lines['details'][:200]}")

    print(f"\n🔌 POWER LINES (STREET VIEW):")
    print(f"   Visible: {power_lines_street.get('visible', False)}")
    print(f"   Confidence: {power_lines_street.get('confidence', 0.0):.2f}")
    print(f"   Type: {power_lines_street.get('type', 'N/A')}")
    print(f"   Proximity: {power_lines_street.get('proximity', 'N/A')}")
    print(f"   Source: {power_lines_street.get('source', 'N/A')}")

    # Structures
    structures = results.get("nearby_structures", {})
    print(f"\n🏘️  NEARBY STRUCTURES:")
    print(f"   Detected: {structures.get('structures_detected', False)}")
    print(f"   Count: {structures.get('count', 0)}")
    print(f"   Types: {structures.get('types', [])}")
    print(f"   Density: {structures.get('density', 'N/A')}")
    print(f"   Confidence: {structures.get('confidence', 0.0):.2f}")

    # Property condition
    prop_cond = results.get("property_condition", {})
    print(f"\n🏠 PROPERTY CONDITION:")
    print(f"   Condition: {prop_cond.get('condition', 'N/A')}")
    print(f"   Maintained: {prop_cond.get('maintained', 'N/A')}")
    print(f"   Development Status: {prop_cond.get('development_status', 'N/A')}")
    print(f"   Confidence: {prop_cond.get('confidence', 0.0):.2f}")

    # Overall risk
    risk = results.get("overall_ai_risk", {})
    print(f"\n⚠️  OVERALL AI RISK:")
    print(f"   Level: {risk.get('level', 'N/A')}")
    print(f"   Score: {risk.get('score', 0)}")
    print(f"   Confidence: {risk.get('confidence', 0.0):.2f}")
    print(f"   Power Lines Detected: {risk.get('power_lines_detected', False)}")
    print(f"   Factors: {risk.get('factors', [])}")

    print(f"\n⏱️  Processing Time: {results.get('processing_time_seconds', 0):.2f}s")

    if results.get('error'):
        print(f"\n❌ ERROR: {results['error']}")

    print("="*80 + "\n")


def main():
    """Main test function."""
    csv_path = "/Users/ahmadraza/Documents/property-anyslis/backend/Export_Contacts_Cleaned Target Best Lehigh_Dec_2025_5_41_PM.csv"

    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    logger.info("="*80)
    logger.info("AI DETECTION MANUAL TESTING")
    logger.info("="*80)
    logger.info(f"CSV File: {csv_path}")

    # Initialize services
    logger.info("Initializing services...")
    imagery_service = ImageryService()
    ai_service = AIAnalysisService()

    # Read CSV
    properties = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append({
                "address": row.get("Street Address", ""),
                "city": row.get("City", ""),
                "state": row.get("State", ""),
                "zip": row.get("Postal Code", "")
            })

    logger.info(f"Found {len(properties)} properties in CSV")

    # Ask user how many to test
    print(f"\nFound {len(properties)} properties.")
    try:
        num_to_test = input("How many properties to test? (default: 3): ").strip()
        num_to_test = int(num_to_test) if num_to_test else 3
    except ValueError:
        num_to_test = 3

    num_to_test = min(num_to_test, len(properties))
    logger.info(f"Testing {num_to_test} properties...")

    # Test properties with increasing delays to avoid rate limits
    results_list = []
    base_delay = 5.0  # Start with 5 second delay

    for i, prop in enumerate(properties[:num_to_test], 1):
        logger.info(f"\n\n{'='*80}")
        logger.info(f"PROPERTY {i}/{num_to_test}")
        logger.info(f"{'='*80}")

        # Increase delay after each property to avoid cumulative rate limiting
        current_delay = base_delay + (i * 2)  # 5s, 7s, 9s, 11s...

        result = test_single_property(
            address=prop["address"],
            city=prop["city"],
            state=prop["state"],
            zip_code=prop["zip"],
            imagery_service=imagery_service,
            ai_service=ai_service,
            delay_seconds=current_delay
        )

        results_list.append(result)

        # Extra delay between properties
        if i < num_to_test:
            wait_time = 10  # 10 seconds between properties
            logger.info(f"\n⏳ Waiting {wait_time}s before next property to avoid rate limits...")
            time.sleep(wait_time)

    # Summary
    print("\n" + "="*80)
    print("TESTING COMPLETE - SUMMARY")
    print("="*80)

    successful = sum(1 for r in results_list if "results" in r)
    failed = len(results_list) - successful

    print(f"\nTotal Tested: {len(results_list)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    # Power line detection summary
    power_lines_detected = sum(
        1 for r in results_list
        if "results" in r and (
            r["results"].get("power_lines", {}).get("visible") or
            r["results"].get("power_lines_street", {}).get("visible")
        )
    )

    print(f"\n🔌 Power Lines Detected: {power_lines_detected}/{successful}")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
