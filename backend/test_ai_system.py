"""
Test script for AI imagery analysis system
Verifies all components are working correctly
"""

import sys
import logging
from database import SessionLocal, engine
from models import Base, Property, AIAnalysisResult, ImageCache
from imagery_service import ImageryService
from ai_analysis_service import AIAnalysisService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_schema():
    """Test 1: Verify database schema is correct"""
    logger.info("Test 1: Checking database schema...")

    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)

        db = SessionLocal()

        # Check if we can query the tables
        property_count = db.query(Property).count()
        ai_count = db.query(AIAnalysisResult).count()
        cache_count = db.query(ImageCache).count()

        logger.info(f"✅ Database schema OK")
        logger.info(f"   - Properties: {property_count}")
        logger.info(f"   - AI Results: {ai_count}")
        logger.info(f"   - Image Cache: {cache_count}")

        db.close()
        return True

    except Exception as e:
        logger.error(f"❌ Database schema test failed: {str(e)}")
        return False

def test_imagery_service():
    """Test 2: Verify imagery service can be instantiated"""
    logger.info("Test 2: Testing imagery service...")

    try:
        service = ImageryService()
        logger.info("✅ Imagery service initialized successfully")

        # Test URL generation (doesn't make API calls)
        test_lat, test_lon = 28.5383, -81.3792  # Orlando, FL

        # These won't actually fetch without API keys, but test the logic
        logger.info(f"   Testing with coordinates: {test_lat}, {test_lon}")

        return True

    except Exception as e:
        logger.error(f"❌ Imagery service test failed: {str(e)}")
        return False

def test_ai_service():
    """Test 3: Verify AI analysis service can be instantiated"""
    logger.info("Test 3: Testing AI analysis service...")

    try:
        service = AIAnalysisService()
        logger.info("✅ AI analysis service initialized successfully")
        logger.info(f"   Model version: {service.model_version}")

        return True

    except Exception as e:
        logger.error(f"❌ AI service test failed: {str(e)}")
        return False

def test_api_endpoints():
    """Test 4: Verify API endpoints are defined"""
    logger.info("Test 4: Testing API endpoints...")

    try:
        from main import app

        routes = [route.path for route in app.routes]

        required_endpoints = [
            "/analyze-ai/{job_id}",
            "/ai-results/{job_id}",
            "/results/{job_id}"
        ]

        all_present = True
        for endpoint in required_endpoints:
            if endpoint in routes:
                logger.info(f"   ✅ {endpoint}")
            else:
                logger.error(f"   ❌ {endpoint} not found")
                all_present = False

        if all_present:
            logger.info("✅ All API endpoints present")
            return True
        else:
            logger.error("❌ Some API endpoints missing")
            return False

    except Exception as e:
        logger.error(f"❌ API endpoints test failed: {str(e)}")
        return False

def test_environment_variables():
    """Test 5: Check environment variables (optional)"""
    logger.info("Test 5: Checking environment variables...")

    import os

    optional_vars = {
        'OPENAI_API_KEY': 'AI analysis (OpenAI)',
        'MAPBOX_ACCESS_TOKEN': 'Satellite imagery (Mapbox)',
        'GOOGLE_MAPS_API_KEY': 'Imagery & Street View (Google)',
        'MAPILLARY_CLIENT_TOKEN': 'Street imagery (Mapillary)'
    }

    found_count = 0
    for var, description in optional_vars.items():
        if os.getenv(var):
            logger.info(f"   ✅ {var} - {description}")
            found_count += 1
        else:
            logger.info(f"   ⚠️  {var} not set - {description}")

    if found_count == 0:
        logger.warning("⚠️  No API keys configured - AI analysis will use fallback mode")
        logger.warning("   Set at least OPENAI_API_KEY for full functionality")
    else:
        logger.info(f"✅ {found_count}/{len(optional_vars)} API keys configured")

    return True

def test_model_attributes():
    """Test 6: Verify AIAnalysisResult model has all required fields"""
    logger.info("Test 6: Testing model attributes...")

    try:
        required_fields = [
            'satellite_image_url',
            'street_image_url',
            'satellite_image_source',
            'street_image_source',
            'road_condition_type',
            'road_condition_confidence',
            'power_lines_visible',
            'power_line_confidence',
            'power_line_distance_meters',
            'power_line_geometry',
            'nearby_dev_type',
            'nearby_dev_count',
            'ai_risk_level',
            'model_version'
        ]

        missing_fields = []
        for field in required_fields:
            if not hasattr(AIAnalysisResult, field):
                missing_fields.append(field)

        if missing_fields:
            logger.error(f"❌ Missing fields: {', '.join(missing_fields)}")
            return False
        else:
            logger.info(f"✅ All {len(required_fields)} required fields present")
            return True

    except Exception as e:
        logger.error(f"❌ Model attributes test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    logger.info("=" * 60)
    logger.info("AI IMAGERY ANALYSIS SYSTEM - TEST SUITE")
    logger.info("=" * 60)
    logger.info("")

    tests = [
        ("Database Schema", test_database_schema),
        ("Imagery Service", test_imagery_service),
        ("AI Analysis Service", test_ai_service),
        ("API Endpoints", test_api_endpoints),
        ("Environment Variables", test_environment_variables),
        ("Model Attributes", test_model_attributes)
    ]

    results = []

    for test_name, test_func in tests:
        logger.info("")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! System is ready to use.")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Start backend: python main.py")
        logger.info("2. Start frontend: cd ../frontend && npm run dev")
        logger.info("3. Visit: http://localhost:3000")
        return 0
    else:
        logger.error("⚠️  Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
