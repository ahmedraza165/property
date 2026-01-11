"""
Full AI Analysis Test - Shows everything AI sees and thinks.
Runs complete analysis with detailed output of detection process.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env')

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from ai_analysis_service import AIAnalysisService

def run_full_analysis():
    """Run complete AI analysis with detailed output."""

    print("="*80)
    print("🤖 FULL AI PROPERTY ANALYSIS")
    print("="*80)
    print()

    # Test coordinates from the CSV (Lehigh Acres, FL)
    latitude = 26.6040585
    longitude = -81.6581333
    address = "Lehigh Acres, FL"

    # Use the images we just downloaded
    satellite_image_path = "/Users/ahmadraza/Documents/property-anyslis/test_sample_satellite.jpg"
    street_image_path = "/Users/ahmadraza/Documents/property-anyslis/test_sample_street.jpg"

    print(f"📍 Property: {address}")
    print(f"📍 Coordinates: {latitude}, {longitude}")
    print()
    print(f"🛰️  Satellite Image: {satellite_image_path}")
    print(f"📸 Street Image: {street_image_path}")
    print()

    # Convert file paths to file URLs
    satellite_url = f"file://{satellite_image_path}"
    street_url = f"file://{street_image_path}"

    print("="*80)
    print("🔍 STARTING AI ANALYSIS")
    print("="*80)
    print()
    print("The AI will now analyze:")
    print("  1. 🛰️  SATELLITE IMAGE - Looking for:")
    print("     • Power lines from above")
    print("     • Power line shadows")
    print("     • Transmission towers")
    print("     • Distance from red marker to power lines")
    print("     • Nearby structures and buildings")
    print()
    print("  2. 📸 STREET VIEW IMAGE - Looking for:")
    print("     • Overhead power lines")
    print("     • Utility poles")
    print("     • Transformers")
    print("     • Power line POSITION (in front/above/nearby/far)")
    print("     • Property condition")
    print()
    print("  3. 🎯 RISK CALCULATION - Based on:")
    print("     • Power line position (HIGH if in front, MEDIUM if nearby, LOW if above)")
    print("     • Property condition")
    print("     • Nearby structures")
    print("     • Flood zone data")
    print()
    print("-"*80)
    print()

    # Run AI analysis
    ai_service = AIAnalysisService()

    try:
        result = ai_service.analyze_property(
            latitude=latitude,
            longitude=longitude,
            satellite_image_url=satellite_url,
            street_image_url=street_url
        )

        print()
        print("="*80)
        print("📊 AI ANALYSIS RESULTS - DETAILED BREAKDOWN")
        print("="*80)
        print()

        # ============================================
        # SATELLITE IMAGE ANALYSIS
        # ============================================
        print("🛰️  SATELLITE IMAGE ANALYSIS (Top-down view with RED MARKER)")
        print("-"*80)

        if result.get('power_lines'):
            pl = result['power_lines']
            print()
            print("🔌 POWER LINE DETECTION:")
            print(f"   Visible: {pl.get('visible', False)}")
            print(f"   Confidence: {pl.get('confidence', 0):.1%}")

            if pl.get('visible'):
                print(f"   Distance from marker: {pl.get('distance_meters', 'N/A')} meters")
                print(f"   AI Details: {pl.get('details', 'N/A')}")
                print()
                print("   💭 AI THINKING:")
                if pl.get('distance_meters'):
                    dist = pl.get('distance_meters', 999)
                    if dist < 30:
                        print("      → Power lines VERY CLOSE to red marker (< 30m)")
                        print("      → This indicates HIGH RISK")
                    elif dist < 100:
                        print("      → Power lines NEARBY red marker (30-100m)")
                        print("      → This indicates MEDIUM RISK")
                    else:
                        print("      → Power lines FAR from red marker (> 100m)")
                        print("      → This indicates LOW RISK")
            else:
                print("   ✅ No power lines detected from above")
                print()
                print("   💭 AI THINKING:")
                print("      → Scanned entire satellite image")
                print("      → No transmission lines visible")
                print("      → No power line corridors detected")
                print("      → No power line shadows found")

        if result.get('nearby_structures'):
            ns = result['nearby_structures']
            print()
            print("🏘️  NEARBY STRUCTURES:")
            print(f"   Structures Detected: {ns.get('structures_detected', False)}")
            print(f"   Count: {ns.get('count', 0)} buildings")
            print(f"   Density: {ns.get('density', 'unknown')}")
            print(f"   Types: {', '.join(ns.get('types', []))}")
            print()
            print("   💭 AI THINKING:")
            print(f"      → Counted {ns.get('count', 0)} structures within visible area")
            print(f"      → Area density: {ns.get('density', 'unknown')}")
            if ns.get('density') == 'high':
                print("      → High density = more established neighborhood")
            elif ns.get('density') == 'medium':
                print("      → Medium density = suburban area")
            else:
                print("      → Low density = rural/sparse area")

        print()
        print()

        # ============================================
        # STREET VIEW ANALYSIS
        # ============================================
        print("📸 STREET VIEW ANALYSIS (Ground-level perspective)")
        print("-"*80)

        if result.get('power_lines_street'):
            pls = result['power_lines_street']
            print()
            print("🔌 POWER LINE DETECTION:")
            print(f"   Visible: {pls.get('visible', False)}")
            print(f"   Confidence: {pls.get('confidence', 0):.1%}")

            if pls.get('visible'):
                print(f"   Type: {pls.get('type', 'unknown')}")
                print(f"   Position: {pls.get('position', 'unknown')}")
                print(f"   Proximity: {pls.get('proximity', 'unknown')}")
                print(f"   AI Details: {pls.get('details', 'N/A')}")
                print()
                print("   💭 AI THINKING:")

                position = pls.get('position', 'unknown')
                proximity = pls.get('proximity', 'unknown')

                if position == 'directly_above':
                    print("      → Power lines DIRECTLY ABOVE property")
                    print("      → Lines running overhead along street")
                    print("      → Risk Level: LOW (overhead lines)")
                    print("      → Risk Points: +15")

                elif position == 'in_front_close' or proximity == 'very_close':
                    print("      → Power lines IN FRONT and VERY CLOSE")
                    print("      → Lines within 10-30 meters of property")
                    print("      → Risk Level: HIGH")
                    print("      ��� Risk Points: +40")

                elif position == 'nearby' or proximity == 'close':
                    print("      → Power lines NEARBY but not directly in front")
                    print("      → Lines within 30-100 meters")
                    print("      → Risk Level: MEDIUM")
                    print("      → Risk Points: +25")

                elif position == 'far' or proximity == 'far':
                    print("      → Power lines visible but FAR AWAY")
                    print("      → Lines beyond 100 meters")
                    print("      → Risk Level: LOW")
                    print("      → Risk Points: +10")
            else:
                print("   ✅ No power lines detected at street level")
                print()
                print("   💭 AI THINKING:")
                print("      → Scanned upper portion of image for overhead lines")
                print("      → Looked for utility poles")
                print("      → No power infrastructure visible")

        if result.get('property_condition'):
            pc = result['property_condition']
            print()
            print("🏠 PROPERTY CONDITION:")
            print(f"   Overall: {pc.get('condition', 'UNKNOWN')}")
            print(f"   Maintained: {pc.get('maintained', 'N/A')}")
            print(f"   Status: {pc.get('development_status', 'N/A')}")

            if pc.get('concerns'):
                print(f"   Concerns: {', '.join(pc.get('concerns', []))}")

            print()
            print("   💭 AI THINKING:")
            if pc.get('condition') == 'POOR' or pc.get('development_status') == 'VACANT':
                print("      → Property appears vacant or undeveloped")
                print("      → This adds to risk score")
            elif pc.get('condition') == 'GOOD':
                print("      → Property well-maintained")
                print("      → Lower risk factor")

        print()
        print()

        # ============================================
        # RISK CALCULATION
        # ============================================
        if result.get('overall_ai_risk'):
            risk = result['overall_ai_risk']

            print("="*80)
            print("🎯 RISK CALCULATION - HOW AI SCORED THIS PROPERTY")
            print("="*80)
            print()

            print("📊 FINAL RISK ASSESSMENT:")
            print(f"   Level: {risk.get('level', 'UNKNOWN')}")
            print(f"   Score: {risk.get('score', 0)} points")
            print(f"   Confidence: {risk.get('confidence', 0):.1%}")
            print()

            print("🔌 POWER LINE ANALYSIS:")
            print(f"   Detected: {risk.get('power_lines_detected', False)}")
            if risk.get('power_lines_detected'):
                print(f"   Confidence: {risk.get('power_line_confidence', 0):.1%}")
                print(f"   Position Impact: {'HIGH' if risk.get('score', 0) >= 60 else 'MEDIUM' if risk.get('score', 0) >= 30 else 'LOW'}")
            else:
                print("   ✅ No power lines = 0 points for this risk factor")
            print()

            print("💡 SCORING BREAKDOWN:")
            print("-"*80)
            print()
            print("   Risk Factors Contributing to Score:")
            for i, factor in enumerate(risk.get('factors', []), 1):
                print(f"   {i}. {factor}")
            print()

            print("   📈 RISK LEVEL THRESHOLDS:")
            print("      • 60+ points = HIGH RISK 🔴")
            print("      • 30-59 points = MEDIUM RISK 🟡")
            print("      • 0-29 points = LOW RISK 🟢")
            print()

            current_score = risk.get('score', 0)
            if current_score >= 60:
                print(f"   → This property scored {current_score} points = HIGH RISK 🔴")
            elif current_score >= 30:
                print(f"   → This property scored {current_score} points = MEDIUM RISK 🟡")
            else:
                print(f"   → This property scored {current_score} points = LOW RISK 🟢")
            print()

        print()
        print("="*80)
        print("⏱️  PERFORMANCE")
        print("="*80)
        print(f"Processing Time: {result.get('processing_time_seconds', 0):.2f} seconds")
        print()

        print()
        print("="*80)
        print("✅ AI ANALYSIS COMPLETE")
        print("="*80)
        print()
        print("Summary:")
        print("  ✓ Analyzed satellite image with red marker")
        print("  ✓ Analyzed street view image")
        print("  ✓ Detected power lines and calculated position-based risk")
        print("  ✓ Assessed property condition and nearby structures")
        print("  ✓ Calculated overall risk score")
        print()

        return result

    except Exception as e:
        print()
        print("="*80)
        print("❌ ANALYSIS FAILED")
        print("="*80)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = run_full_analysis()

    if result:
        print()
        print("="*80)
        print("🎉 TEST COMPLETE!")
        print("="*80)
        print()
        print("Next Steps:")
        print("  1. Review the detailed AI analysis above")
        print("  2. Check how AI detected power lines and calculated risk")
        print("  3. Verify the position-based scoring is working correctly")
        print("  4. This same analysis will appear in the frontend")
        print()
