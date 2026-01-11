#!/usr/bin/env python3
"""
Complete CSV Processing Flow Test
Tests the entire pipeline: Upload -> GIS Analysis -> AI Analysis
Validates that ALL properties are processed with no "UNKNOWN" states
"""

import requests
import time
import json
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000"
CSV_FILE = "backend/Export_Contacts_Cleaned Target Best Lehigh_Dec_2025_5_41_PM.csv"

def log_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def log_info(message):
    """Print info message"""
    print(f"✓ {message}")

def log_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")

def log_error(message):
    """Print error message"""
    print(f"✗ {message}")

def test_server_health():
    """Test if the server is running"""
    log_section("1. TESTING SERVER HEALTH")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            log_info("Server is healthy and responsive")
            return True
        else:
            log_error(f"Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Cannot connect to server: {str(e)}")
        log_info("Please start the server with: cd backend && uvicorn main:app --reload")
        return False

def upload_csv():
    """Upload the CSV file"""
    log_section("2. UPLOADING CSV FILE")

    csv_path = Path(CSV_FILE)
    if not csv_path.exists():
        log_error(f"CSV file not found: {CSV_FILE}")
        return None

    log_info(f"Reading CSV file: {csv_path}")
    log_info(f"File size: {csv_path.stat().st_size} bytes")

    with open(csv_path, 'rb') as f:
        files = {'file': (csv_path.name, f, 'text/csv')}
        try:
            response = requests.post(f"{API_BASE}/process-csv", files=files, timeout=30)

            if response.status_code == 200:
                data = response.json()
                job_id = data.get('job_id')
                total_rows = data.get('total_rows')

                log_info(f"Upload successful!")
                log_info(f"Job ID: {job_id}")
                log_info(f"Total properties: {total_rows}")

                return job_id
            else:
                log_error(f"Upload failed: {response.status_code}")
                log_error(f"Response: {response.text}")
                return None
        except Exception as e:
            log_error(f"Upload error: {str(e)}")
            return None

def monitor_processing(job_id, expected_count):
    """Monitor the processing status until completion"""
    log_section("3. MONITORING PROPERTY PROCESSING (GIS Analysis)")

    log_info(f"Monitoring job: {job_id}")
    log_info(f"Expected properties: {expected_count}")

    start_time = time.time()
    last_processed = 0

    while True:
        try:
            response = requests.get(f"{API_BASE}/status/{job_id}", timeout=10)

            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                processed = data.get('processed_rows', 0)
                total = data.get('total_rows', 0)
                progress = data.get('progress_percentage', 0)

                # Show progress update
                if processed != last_processed:
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    eta = (total - processed) / rate if rate > 0 else 0

                    print(f"\r  Progress: {processed}/{total} ({progress}%) - "
                          f"{rate:.1f} props/sec - ETA: {eta:.0f}s", end='')
                    last_processed = processed

                if status == 'completed':
                    print()  # New line after progress
                    log_info(f"Processing complete in {elapsed:.1f}s!")
                    log_info(f"Processed: {processed}/{total} properties")
                    return True
                elif status == 'failed':
                    print()
                    log_error(f"Processing failed: {data.get('error_message')}")
                    return False

                time.sleep(2)  # Poll every 2 seconds
            else:
                log_error(f"Status check failed: {response.status_code}")
                return False

        except Exception as e:
            log_error(f"Monitoring error: {str(e)}")
            return False

        # Timeout after 5 minutes
        if time.time() - start_time > 300:
            log_error("Processing timeout (5 minutes)")
            return False

def verify_gis_results(job_id):
    """Verify GIS processing results"""
    log_section("4. VERIFYING GIS ANALYSIS RESULTS")

    try:
        response = requests.get(f"{API_BASE}/results/{job_id}", timeout=30)

        if response.status_code != 200:
            log_error(f"Failed to get results: {response.status_code}")
            return False

        data = response.json()
        results = data.get('results', [])

        log_info(f"Retrieved {len(results)} property results")

        # Analyze results
        issues = []
        stats = {
            'total': len(results),
            'has_coordinates': 0,
            'has_risk_data': 0,
            'unknown_risk': 0,
            'missing_fields': 0
        }

        for idx, result in enumerate(results, 1):
            address = result.get('address', {}).get('full_address', 'Unknown')
            coords = result.get('coordinates')
            risk = result.get('phase1_risk', {})

            # Check coordinates
            if coords and coords.get('latitude') and coords.get('longitude'):
                stats['has_coordinates'] += 1
            else:
                issues.append(f"Property {idx} ({address}): Missing coordinates")

            # Check risk data
            overall_risk = risk.get('overall_risk')
            if overall_risk:
                stats['has_risk_data'] += 1
                if overall_risk == 'UNKNOWN':
                    stats['unknown_risk'] += 1
                    issues.append(f"Property {idx} ({address}): Risk is UNKNOWN")
            else:
                stats['missing_fields'] += 1
                issues.append(f"Property {idx} ({address}): Missing risk data")

        # Print statistics
        log_info(f"Properties with coordinates: {stats['has_coordinates']}/{stats['total']}")
        log_info(f"Properties with risk data: {stats['has_risk_data']}/{stats['total']}")

        if stats['unknown_risk'] > 0:
            log_warning(f"Properties with UNKNOWN risk: {stats['unknown_risk']}")

        if stats['missing_fields'] > 0:
            log_warning(f"Properties with missing data: {stats['missing_fields']}")

        # Print issues
        if issues:
            log_warning(f"Found {len(issues)} issues:")
            for issue in issues[:10]:  # Show first 10
                print(f"    - {issue}")
            if len(issues) > 10:
                print(f"    ... and {len(issues) - 10} more")
        else:
            log_info("All properties processed successfully!")

        return len(issues) == 0

    except Exception as e:
        log_error(f"Verification error: {str(e)}")
        return False

def trigger_ai_analysis(job_id):
    """Trigger AI analysis for all properties"""
    log_section("5. TRIGGERING AI ANALYSIS")

    try:
        response = requests.post(f"{API_BASE}/analyze-ai/{job_id}", timeout=30)

        if response.status_code == 200:
            data = response.json()
            log_info(f"AI analysis started!")
            log_info(f"Total properties: {data.get('total_properties')}")
            log_info(f"Existing AI results: {data.get('existing_ai_results')}")
            return True
        else:
            log_error(f"Failed to trigger AI analysis: {response.status_code}")
            log_error(f"Response: {response.text}")
            return False
    except Exception as e:
        log_error(f"AI trigger error: {str(e)}")
        return False

def monitor_ai_processing(job_id, expected_count):
    """Monitor AI analysis progress"""
    log_section("6. MONITORING AI ANALYSIS")

    log_info(f"Waiting for AI analysis to complete...")
    log_info(f"Expected properties: {expected_count}")
    log_info("Note: AI analysis is slower due to image processing and vision API calls")

    start_time = time.time()
    last_count = 0

    while True:
        try:
            response = requests.get(f"{API_BASE}/ai-results/{job_id}", timeout=30)

            if response.status_code == 200:
                data = response.json()
                count = data.get('total_results', 0)

                # Show progress update
                if count != last_count:
                    elapsed = time.time() - start_time
                    rate = count / elapsed if elapsed > 0 else 0
                    eta = (expected_count - count) / rate if rate > 0 else 0
                    progress = (count / expected_count * 100) if expected_count > 0 else 0

                    print(f"\r  AI Progress: {count}/{expected_count} ({progress:.1f}%) - "
                          f"{rate:.2f} props/sec - ETA: {eta:.0f}s", end='')
                    last_count = count

                if count >= expected_count:
                    print()  # New line
                    elapsed = time.time() - start_time
                    log_info(f"AI analysis complete in {elapsed:.1f}s!")
                    log_info(f"Analyzed: {count}/{expected_count} properties")
                    return True

                time.sleep(5)  # Poll every 5 seconds (AI is slower)
            else:
                time.sleep(5)

        except Exception as e:
            log_error(f"AI monitoring error: {str(e)}")
            time.sleep(5)

        # Timeout after 30 minutes (AI is much slower)
        if time.time() - start_time > 1800:
            print()
            log_error("AI processing timeout (30 minutes)")
            log_info(f"Processed {last_count}/{expected_count} properties before timeout")
            return False

def verify_ai_results(job_id):
    """Verify AI analysis results"""
    log_section("7. VERIFYING AI ANALYSIS RESULTS")

    try:
        response = requests.get(f"{API_BASE}/results/{job_id}", timeout=30)

        if response.status_code != 200:
            log_error(f"Failed to get results: {response.status_code}")
            return False

        data = response.json()
        results = data.get('results', [])

        log_info(f"Retrieved {len(results)} property results")

        # Analyze AI results
        issues = []
        stats = {
            'total': len(results),
            'has_ai_data': 0,
            'has_satellite': 0,
            'has_street': 0,
            'has_road_condition': 0,
            'has_power_lines': 0,
            'ai_errors': 0,
            'unknown_risk': 0
        }

        for idx, result in enumerate(results, 1):
            address = result.get('address', {}).get('full_address', 'Unknown')
            ai = result.get('ai_analysis')

            if ai:
                stats['has_ai_data'] += 1

                # Check imagery
                imagery = ai.get('imagery', {})
                if imagery.get('satellite', {}).get('url'):
                    stats['has_satellite'] += 1
                else:
                    issues.append(f"Property {idx} ({address}): No satellite image")

                if imagery.get('street', {}).get('url'):
                    stats['has_street'] += 1
                else:
                    issues.append(f"Property {idx} ({address}): No street view image")

                # Check road condition
                road = ai.get('road_condition', {})
                if road and road.get('type'):
                    stats['has_road_condition'] += 1
                    if road.get('type') == 'UNKNOWN':
                        stats['unknown_risk'] += 1
                else:
                    issues.append(f"Property {idx} ({address}): No road condition data")

                # Check power lines
                power = ai.get('power_lines', {})
                if power and 'visible' in power:
                    stats['has_power_lines'] += 1

                # Check for errors
                if ai.get('error'):
                    stats['ai_errors'] += 1
                    issues.append(f"Property {idx} ({address}): AI error - {ai.get('error')}")

                # Check processing time
                proc_time = ai.get('processing_time_seconds')
                if proc_time is None:
                    issues.append(f"Property {idx} ({address}): No processing time recorded")
            else:
                issues.append(f"Property {idx} ({address}): No AI analysis data")

        # Print statistics
        log_info(f"Properties with AI data: {stats['has_ai_data']}/{stats['total']}")
        log_info(f"Properties with satellite images: {stats['has_satellite']}/{stats['total']}")
        log_info(f"Properties with street images: {stats['has_street']}/{stats['total']}")
        log_info(f"Properties with road condition: {stats['has_road_condition']}/{stats['total']}")
        log_info(f"Properties with power line data: {stats['has_power_lines']}/{stats['total']}")

        if stats['ai_errors'] > 0:
            log_warning(f"Properties with AI errors: {stats['ai_errors']}")

        if stats['unknown_risk'] > 0:
            log_warning(f"Properties with UNKNOWN road condition: {stats['unknown_risk']}")

        # Print issues
        if issues:
            log_warning(f"Found {len(issues)} issues:")
            for issue in issues[:15]:  # Show first 15
                print(f"    - {issue}")
            if len(issues) > 15:
                print(f"    ... and {len(issues) - 15} more")
        else:
            log_info("All AI analysis completed successfully!")

        return len(issues) == 0

    except Exception as e:
        log_error(f"AI verification error: {str(e)}")
        return False

def print_summary(job_id):
    """Print final summary"""
    log_section("8. FINAL SUMMARY")

    try:
        # Get results summary
        response = requests.get(f"{API_BASE}/results/{job_id}/summary", timeout=30)
        if response.status_code == 200:
            data = response.json()
            log_info(f"Total properties: {data.get('total_properties')}")

            risk_dist = data.get('risk_distribution', {})
            log_info(f"Risk distribution:")
            print(f"    - Low risk: {risk_dist.get('low', 0)}")
            print(f"    - Medium risk: {risk_dist.get('medium', 0)}")
            print(f"    - High risk: {risk_dist.get('high', 0)}")

            risk_factors = data.get('risk_factors', {})
            if risk_factors:
                log_info(f"Risk factors detected:")
                print(f"    - Wetlands: {risk_factors.get('wetlands', 0)}")
                print(f"    - High flood zone: {risk_factors.get('high_flood_zone', 0)}")
                print(f"    - Landlocked: {risk_factors.get('landlocked', 0)}")
                print(f"    - Protected land: {risk_factors.get('protected_land', 0)}")

        log_info(f"\nYou can view full results at:")
        print(f"    http://localhost:3000/results/{job_id}")

    except Exception as e:
        log_warning(f"Could not generate summary: {str(e)}")

def main():
    """Main test flow"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║                COMPLETE CSV PROCESSING FLOW TEST                      ║")
    print("║         Testing: Upload → GIS Analysis → AI Analysis → Export        ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")

    # Step 1: Health check
    if not test_server_health():
        return False

    # Step 2: Upload CSV
    job_id = upload_csv()
    if not job_id:
        return False

    # Step 3: Monitor GIS processing
    if not monitor_processing(job_id, 20):  # 20 properties in CSV
        return False

    # Step 4: Verify GIS results
    gis_ok = verify_gis_results(job_id)

    # Step 5: Trigger AI analysis
    if not trigger_ai_analysis(job_id):
        return False

    # Step 6: Monitor AI processing
    if not monitor_ai_processing(job_id, 20):
        log_warning("AI processing incomplete or timed out")

    # Step 7: Verify AI results
    ai_ok = verify_ai_results(job_id)

    # Step 8: Print summary
    print_summary(job_id)

    # Final result
    log_section("TEST COMPLETE")

    if gis_ok and ai_ok:
        log_info("✅ ALL TESTS PASSED! All properties processed successfully.")
        return True
    else:
        log_warning("⚠️ TESTS COMPLETED WITH WARNINGS - Check issues above")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
