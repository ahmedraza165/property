"""
Test script for power line detection with new position-based risk scoring.

This script tests:
1. Debug logging output
2. Position-based risk scoring
3. AI detection with enhanced prompts
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
load_dotenv('backend/.env')

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ai_analysis_service import AIAnalysisService

def test_risk_scoring():
    """Test the position-based risk scoring logic."""

    logger.info("="*80)
    logger.info("TESTING POWER LINE RISK SCORING")
    logger.info("="*80)

    # Test cases for different power line positions
    test_cases = [
        {
            "name": "Power lines directly above property",
            "power_lines_street": {
                "visible": True,
                "confidence": 0.9,
                "type": "overhead_lines",
                "position": "directly_above",
                "proximity": "very_close"
            },
            "expected_risk": "LOW (15 points)"
        },
        {
            "name": "Power lines in front/very close to property",
            "power_lines_street": {
                "visible": True,
                "confidence": 0.85,
                "type": "utility_poles",
                "position": "in_front_close",
                "proximity": "very_close"
            },
            "expected_risk": "HIGH (40 points)"
        },
        {
            "name": "Power lines nearby property",
            "power_lines_street": {
                "visible": True,
                "confidence": 0.8,
                "type": "overhead_lines",
                "position": "nearby",
                "proximity": "close"
            },
            "expected_risk": "MEDIUM (25 points)"
        },
        {
            "name": "Power lines far from property",
            "power_lines_street": {
                "visible": True,
                "confidence": 0.7,
                "type": "transmission_lines",
                "position": "far",
                "proximity": "far"
            },
            "expected_risk": "LOW (10 points)"
        },
        {
            "name": "No power lines detected",
            "power_lines_street": {
                "visible": False,
                "confidence": 0.1
            },
            "expected_risk": "NONE (0 points)"
        }
    ]

    service = AIAnalysisService()

    for i, test_case in enumerate(test_cases, 1):
        logger.info("")
        logger.info(f"{'='*80}")
        logger.info(f"TEST CASE {i}: {test_case['name']}")
        logger.info(f"{'='*80}")

        # Calculate risk for this test case
        result = service._calculate_overall_ai_risk(
            road_condition=None,
            power_lines=None,
            power_lines_street=test_case['power_lines_street'],
            nearby_structures=None,
            property_condition=None,
            nearby_development=None
        )

        logger.info("")
        logger.info(f"📊 RESULT:")
        logger.info(f"   Risk Level: {result['level']}")
        logger.info(f"   Risk Score: {result['score']}")
        logger.info(f"   Confidence: {result['confidence']:.2f}")
        logger.info(f"   Factors: {result['factors']}")
        logger.info(f"   Expected: {test_case['expected_risk']}")
        logger.info("")

    logger.info("="*80)
    logger.info("✅ ALL TEST CASES COMPLETED")
    logger.info("="*80)
    logger.info("")
    logger.info("📋 RISK SCORING SUMMARY:")
    logger.info("   🔴 HIGH RISK (40 pts): Power lines in front or very close to property")
    logger.info("   🟡 MEDIUM RISK (25 pts): Power lines nearby but not directly in front")
    logger.info("   🟢 LOW RISK (15 pts): Power lines overhead/above property")
    logger.info("   🟢 LOW RISK (10 pts): Power lines far from property")
    logger.info("   ✅ NO RISK (0 pts): No power lines detected")
    logger.info("")
    logger.info("🎯 Risk scoring is based on POSITION relative to property:")
    logger.info("   - 'directly_above' = LOW (overhead, less impact)")
    logger.info("   - 'in_front_close' = HIGH (major safety/insurability concern)")
    logger.info("   - 'nearby' = MEDIUM (moderate concern)")
    logger.info("   - 'far' = LOW (minimal impact)")
    logger.info("="*80)

if __name__ == "__main__":
    test_risk_scoring()
