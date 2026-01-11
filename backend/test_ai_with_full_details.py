"""
Complete AI Analysis with Full Details - Shows everything AI sees and calculates.
This is the format that will be shown in the frontend.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

# Load environment variables
load_dotenv('.env')

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from imagery_service import ImageryService
from ai_analysis_service import AIAnalysisService

def format_percentage(value):
    """Format confidence as percentage."""
    return f"{value * 100:.0f}%"

def print_section(title, char="="):
    """Print a formatted section header."""
    print()
    print(char * 80)
    print(title)
    print(char * 80)
    print()

def run_analysis_with_details(address, latitude, longitude):
    """Run complete analysis with detailed output."""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print_section("🏠 PROPERTY ANALYSIS REPORT")

    print(f"📅 Analysis Date: {timestamp}")
    print(f"📍 Address: {address}")
    print(f"📍 Coordinates: {latitude}, {longitude}")
    print()

    # STEP 1: Fetch Imagery
    print_section("STEP 1: FETCHING PROPERTY IMAGES", "-")

    print("🛰️  Downloading satellite image with RED MARKER...")
    print("📸 Downloading street view image...")
    print()

    imagery_service = ImageryService()

    try:
        imagery = imagery_service.fetch_imagery(latitude, longitude)

        print("✅ Images Downloaded Successfully")
        print()
        print(f"   Satellite: {imagery['satellite']['source']}")
        print(f"   • Zoom Level: 18 (balanced view ~200m radius)")
        print(f"   • Red Marker: Added at exact property location")
        print(f"   • Resolution: High (@2x, 800x800 pixels)")
        print()
        print(f"   Street View: {imagery['street']['source']}")
        print(f"   • Ground-level perspective")
        print(f"   • 800x600 pixels")
        print()

        # STEP 2: Run AI Analysis
        print_section("STEP 2: AI ANALYSIS - WHAT THE AI SEES", "-")

        print("🤖 Sending images to AI model (GPT-4o Vision)...")
        print()

        ai_service = AIAnalysisService()

        result = ai_service.analyze_property(
            latitude=latitude,
            longitude=longitude,
            satellite_image_url=imagery['satellite']['url'],
            street_image_url=imagery['street']['url']
        )

        # SATELLITE ANALYSIS
        print_section("🛰️  SATELLITE IMAGE ANALYSIS")

        print("What the AI sees in this image:")
        print("  • Top-down aerial view with RED MARKER at property center")
        print("  • Coverage area: ~200 meter radius around property")
        print("  • Can identify: power lines, structures, vegetation, terrain")
        print()

        # Power Lines (Satellite)
        if result.get('power_lines'):
            pl = result['power_lines']
            print("🔌 POWER LINE DETECTION (from above):")
            print("-" * 40)
            print(f"   Detected: {'YES' if pl.get('visible') else 'NO'}")
            print(f"   Confidence: {format_percentage(pl.get('confidence', 0))}")

            if pl.get('visible'):
                print(f"   Distance from marker: {pl.get('distance_meters', 'N/A')} meters")
                print()
                print("   💭 AI ANALYSIS:")
                print(f"      '{pl.get('details', 'N/A')}'")
                print()

                dist = pl.get('distance_meters', 999)
                if dist and dist != 'N/A':
                    try:
                        dist_val = int(dist) if isinstance(dist, str) else dist
                        print("   🎯 RISK IMPACT:")
                        if dist_val < 30:
                            print("      → VERY CLOSE (< 30m) = HIGH RISK ⚠️")
                            print("      → Power lines directly adjacent to property")
                        elif dist_val < 100:
                            print("      → NEARBY (30-100m) = MEDIUM RISK ⚠️")
                            print("      → Power lines within moderate distance")
                        else:
                            print("      → FAR (> 100m) = LOW RISK ✓")
                            print("      → Power lines at safe distance")
                    except:
                        pass
            else:
                print()
                print("   💭 AI ANALYSIS:")
                print(f"      '{pl.get('details', 'No power line infrastructure detected.')}'")
                print()
                print("   ✅ NO RISK: No power lines visible from satellite view")

        # Nearby Structures
        if result.get('nearby_structures'):
            ns = result['nearby_structures']
            print()
            print("🏘️  NEARBY STRUCTURES:")
            print("-" * 40)
            print(f"   Structures Detected: {'YES' if ns.get('structures_detected') else 'NO'}")
            print(f"   Count: {ns.get('count', 0)} buildings")
            print(f"   Density: {ns.get('density', 'unknown').upper()}")
            print(f"   Types: {', '.join(ns.get('types', []))}")
            print()
            print("   💭 AI INTERPRETATION:")

            density = ns.get('density', 'unknown')
            if density == 'high':
                print("      → High density area = Established neighborhood")
                print("      → Many nearby properties and infrastructure")
            elif density == 'medium':
                print("      → Medium density = Suburban development")
                print("      → Moderate level of surrounding buildings")
            elif density == 'low':
                print("      → Low density = Rural/sparse area")
                print("      → Few nearby structures, isolated location")
            else:
                print("      → Density assessment uncertain")

        # STREET VIEW ANALYSIS
        print()
        print_section("📸 STREET VIEW ANALYSIS")

        print("What the AI sees in this image:")
        print("  • Ground-level perspective of property")
        print("  • Can identify: overhead power lines, utility poles, property condition")
        print()

        # Power Lines (Street)
        if result.get('power_lines_street'):
            pls = result['power_lines_street']
            print("🔌 POWER LINE DETECTION (ground level):")
            print("-" * 40)
            print(f"   Detected: {'YES' if pls.get('visible') else 'NO'}")
            print(f"   Confidence: {format_percentage(pls.get('confidence', 0))}")

            if pls.get('visible'):
                print(f"   Type: {pls.get('type', 'unknown').upper()}")
                print(f"   Position: {pls.get('position', 'unknown').upper()}")
                print(f"   Proximity: {pls.get('proximity', 'unknown').upper()}")
                print()
                print("   💭 AI ANALYSIS:")
                print(f"      '{pls.get('details', 'N/A')}'")
                print()

                position = pls.get('position', 'unknown')
                proximity = pls.get('proximity', 'unknown')

                print("   🎯 RISK CALCULATION:")

                if position == 'directly_above':
                    print("      → Position: DIRECTLY ABOVE property")
                    print("      → Risk Level: LOW (overhead lines)")
                    print("      → Risk Points: +15")
                    print("      → Reasoning: Lines run overhead but don't pose major risk")

                elif position == 'in_front_close' or proximity == 'very_close':
                    print("      → Position: IN FRONT and VERY CLOSE")
                    print("      → Risk Level: HIGH ⚠️⚠️⚠️")
                    print("      → Risk Points: +40")
                    print("      → Reasoning: Power lines within 10-30m of property front")

                elif position == 'nearby' or proximity == 'close':
                    print("      → Position: NEARBY but not directly in front")
                    print("      → Risk Level: MEDIUM ⚠️⚠️")
                    print("      → Risk Points: +25")
                    print("      → Reasoning: Power lines within 30-100m range")

                elif position == 'far' or proximity in ['moderate', 'far']:
                    print("      → Position: FAR from property")
                    print("      → Risk Level: LOW ✓")
                    print("      → Risk Points: +10")
                    print("      → Reasoning: Power lines beyond 100m, minimal impact")

            else:
                print()
                print("   💭 AI ANALYSIS:")
                print(f"      '{pls.get('details', 'No overhead power infrastructure visible.')}'")
                print()
                print("   ✅ NO RISK: No power lines visible at ground level")

        # Property Condition
        if result.get('property_condition'):
            pc = result['property_condition']
            print()
            print("🏠 PROPERTY CONDITION ASSESSMENT:")
            print("-" * 40)
            print(f"   Overall Condition: {pc.get('condition', 'UNKNOWN')}")
            print(f"   Well Maintained: {pc.get('maintained', 'N/A')}")
            print(f"   Development Status: {pc.get('development_status', 'N/A').upper()}")

            if pc.get('concerns'):
                print(f"   Concerns Identified: {len(pc.get('concerns', []))}")
                for concern in pc.get('concerns', []):
                    print(f"      • {concern}")

            print()
            print("   💭 AI INTERPRETATION:")

            condition = pc.get('condition', 'UNKNOWN')
            dev_status = pc.get('development_status', 'unknown')

            if condition == 'POOR' or dev_status == 'vacant':
                print("      → Property appears VACANT or UNDEVELOPED")
                print("      → This indicates potential issues or lack of maintenance")
                print("      → Risk Factor: Property condition concerns")
            elif condition == 'GOOD':
                print("      → Property appears WELL-MAINTAINED")
                print("      → Good condition reduces overall risk")
            elif dev_status == 'undeveloped':
                print("      → Property is UNDEVELOPED land")
                print("      → No structures present, vacant lot")

        # RISK CALCULATION BREAKDOWN
        print()
        print_section("🎯 OVERALL RISK ASSESSMENT - HOW AI CALCULATES SCORE")

        if result.get('overall_ai_risk'):
            risk = result['overall_ai_risk']

            risk_level = risk.get('level', 'UNKNOWN')
            risk_score = risk.get('score', 0)
            risk_conf = risk.get('confidence', 0)

            # Show final result prominently
            if risk_level == 'HIGH':
                print("🔴 RISK LEVEL: HIGH")
            elif risk_level == 'MEDIUM':
                print("🟡 RISK LEVEL: MEDIUM")
            else:
                print("🟢 RISK LEVEL: LOW")

            print()
            print(f"   Total Score: {risk_score} points")
            print(f"   Confidence: {format_percentage(risk_conf)}")
            print()

            # Show scoring thresholds
            print("📊 SCORING SYSTEM:")
            print("-" * 40)
            print("   60+ points  = HIGH RISK 🔴")
            print("   30-59 points = MEDIUM RISK 🟡")
            print("   0-29 points  = LOW RISK 🟢")
            print()
            print(f"   This property: {risk_score} points → {risk_level} RISK")
            print()

            # Power line specific analysis
            print("🔌 POWER LINE RISK:")
            print("-" * 40)

            if risk.get('power_lines_detected'):
                print(f"   ⚠️  POWER LINES DETECTED")
                print(f"   Confidence: {format_percentage(risk.get('power_line_confidence', 0))}")
                print()

                # Explain which detection method found them
                if result.get('power_lines', {}).get('visible'):
                    print("   📡 Detected from: Satellite view (aerial perspective)")
                if result.get('power_lines_street', {}).get('visible'):
                    print("   📸 Detected from: Street view (ground perspective)")

            else:
                print("   ✅ NO POWER LINES DETECTED")
                print("   Power line risk factor: 0 points")

            print()

            # Detailed risk factor breakdown
            print("💡 RISK FACTORS BREAKDOWN:")
            print("-" * 40)

            factors = risk.get('factors', [])
            if factors:
                print()
                print("   The following factors contributed to the risk score:")
                print()
                for i, factor in enumerate(factors, 1):
                    print(f"   {i}. {factor}")
            else:
                print("   No significant risk factors identified")

            print()

            # Explain each component
            print("🧮 HOW THE SCORE WAS CALCULATED:")
            print("-" * 40)
            print()
            print("   The AI analyzed multiple risk categories:")
            print()

            # Power Lines
            has_power = risk.get('power_lines_detected', False)
            if has_power:
                if 'HIGH RISK: Power lines in front' in str(factors):
                    print("   🔌 Power Lines: +40 points (IN FRONT/VERY CLOSE)")
                elif 'MEDIUM RISK: Power lines nearby' in str(factors):
                    print("   🔌 Power Lines: +25 points (NEARBY)")
                elif 'LOW RISK: Power lines overhead' in str(factors):
                    print("   🔌 Power Lines: +15 points (OVERHEAD)")
                else:
                    print("   🔌 Power Lines: +10 points (FAR/VISIBLE)")
            else:
                print("   🔌 Power Lines: 0 points (none detected)")

            # Property Condition
            if 'Undeveloped property' in str(factors) or 'vacant' in str(factors).lower():
                print("   🏚️  Property Condition: +20 points (VACANT/UNDEVELOPED)")
            elif 'concerns identified' in str(factors).lower():
                concern_count = str(factors).count('concern')
                print(f"   🏚️  Property Condition: +{concern_count * 6} points (maintenance concerns)")

            # Road Condition
            if 'Unpaved' in str(factors) or 'dirt road' in str(factors).lower():
                print("   🛣️  Road Access: +20 points (DIRT/UNPAVED ROAD)")
            elif 'gravel' in str(factors).lower():
                print("   🛣️  Road Access: +10 points (GRAVEL ROAD)")

            # Density
            if 'Low density' in str(factors):
                print("   🏘️  Area Density: +10 points (FEW NEARBY STRUCTURES)")
            elif 'Medium density' in str(factors):
                print("   🏘️  Area Density: +5 points (MODERATE DENSITY)")

            print()
            print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"   TOTAL RISK SCORE: {risk_score} points")
            print()

        # Performance
        print_section("⏱️  PROCESSING PERFORMANCE", "-")

        print(f"Total Processing Time: {result.get('processing_time_seconds', 0):.2f} seconds")
        print()
        print("Breakdown:")
        print("  • Image download: ~2-3 seconds")
        print("  • AI analysis (5 models): ~30-35 seconds")
        print("  • Risk calculation: < 1 second")
        print()

        # Summary
        print_section("✅ ANALYSIS COMPLETE")

        print("This analysis used:")
        print("  ✓ Satellite imagery with red property marker")
        print("  ✓ Street view imagery for ground-level perspective")
        print("  ✓ GPT-4o Vision AI model for image analysis")
        print("  ✓ Position-based power line risk scoring")
        print("  ✓ Multi-factor risk assessment algorithm")
        print()

        if risk_level == 'HIGH':
            print("⚠️  ACTION RECOMMENDED: This property has HIGH RISK factors")
            print("    Review the risk factors above and consider additional due diligence.")
        elif risk_level == 'MEDIUM':
            print("⚠️  CAUTION: This property has MEDIUM RISK factors")
            print("    Review the specific concerns identified by the AI.")
        else:
            print("✅ LOW RISK: This property appears to have minimal risk factors")

        print()

        return result

    except Exception as e:
        print()
        print_section("❌ ANALYSIS FAILED")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test with real property
    test_address = "909 Monroe Ave, Lehigh Acres, FL 33972"
    test_lat = 26.6331012
    test_lon = -81.5775364

    result = run_analysis_with_details(test_address, test_lat, test_lon)
