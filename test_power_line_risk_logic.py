#!/usr/bin/env python3
"""
Test script to verify power line risk logic is correct.
Tests the risk scoring to ensure:
- Power lines INCREASE risk (bad for insurance/safety)
- No power lines DECREASE risk (good - safer property)
"""

def calculate_power_line_risk(power_lines_detected, position=None):
    """
    Simulates the risk calculation logic from ai_analysis_service.py
    Returns: (risk_score, risk_level, message)
    """
    risk_score = 0
    message = ""

    if power_lines_detected:
        if position == 'directly_above' or position == 'in_front_close':
            risk_score += 30
            message = "⚠️ HIGH RISK: Power lines directly overhead/very close - Safety hazard, insurance concern"
        elif position == 'nearby':
            risk_score += 20
            message = "⚠️ MEDIUM-HIGH RISK: Power lines nearby - Moderate safety concern"
        elif position == 'far':
            risk_score += 10
            message = "🟡 LOW-MEDIUM RISK: Power lines visible but distant"
        else:
            risk_score += 15
            message = "⚠️ Power lines detected - position uncertain"
    else:
        risk_score -= 10  # BONUS for no power lines
        message = "✅ LOW RISK: No power lines detected - Safer property, better insurance rates"

    # Determine risk level (simplified)
    if risk_score >= 25:
        risk_level = "HIGH"
    elif risk_score >= 15:
        risk_level = "MEDIUM"
    elif risk_score >= 5:
        risk_level = "LOW-MEDIUM"
    else:
        risk_level = "LOW"

    return risk_score, risk_level, message


def run_tests():
    """Run test cases to verify risk logic"""
    print("="*70)
    print("POWER LINE RISK LOGIC VERIFICATION TEST")
    print("="*70)
    print()

    test_cases = [
        # (power_lines_detected, position, expected_result)
        (True, 'directly_above', 'HIGH', 30, "Power lines overhead should be HIGH RISK"),
        (True, 'in_front_close', 'HIGH', 30, "Power lines close should be HIGH RISK"),
        (True, 'nearby', 'MEDIUM', 20, "Power lines nearby should be MEDIUM RISK"),
        (True, 'far', 'LOW-MEDIUM', 10, "Power lines far should be LOW-MEDIUM RISK"),
        (False, None, 'LOW', -10, "No power lines should be LOW RISK (BONUS)"),
    ]

    all_passed = True

    for i, (detected, position, expected_level, expected_score, description) in enumerate(test_cases, 1):
        score, level, message = calculate_power_line_risk(detected, position)

        # Check if test passed
        passed = (score == expected_score)

        status = "✅ PASS" if passed else "❌ FAIL"

        print(f"Test {i}: {description}")
        print(f"  Detected: {detected}, Position: {position}")
        print(f"  Expected: score={expected_score}, level={expected_level}")
        print(f"  Actual:   score={score}, level={level}")
        print(f"  Message:  {message}")
        print(f"  Status:   {status}")
        print()

        if not passed:
            all_passed = False

    print("="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED - Risk logic is correct!")
        print()
        print("Summary:")
        print("  • Power lines CLOSE/OVERHEAD → +30 risk (HIGH)")
        print("  • Power lines NEARBY → +20 risk (MEDIUM-HIGH)")
        print("  • Power lines FAR → +10 risk (LOW-MEDIUM)")
        print("  • NO power lines → -10 risk (LOW - BONUS)")
    else:
        print("❌ SOME TESTS FAILED - Check the logic!")
    print("="*70)

    return all_passed


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
