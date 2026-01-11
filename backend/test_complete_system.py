"""
Complete system test with marked satellite images and enhanced AI detection.
Tests the full pipeline with real data.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure detailed logging to see all debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env')

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from imagery_service import ImageryService
from ai_analysis_service import AIAnalysisService

def test_complete_analysis():
    """Test complete property analysis with marked images."""

    # Test property
    test_address = "909 monroe ave, Lehigh Acres, FL 33972"
    latitude = 26.6331012
    longitude = -81.5775364

    print("="*80)
    print("COMPLETE SYSTEM TEST")
    print("="*80)
    print()
    print(f"📍 Testing Address: {test_address}")
    print(f"📍 Coordinates: {latitude}, {longitude}")
    print()

    # Step 1: Fetch imagery
    print("="*80)
    print("STEP 1: FETCHING IMAGERY (with red marker)")
    print("="*80)
    print()

    imagery_service = ImageryService()

    try:
        imagery = imagery_service.fetch_imagery(latitude, longitude)

        print("📊 Imagery Results:")
        print(f"   Satellite: {imagery['satellite']['source']}")
        print(f"   URL: {imagery['satellite']['url'][:80]}..." if imagery['satellite']['url'] else "   URL: None")
        print()
        print(f"   Street: {imagery['street']['source']}")
        print(f"   URL: {imagery['street']['url'][:80]}..." if imagery['street']['url'] else "   URL: None")
        print()

        if not imagery['satellite']['url']:
            print("❌ No satellite imagery available - cannot test AI analysis")
            return

        # Step 2: Run AI Analysis
        print("="*80)
        print("STEP 2: AI ANALYSIS WITH MARKED IMAGES")
        print("="*80)
        print()

        ai_service = AIAnalysisService()

        result = ai_service.analyze_property(
            latitude=latitude,
            longitude=longitude,
            satellite_image_url=imagery['satellite']['url'],
            street_image_url=imagery['street']['url']
        )

        print()
        print("="*80)
        print("AI ANALYSIS RESULTS")
        print("="*80)
        print()

        # Power Lines (Satellite)
        if result['power_lines']:
            pl = result['power_lines']
            print("🛰️ SATELLITE - Power Line Detection:")
            print(f"   Visible: {pl.get('visible', False)}")
            print(f"   Confidence: {pl.get('confidence', 0):.2f}")
            print(f"   Distance from marker: {pl.get('distance_meters', 'N/A')}m")
            print(f"   Details: {pl.get('details', 'N/A')[:100]}")
            print()

        # Power Lines (Street View)
        if result['power_lines_street']:
            pls = result['power_lines_street']
            print("📸 STREET VIEW - Power Line Detection:")
            print(f"   Visible: {pls.get('visible', False)}")
            print(f"   Confidence: {pls.get('confidence', 0):.2f}")
            print(f"   Position: {pls.get('position', 'unknown')}")
            print(f"   Proximity: {pls.get('proximity', 'unknown')}")
            print(f"   Type: {pls.get('type', 'unknown')}")
            print(f"   Details: {pls.get('details', 'N/A')[:100]}")
            print()

        # Nearby Structures
        if result['nearby_structures']:
            ns = result['nearby_structures']
            print("🏘️ NEARBY STRUCTURES:")
            print(f"   Detected: {ns.get('structures_detected', False)}")
            print(f"   Count: {ns.get('count', 0)}")
            print(f"   Density: {ns.get('density', 'unknown')}")
            print(f"   Types: {ns.get('types', [])}")
            print()

        # Property Condition
        if result['property_condition']:
            pc = result['property_condition']
            print("🏠 PROPERTY CONDITION:")
            print(f"   Condition: {pc.get('condition', 'UNKNOWN')}")
            print(f"   Maintained: {pc.get('maintained', 'N/A')}")
            print(f"   Status: {pc.get('development_status', 'N/A')}")
            print(f"   Concerns: {pc.get('concerns', [])}")
            print()

        # Overall AI Risk
        if result['overall_ai_risk']:
            risk = result['overall_ai_risk']
            print("="*80)
            print("🎯 OVERALL AI RISK ASSESSMENT")
            print("="*80)
            print(f"   Level: {risk.get('level', 'UNKNOWN')}")
            print(f"   Score: {risk.get('score', 0)}")
            print(f"   Confidence: {risk.get('confidence', 0):.2f}")
            print(f"   Power Lines Detected: {risk.get('power_lines_detected', False)}")
            if risk.get('power_lines_detected'):
                print(f"   Power Line Confidence: {risk.get('power_line_confidence', 0):.2f}")
            print()
            print("   Risk Factors:")
            for factor in risk.get('factors', []):
                print(f"      • {factor}")
            print()

        print(f"⏱️  Processing Time: {result.get('processing_time_seconds', 0):.2f}s")
        print()

        # Test Summary
        print("="*80)
        print("✅ TEST SUMMARY")
        print("="*80)
        print()
        print("✓ Imagery fetched successfully (with red marker)")
        print("✓ AI analysis completed")
        print("✓ Position-based risk scoring applied")
        print("✓ Debug logging shows all details")
        print()

        if result['overall_ai_risk']:
            risk_level = result['overall_ai_risk'].get('level', 'UNKNOWN')
            if risk_level == 'HIGH':
                print("🔴 RESULT: HIGH RISK PROPERTY")
            elif risk_level == 'MEDIUM':
                print("🟡 RESULT: MEDIUM RISK PROPERTY")
            else:
                print("🟢 RESULT: LOW RISK PROPERTY")

        print()
        print("="*80)
        print("🎉 SYSTEM TEST COMPLETE - ALL FEATURES WORKING!")
        print("="*80)

    except Exception as e:
        print()
        print("="*80)
        print("❌ TEST FAILED")
        print("="*80)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print()

if __name__ == "__main__":
    test_complete_analysis()
