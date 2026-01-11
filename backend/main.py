from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, engine, SessionLocal
from models import (
    Base, Upload, Property, RiskResult, GeocodingCache,
    PropertyOwnerInfo, AIAnalysisResult, ImageCache, APIRateLimit
)
from geocoding_service import GeocodingService
from gis_service import GISRiskService
from legal_description_service import LegalDescriptionService
from water_utility_service import WaterUtilityService
from imagery_service import ImageryService
from ai_analysis_service import AIAnalysisService
from skip_trace_service import SkipTraceService
import logging
import csv
import io
import uuid
import json
from datetime import datetime
from typing import Optional, List
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Property Analysis API",
    description="API for property risk analysis and GIS data processing",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
geocoding_service = GeocodingService()
gis_service = GISRiskService()
legal_service = LegalDescriptionService()
water_utility_service = WaterUtilityService()
imagery_service = ImageryService()
ai_analysis_service = AIAnalysisService()
skip_trace_service = SkipTraceService()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Property Analysis API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(func.now())
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/process-csv")
async def process_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Upload and process a CSV file with property addresses

    Expected CSV columns:
    - Street Address (required)
    - City (required)
    - State (required)
    - Postal Code (required)
    - Contact ID (optional)
    - First Name (optional)
    - Last Name (optional)
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        # Read CSV file
        contents = await file.read()
        csv_data = csv.DictReader(io.StringIO(contents.decode('utf-8')))

        # Convert to list to get row count
        rows = list(csv_data)
        total_rows = len(rows)

        if total_rows == 0:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        if total_rows > 20000:
            raise HTTPException(status_code=400, detail="Maximum 20,000 properties per upload")

        # Validate required columns exist
        if rows:
            sample_row = rows[0]

            # Check for address column
            has_street = get_csv_field(sample_row,
                'Street Address', 'Street address', 'street_address',
                'Property Address', 'Property address', 'property_address',
                'Address', 'address', 'STREET', 'PROPERTY ADDRESS'
            )

            # Check for city column
            has_city = get_csv_field(sample_row,
                'City', 'city', 'CITY',
                'Property City', 'Property city', 'property_city',
                'PROPERTY CITY'
            )

            # Check for state column
            has_state = get_csv_field(sample_row,
                'State', 'state', 'STATE',
                'Property State', 'Property state', 'property_state',
                'PROPERTY STATE', 'St', 'ST'
            )

            # Check for zip column
            has_zip = get_csv_field(sample_row,
                'Postal Code', 'postal_code', 'POSTAL CODE',
                'Property Zip', 'Property zip', 'property_zip',
                'PROPERTY ZIP', 'Zip Code', 'zip_code', 'Zip', 'zip', 'ZIP'
            )

            missing_columns = []
            if not has_street:
                missing_columns.append("Street Address (or Property Address)")
            if not has_city:
                missing_columns.append("City (or Property City)")
            if not has_state:
                missing_columns.append("State (or Property State)")
            if not has_zip:
                missing_columns.append("ZIP Code (or Property Zip)")

            if missing_columns:
                error_msg = f"Missing required columns: {', '.join(missing_columns)}. Available columns: {', '.join(sample_row.keys())}"
                logger.error(f"CSV validation failed: {error_msg}")
                raise HTTPException(status_code=400, detail=error_msg)

        # Create upload record
        upload_id = uuid.uuid4()
        upload = Upload(
            id=upload_id,
            filename=file.filename,
            total_rows=total_rows,
            status="processing"
        )
        db.add(upload)
        db.commit()

        # Process properties in background
        if background_tasks:
            background_tasks.add_task(process_properties, upload_id, rows, db)
        else:
            # Process synchronously for testing
            process_properties_sync(upload_id, rows, db)

        return {
            "job_id": str(upload_id),
            "status": "processing",
            "total_rows": total_rows,
            "message": "Upload successful. Processing started."
        }

    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def get_csv_field(row: dict, *field_names) -> Optional[str]:
    """
    Flexibly extract field from CSV row with multiple possible column names.
    Case-insensitive, strips whitespace.
    """
    for field_name in field_names:
        # Try exact match first
        if field_name in row and row[field_name]:
            return str(row[field_name]).strip()

        # Try case-insensitive match
        for key, value in row.items():
            if key.strip().lower() == field_name.lower() and value:
                return str(value).strip()

    return None


def process_single_property(row: dict, idx: int, upload_id: uuid.UUID):
    """Process a single property (used in batch processing)"""
    from database import SessionLocal
    db = SessionLocal()
    property_start_time = time.time()

    try:
        logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"Processing Property #{idx + 1}")
        logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # Extract address components with flexible column matching
        street = get_csv_field(row,
            'Street Address', 'Street address', 'street_address',
            'Property Address', 'Property address', 'property_address',
            'Address', 'address', 'STREET', 'PROPERTY ADDRESS'
        )

        city = get_csv_field(row,
            'City', 'city', 'CITY',
            'Property City', 'Property city', 'property_city',
            'PROPERTY CITY'
        )

        state = get_csv_field(row,
            'State', 'state', 'STATE',
            'Property State', 'Property state', 'property_state',
            'PROPERTY STATE', 'St', 'ST'
        )

        postal_code = get_csv_field(row,
            'Postal Code', 'postal_code', 'POSTAL CODE',
            'Property Zip', 'Property zip', 'property_zip',
            'PROPERTY ZIP', 'Zip Code', 'zip_code', 'Zip', 'zip', 'ZIP'
        )

        logger.info(f"📍 Address: {street}, {city}, {state} {postal_code}")

        if not all([street, city, state, postal_code]):
            logger.error(f"❌ Row {idx + 1}: Missing required address fields - Street: {street}, City: {city}, State: {state}, ZIP: {postal_code}")
            return False

        # Geocode address with fallback
        logger.info(f"🌍 Step 1/3: Geocoding address...")
        geocode_result = geocoding_service.geocode_address(street, city, state, postal_code)

        if not geocode_result:
            logger.error(f"❌ Row {idx + 1}: All geocoding methods failed for {street}, {city}, {state} {postal_code}")
            return False

        # Log geocoding source for monitoring
        logger.info(f"✅ Geocoded via {geocode_result.get('source', 'unknown')} (accuracy: {geocode_result.get('accuracy', 'unknown')})")
        logger.info(f"   Coordinates: ({geocode_result['latitude']}, {geocode_result['longitude']})")

        # Extract optional fields with flexible matching
        contact_id = get_csv_field(row, 'Contact ID', 'contact_id', 'Contact Id', 'ContactID')
        first_name = get_csv_field(row, 'First Name', 'first_name', 'FirstName', 'First')
        last_name = get_csv_field(row, 'Last Name', 'last_name', 'LastName', 'Last')
        full_name_from_csv = get_csv_field(row, 'Name', 'name', 'Full Name', 'full_name')

        # Create full name
        if full_name_from_csv:
            full_name = full_name_from_csv
        elif first_name or last_name:
            full_name = f"{first_name or ''} {last_name or ''}".strip()
        else:
            full_name = None

        # Create property record
        property_data = {
            'upload_id': upload_id,
            'contact_id': contact_id,
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
            'street_address': street,
            'city': geocode_result['city'],
            'state': geocode_result['state'],
            'postal_code': geocode_result['zip'],
            'county': geocode_result.get('county'),
            'full_address': geocode_result['full_address'],
            'latitude': geocode_result['latitude'],
            'longitude': geocode_result['longitude'],
            'geocode_accuracy': geocode_result.get('accuracy')
        }

        # Store entire original CSV row for export preservation
        property_data['original_data'] = dict(row)

        property_record = Property(**property_data)

        db.add(property_record)
        db.flush()  # Get property ID
        logger.info(f"✅ Property record created (ID: {property_record.id})")

        # Perform GIS risk analysis with proper parameters
        logger.info(f"🗺️  Step 2/3: Performing GIS risk analysis...")
        risk_analysis = gis_service.analyze_property(
            latitude=geocode_result['latitude'],
            longitude=geocode_result['longitude'],
            address=street,
            city=city,
            state=state
        )
        logger.info(f"✅ GIS analysis complete - Overall Risk: {risk_analysis['overall_risk']}")

        # Skip water utility checks (not needed)

        # Create risk result record
        risk_result = RiskResult(
            property_id=property_record.id,
            upload_id=upload_id,
            wetlands_status=risk_analysis['wetlands']['status'],
            wetlands_source=risk_analysis['wetlands']['source'],
            flood_zone=risk_analysis['flood_zone']['zone'],
            flood_severity=risk_analysis['flood_zone']['severity'],
            flood_source=risk_analysis['flood_zone']['source'],
            slope_percentage=risk_analysis['slope']['percentage'],
            slope_severity=risk_analysis['slope']['severity'],
            slope_source=risk_analysis['slope']['source'],
            road_access=risk_analysis['road_access']['has_access'],
            road_distance_meters=risk_analysis['road_access']['distance_meters'],
            road_source=risk_analysis['road_access']['source'],
            landlocked=risk_analysis['landlocked'],
            protected_land=risk_analysis['protected_land']['is_protected'],
            protected_land_type=risk_analysis['protected_land'].get('type'),
            protected_land_source=risk_analysis['protected_land']['source'],
            water_available=None,  # Removed
            sewer_available=None,  # Removed
            water_provider=None,  # Removed
            sewer_provider=None,  # Removed
            utility_source=None,  # Removed
            overall_risk=risk_analysis['overall_risk'],
            processing_time_seconds=risk_analysis['processing_time_seconds'],
            error_message=risk_analysis.get('error')
        )

        db.add(risk_result)
        db.commit()

        processing_time = time.time() - property_start_time
        logger.info(f"✅ Property #{idx + 1} processed successfully in {processing_time:.2f}s")
        logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        return True

    except Exception as e:
        logger.error(f"❌ Error processing row {idx + 1}: {str(e)}", exc_info=True)
        db.rollback()
        return False
    finally:
        db.close()


def process_properties_sync(upload_id: uuid.UUID, rows: List[dict], db: Session):
    """Batch property processing with concurrent execution"""
    from database import SessionLocal
    db = SessionLocal()

    try:
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            return

        # Process properties in batches using ThreadPoolExecutor
        max_workers = 10  # Process 10 properties concurrently (PostgreSQL can handle this easily)
        completed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_idx = {
                executor.submit(process_single_property, row, idx, upload_id): idx
                for idx, row in enumerate(rows)
            }

            # Process completed tasks
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    success = future.result()
                    if success:
                        completed += 1

                        # Update progress
                        upload.processed_rows = completed
                        db.commit()

                except Exception as e:
                    logger.error(f"Error processing property {idx + 1}: {str(e)}")

        # Mark upload as completed
        upload.status = "completed"
        upload.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Upload {upload_id} completed successfully - {completed}/{len(rows)} properties")

    except Exception as e:
        logger.error(f"Error in process_properties: {str(e)}")
        upload.status = "failed"
        upload.error_message = str(e)
        db.commit()
    finally:
        db.close()


def process_properties(upload_id: uuid.UUID, rows: List[dict], db: Session):
    """Background task to process properties"""
    process_properties_sync(upload_id, rows, db)


@app.get("/status/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get processing status for a job"""
    try:
        upload_id = uuid.UUID(job_id)
        upload = db.query(Upload).filter(Upload.id == upload_id).first()

        if not upload:
            raise HTTPException(status_code=404, detail="Job not found")

        progress_percentage = 0
        if upload.total_rows > 0:
            progress_percentage = round((upload.processed_rows / upload.total_rows) * 100, 2)

        return {
            "job_id": str(upload.id),
            "filename": upload.filename,
            "status": upload.status,
            "total_rows": upload.total_rows,
            "processed_rows": upload.processed_rows,
            "progress_percentage": progress_percentage,
            "uploaded_at": upload.uploaded_at.isoformat() if upload.uploaded_at else None,
            "completed_at": upload.completed_at.isoformat() if upload.completed_at else None,
            "error_message": upload.error_message
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")


@app.get("/results/{job_id}")
async def get_results(
    job_id: str,
    county: Optional[str] = None,
    postal_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get analysis results for a job with optional filtering"""
    try:
        upload_id = uuid.UUID(job_id)
        upload = db.query(Upload).filter(Upload.id == upload_id).first()

        if not upload:
            raise HTTPException(status_code=404, detail="Job not found")

        # Build query with filters, LEFT JOIN for AI results and owner info (may not exist yet)
        query = db.query(Property, RiskResult, AIAnalysisResult, PropertyOwnerInfo).join(
            RiskResult, Property.id == RiskResult.property_id
        ).outerjoin(
            AIAnalysisResult, Property.id == AIAnalysisResult.property_id
        ).outerjoin(
            PropertyOwnerInfo, Property.id == PropertyOwnerInfo.property_id
        ).filter(Property.upload_id == upload_id)

        # Apply filters
        if county:
            query = query.filter(Property.county == county)
        if postal_code:
            query = query.filter(Property.postal_code == postal_code)

        results = query.all()

        # Format results
        formatted_results = []
        for prop, risk, ai, owner in results:
            formatted_results.append({
                "contact_id": prop.contact_id or "",
                "name": prop.full_name or "",
                "address": {
                    "street": prop.street_address,
                    "city": prop.city,
                    "state": prop.state,
                    "zip": prop.postal_code,
                    "county": prop.county,
                    "full_address": prop.full_address
                },
                "coordinates": {
                    "latitude": prop.latitude,
                    "longitude": prop.longitude
                } if prop.latitude and prop.longitude else None,
                "property_details": {
                    "legal_description": prop.legal_description,
                    "lot_size_acres": prop.lot_size_acres,
                    "lot_size_sqft": prop.lot_size_sqft
                },
                "phase1_risk": {
                    "wetlands": {
                        "status": risk.wetlands_status,
                        "source": risk.wetlands_source
                    },
                    "flood_zone": {
                        "zone": risk.flood_zone,
                        "severity": risk.flood_severity,
                        "source": risk.flood_source
                    },
                    "slope": {
                        "percentage": risk.slope_percentage,
                        "severity": risk.slope_severity,
                        "source": risk.slope_source
                    },
                    "road_access": {
                        "has_access": risk.road_access,
                        "distance_meters": risk.road_distance_meters,
                        "source": risk.road_source
                    },
                    "landlocked": risk.landlocked,
                    "protected_land": {
                        "is_protected": risk.protected_land,
                        "type": risk.protected_land_type,
                        "source": risk.protected_land_source
                    },
                    "water_utility": {
                        "water_available": risk.water_available,
                        "sewer_available": risk.sewer_available,
                        "water_provider": risk.water_provider,
                        "sewer_provider": risk.sewer_provider,
                        "source": risk.utility_source
                    },
                    "overall_risk": risk.overall_risk,
                    "processing_time_seconds": risk.processing_time_seconds,
                    "error": risk.error_message
                },
                "ai_analysis": {
                    "imagery": {
                        "satellite": {
                            "url": ai.satellite_image_url,
                            "source": ai.satellite_image_source
                        },
                        "street": {
                            "url": ai.street_image_url,
                            "source": ai.street_image_source
                        }
                    },
                    "road_condition": {
                        "type": ai.road_condition_type,
                        "confidence": ai.road_condition_confidence
                    },
                    "power_lines": {
                        "visible": ai.power_lines_visible,
                        "confidence": ai.power_line_confidence,
                        "distance_meters": ai.power_line_distance_meters,
                        "geometry": ai.power_line_geometry
                    },
                    "nearby_development": {
                        "type": ai.nearby_dev_type,
                        "count": ai.nearby_dev_count,
                        "confidence": ai.nearby_dev_confidence,
                        "details": getattr(ai, 'nearby_dev_details', None)
                    },
                    "nearby_structures": {
                        "structures_detected": getattr(ai, 'structures_detected', False),
                        "count": getattr(ai, 'structures_count', None),
                        "types": json.loads(getattr(ai, 'structures_types', '[]') or '[]'),
                        "density": getattr(ai, 'structures_density', None),
                        "confidence": getattr(ai, 'structures_confidence', None),
                        "details": getattr(ai, 'structures_details', None)
                    },
                    "overall_risk": {
                        "level": ai.ai_risk_level,
                        "confidence": ai.ai_risk_confidence
                    },
                    "processing_time_seconds": ai.processing_time_seconds,
                    "model_version": ai.model_version,
                    "analyzed_at": ai.analyzed_at.isoformat() if ai.analyzed_at else None,
                    "error": ai.error_message
                } if ai else None,
                "owner_info": {
                    "status": owner.owner_info_status,
                    "found": owner.owner_info_status == 'complete',
                    "name": {
                        "first": owner.owner_first_name,
                        "middle": owner.owner_middle_name,
                        "last": owner.owner_last_name,
                        "full": owner.owner_full_name
                    },
                    "contact": {
                        "phone_primary": owner.phone_primary,
                        "phone_mobile": owner.phone_mobile,
                        "phone_secondary": owner.phone_secondary,
                        "email_primary": owner.email_primary,
                        "email_secondary": owner.email_secondary
                    },
                    "mailing_address": {
                        "street": owner.mailing_street,
                        "city": owner.mailing_city,
                        "state": owner.mailing_state,
                        "zip": owner.mailing_zip,
                        "full": owner.mailing_full_address
                    },
                    "details": {
                        "owner_type": owner.owner_type,
                        "owner_occupied": owner.owner_occupied
                    },
                    "metadata": {
                        "source": owner.source,
                        "confidence": owner.confidence_score,
                        "retrieved_at": owner.retrieved_at.isoformat() if owner.retrieved_at else None,
                        "processing_time_seconds": owner.processing_time_seconds
                    }
                } if owner else None
            })

        return {
            "job_id": str(upload.id),
            "status": upload.status,
            "filename": upload.filename,
            "total_properties": upload.total_rows,
            "processed_properties": upload.processed_rows,
            "completed_at": upload.completed_at.isoformat() if upload.completed_at else None,
            "results": formatted_results
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")


@app.get("/results/{job_id}/summary")
async def get_results_summary(job_id: str, db: Session = Depends(get_db)):
    """Get summary statistics for a job"""
    try:
        upload_id = uuid.UUID(job_id)
        upload = db.query(Upload).filter(Upload.id == upload_id).first()

        if not upload:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get risk distribution
        risk_counts = db.query(
            RiskResult.overall_risk,
            func.count(RiskResult.id)
        ).filter(RiskResult.upload_id == upload_id).group_by(RiskResult.overall_risk).all()

        risk_distribution = {"low": 0, "medium": 0, "high": 0}
        total_properties = 0

        for risk_level, count in risk_counts:
            total_properties += count
            if risk_level == "LOW":
                risk_distribution["low"] = count
            elif risk_level == "MEDIUM":
                risk_distribution["medium"] = count
            elif risk_level == "HIGH":
                risk_distribution["high"] = count

        # Calculate percentages
        percentages = {
            "low_risk": round((risk_distribution["low"] / total_properties * 100), 1) if total_properties > 0 else 0,
            "medium_risk": round((risk_distribution["medium"] / total_properties * 100), 1) if total_properties > 0 else 0,
            "high_risk": round((risk_distribution["high"] / total_properties * 100), 1) if total_properties > 0 else 0
        }

        # Get risk factors
        risk_factors = {
            "wetlands": db.query(func.count(RiskResult.id)).filter(
                RiskResult.upload_id == upload_id,
                RiskResult.wetlands_status == True
            ).scalar() or 0,
            "high_flood_zone": db.query(func.count(RiskResult.id)).filter(
                RiskResult.upload_id == upload_id,
                RiskResult.flood_severity == "HIGH"
            ).scalar() or 0,
            "landlocked": db.query(func.count(RiskResult.id)).filter(
                RiskResult.upload_id == upload_id,
                RiskResult.landlocked == True
            ).scalar() or 0,
            "protected_land": db.query(func.count(RiskResult.id)).filter(
                RiskResult.upload_id == upload_id,
                RiskResult.protected_land == True
            ).scalar() or 0
        }

        return {
            "job_id": str(upload.id),
            "status": upload.status,
            "total_properties": total_properties,
            "risk_distribution": risk_distribution,
            "percentages": percentages,
            "risk_factors": risk_factors
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")


@app.get("/results/{job_id}/export-status")
async def get_export_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get the status of what data is available for export.
    Returns counts of properties with/without AI analysis and owner info.
    """
    try:
        upload_id = uuid.UUID(job_id)
        upload = db.query(Upload).filter(Upload.id == upload_id).first()

        if not upload:
            raise HTTPException(status_code=404, detail="Job not found")

        # Count total properties
        total_properties = db.query(func.count(Property.id)).filter(
            Property.upload_id == upload_id
        ).scalar() or 0

        # Count properties with AI analysis
        ai_analyzed_count = db.query(func.count(AIAnalysisResult.id)).filter(
            AIAnalysisResult.upload_id == upload_id,
            AIAnalysisResult.error_message == None
        ).scalar() or 0

        # Count properties with owner info
        owner_info_count = db.query(func.count(PropertyOwnerInfo.id)).filter(
            PropertyOwnerInfo.upload_id == upload_id,
            PropertyOwnerInfo.owner_info_status == 'complete'
        ).scalar() or 0

        # Get original CSV columns from first property
        first_property = db.query(Property).filter(
            Property.upload_id == upload_id
        ).first()

        original_columns = []
        if first_property and first_property.original_data:
            original_columns = list(first_property.original_data.keys())

        return {
            "job_id": job_id,
            "total_properties": total_properties,
            "ai_analysis": {
                "count": ai_analyzed_count,
                "available": ai_analyzed_count > 0,
                "complete": ai_analyzed_count == total_properties
            },
            "owner_info": {
                "count": owner_info_count,
                "available": owner_info_count > 0,
                "complete": owner_info_count == total_properties
            },
            "original_columns": original_columns
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")


@app.get("/results/{job_id}/export")
async def export_results_csv(job_id: str, db: Session = Depends(get_db)):
    """
    Export results as CSV with original data + all analysis.
    Preserves all original CSV columns and adds:
    - GIS risk analysis columns
    - AI analysis columns (if available)
    - Owner/skip trace columns (if available)
    """
    try:
        upload_id = uuid.UUID(job_id)
        upload = db.query(Upload).filter(Upload.id == upload_id).first()

        if not upload:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get all properties with their results (LEFT JOIN for optional data)
        results = db.query(Property, RiskResult, AIAnalysisResult, PropertyOwnerInfo).join(
            RiskResult, Property.id == RiskResult.property_id
        ).outerjoin(
            AIAnalysisResult, Property.id == AIAnalysisResult.property_id
        ).outerjoin(
            PropertyOwnerInfo, Property.id == PropertyOwnerInfo.property_id
        ).filter(Property.upload_id == upload_id).all()

        if not results:
            raise HTTPException(status_code=404, detail="No results found")

        # Create CSV in memory
        output = io.StringIO()

        # Get all unique column names from original data (preserve order from first row)
        original_columns = []
        for prop, _, _, _ in results:
            if prop.original_data:
                original_columns = list(prop.original_data.keys())
                break

        # Check if we have any AI analysis or owner info
        has_ai_analysis = any(ai is not None for _, _, ai, _ in results)
        has_owner_info = any(owner is not None for _, _, _, owner in results)

        # Define GIS analysis columns (always present)
        gis_columns = [
            'Latitude',
            'Longitude',
            'County',
            'Wetlands Status',
            'Flood Zone',
            'Flood Severity',
            'Slope Percentage',
            'Slope Severity',
            'Road Access',
            'Road Distance (m)',
            'Landlocked',
            'Protected Land',
            'Protected Land Type',
            'Overall Risk'
        ]

        # Define AI analysis columns (if available)
        ai_columns = []
        if has_ai_analysis:
            ai_columns = [
                'AI Road Condition',
                'AI Road Confidence',
                'AI Power Lines Visible',
                'AI Power Lines Distance (m)',
                'AI Development Type',
                'AI Structures Count',
                'AI Structures Types',
                'AI Risk Level',
                'Satellite Image URL',
                'Street View URL'
            ]

        # Define owner info columns (if available)
        owner_columns = []
        if has_owner_info:
            owner_columns = [
                'Owner Name',
                'Owner Type',
                'Owner Occupied',
                'Phone Primary',
                'Phone Mobile',
                'Phone Secondary',
                'Phone Count',
                'Email Primary',
                'Email Secondary',
                'Email Count',
                'Mailing Street',
                'Mailing City',
                'Mailing State',
                'Mailing Zip',
                'Is Deceased',
                'Is Litigator',
                'Has DNC',
                'Has TCPA',
                'Has Bankruptcy'
            ]

        # Combine: Original columns + GIS + AI + Owner columns
        fieldnames = original_columns + gis_columns + ai_columns + owner_columns

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Write data rows
        for prop, risk, ai, owner in results:
            row_data = {}

            # Add original CSV data
            if prop.original_data:
                row_data.update(prop.original_data)

            # Add GIS analysis data
            row_data.update({
                'Latitude': prop.latitude,
                'Longitude': prop.longitude,
                'County': prop.county,
                'Wetlands Status': 'Yes' if risk.wetlands_status else 'No',
                'Flood Zone': risk.flood_zone,
                'Flood Severity': risk.flood_severity,
                'Slope Percentage': risk.slope_percentage,
                'Slope Severity': risk.slope_severity,
                'Road Access': 'Yes' if risk.road_access else 'No',
                'Road Distance (m)': risk.road_distance_meters,
                'Landlocked': 'Yes' if risk.landlocked else 'No',
                'Protected Land': 'Yes' if risk.protected_land else 'No',
                'Protected Land Type': risk.protected_land_type,
                'Overall Risk': risk.overall_risk
            })

            # Add AI analysis data (if columns exist)
            if has_ai_analysis:
                if ai:
                    row_data.update({
                        'AI Road Condition': ai.road_condition_type,
                        'AI Road Confidence': f"{int(ai.road_condition_confidence * 100)}%" if ai.road_condition_confidence else '',
                        'AI Power Lines Visible': 'Yes' if ai.power_lines_visible else 'No',
                        'AI Power Lines Distance (m)': ai.power_line_distance_meters,
                        'AI Development Type': ai.nearby_dev_type,
                        'AI Structures Count': ai.structures_count,
                        'AI Structures Types': ai.structures_types,
                        'AI Risk Level': ai.ai_risk_level,
                        'Satellite Image URL': ai.satellite_image_url,
                        'Street View URL': ai.street_image_url
                    })
                else:
                    # Empty values for properties without AI analysis
                    for col in ai_columns:
                        row_data[col] = ''

            # Add owner info data (if columns exist)
            if has_owner_info:
                if owner and owner.owner_info_status == 'complete':
                    row_data.update({
                        'Owner Name': owner.owner_full_name or owner.owner_name,
                        'Owner Type': owner.owner_type,
                        'Owner Occupied': 'Yes' if owner.owner_occupied else 'No' if owner.owner_occupied is False else '',
                        'Phone Primary': owner.phone_primary,
                        'Phone Mobile': owner.phone_mobile,
                        'Phone Secondary': owner.phone_secondary,
                        'Phone Count': owner.phone_count,
                        'Email Primary': owner.email_primary,
                        'Email Secondary': owner.email_secondary,
                        'Email Count': owner.email_count,
                        'Mailing Street': owner.mailing_street,
                        'Mailing City': owner.mailing_city,
                        'Mailing State': owner.mailing_state,
                        'Mailing Zip': owner.mailing_zip,
                        'Is Deceased': 'Yes' if owner.is_deceased else 'No',
                        'Is Litigator': 'Yes' if owner.is_litigator else 'No',
                        'Has DNC': 'Yes' if owner.has_dnc else 'No',
                        'Has TCPA': 'Yes' if owner.has_tcpa else 'No',
                        'Has Bankruptcy': 'Yes' if owner.has_bankruptcy else 'No'
                    })
                else:
                    # Empty values for properties without owner info
                    for col in owner_columns:
                        row_data[col] = ''

            writer.writerow(row_data)

        # Prepare response
        csv_content = output.getvalue()
        output.close()

        # Return CSV file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=property_analysis_{job_id}.csv"
            }
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")


@app.post("/analyze-ai/{job_id}")
async def trigger_ai_analysis(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger AI analysis for all properties in a job.
    This performs satellite imagery analysis, road condition detection,
    and power line detection.
    """
    try:
        upload_id = uuid.UUID(job_id)
        upload = db.query(Upload).filter(Upload.id == upload_id).first()

        if not upload:
            raise HTTPException(status_code=404, detail="Job not found")

        if upload.status != "completed":
            raise HTTPException(
                status_code=400,
                detail="Cannot run AI analysis. Property processing must be completed first."
            )

        # Count properties for this upload
        property_count = db.query(func.count(Property.id)).filter(
            Property.upload_id == upload_id
        ).scalar()

        # Check if AI analysis already exists
        existing_count = db.query(func.count(AIAnalysisResult.id)).filter(
            AIAnalysisResult.upload_id == upload_id
        ).scalar()

        # Queue background AI processing
        background_tasks.add_task(process_ai_analysis, upload_id)

        return {
            "job_id": str(upload_id),
            "status": "analyzing_ai",
            "total_properties": property_count,
            "existing_ai_results": existing_count,
            "message": "AI analysis started in background"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")


def process_ai_analysis(upload_id: uuid.UUID):
    """Background task to process AI analysis for all properties"""
    from database import SessionLocal
    db = SessionLocal()

    try:
        # Get all properties for this upload
        properties = db.query(Property).filter(
            Property.upload_id == upload_id
        ).all()

        logger.info(f"Starting AI analysis for {len(properties)} properties")

        # Process properties concurrently (limited workers due to AI model constraints)
        max_workers = 3  # Reduced for GPU/API rate limits
        completed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_prop = {
                executor.submit(process_single_property_ai, prop, upload_id): prop
                for prop in properties
            }

            for future in as_completed(future_to_prop):
                prop = future_to_prop[future]
                try:
                    success = future.result()
                    if success:
                        completed += 1
                        logger.info(f"AI analysis completed for property {completed}/{len(properties)}")
                except Exception as e:
                    logger.error(f"Error processing AI for property {prop.id}: {str(e)}")

        logger.info(f"AI analysis completed for upload {upload_id} - {completed}/{len(properties)} properties")

    except Exception as e:
        logger.error(f"Error in AI analysis batch: {str(e)}")
    finally:
        db.close()


def process_single_property_ai(property_obj: Property, upload_id: uuid.UUID):
    """Process AI analysis for a single property"""
    from database import SessionLocal
    db = SessionLocal()
    ai_start_time = time.time()

    try:
        logger.info(f"╔═══════════════════════════════════════════════════════════════╗")
        logger.info(f"║  AI ANALYSIS - Property ID: {property_obj.id}")
        logger.info(f"║  Address: {property_obj.full_address}")
        logger.info(f"╚═══════════════════════════════════════════════════════════════╝")

        # Skip if no coordinates
        if not property_obj.latitude or not property_obj.longitude:
            logger.error(f"❌ Skipping AI analysis for property {property_obj.id} - no coordinates")
            return False

        logger.info(f"📍 Coordinates: ({property_obj.latitude}, {property_obj.longitude})")

        # Check if AI analysis already exists
        existing = db.query(AIAnalysisResult).filter(
            AIAnalysisResult.property_id == property_obj.id
        ).first()

        if existing:
            logger.info(f"⏭️  AI analysis already exists for property {property_obj.id}, skipping")
            return True

        start_time = time.time()

        # Fetch imagery (with base64 for AI) - NOW FETCHES 3 IMAGES
        logger.info(f"📸 Step 1/3: Fetching imagery (1 satellite + 2 street views)...")
        imagery = imagery_service.fetch_imagery(
            property_obj.latitude,
            property_obj.longitude,
            cache_db=db
        )

        satellite_url = imagery['satellite']['url']
        street_url_1 = imagery['street_view_1']['url']
        street_url_2 = imagery['street_view_2']['url']
        satellite_base64 = imagery['satellite']['base64']  # Base64 for AI
        street_base64_1 = imagery['street_view_1']['base64']  # Base64 for AI (angle 1)
        street_base64_2 = imagery['street_view_2']['base64']  # Base64 for AI (angle 2)
        satellite_source = imagery['satellite']['source']
        street_source_1 = imagery['street_view_1']['source']
        street_source_2 = imagery['street_view_2']['source']

        if satellite_url:
            logger.info(f"   ✅ Satellite image: {satellite_source}")
        else:
            logger.warning(f"   ⚠️  No satellite image: {imagery['satellite'].get('error')}")

        if street_url_1:
            logger.info(f"   ✅ Street view 1 (0°): {street_source_1}")
        else:
            logger.warning(f"   ⚠️  No street view 1: {imagery['street_view_1'].get('error')}")

        if street_url_2:
            logger.info(f"   ✅ Street view 2 (180°): {street_source_2}")
        else:
            logger.warning(f"   ⚠️  No street view 2: {imagery['street_view_2'].get('error')}")

        # Perform AI analysis using base64 URLs (NOW PASSES 3 IMAGES)
        logger.info(f"🤖 Step 2/3: Running AI vision analysis with 3 images...")
        ai_result = ai_analysis_service.analyze_property(
            property_obj.latitude,
            property_obj.longitude,
            satellite_base64,  # Pass base64 instead of regular URL
            street_base64_1,   # Street view angle 1
            street_base64_2    # Street view angle 2
        )

        processing_time = time.time() - start_time
        logger.info(f"✅ AI analysis complete in {processing_time:.2f}s")

        # Get existing GIS risk result for comparison
        risk_result = db.query(RiskResult).filter(
            RiskResult.property_id == property_obj.id
        ).first()

        # Check if AI should override GIS road access
        if risk_result and ai_result.get('road_condition'):
            override_check = ai_analysis_service.check_and_determine_road_access_override(
                road_condition=ai_result['road_condition'],
                gis_road_access=risk_result.road_access,
                gis_road_distance=risk_result.road_distance_meters or 0
            )

            if override_check['should_override']:
                old_access = risk_result.road_access
                old_distance = risk_result.road_distance_meters

                # Update road access based on AI
                risk_result.road_access = override_check['new_road_access']
                risk_result.road_distance_meters = override_check['new_road_distance']
                risk_result.road_source = f"AI Override: {override_check['reason']}"

                # Update landlocked status
                risk_result.landlocked = not override_check['new_road_access']

                # Recalculate overall risk with new road access values
                updated_risk = gis_service._calculate_overall_risk(
                    wetlands={'status': risk_result.wetlands_status, 'confidence': 'HIGH'},
                    flood_zone={'severity': risk_result.flood_severity, 'confidence': 'HIGH'},
                    slope={'severity': risk_result.slope_severity, 'confidence': 'HIGH'},
                    road_access={'has_access': risk_result.road_access, 'confidence': 'HIGH'},
                    landlocked=risk_result.landlocked,
                    protected_land={'is_protected': risk_result.protected_land, 'confidence': 'HIGH'}
                )

                old_risk = risk_result.overall_risk
                risk_result.overall_risk = updated_risk

                logger.info(
                    f"Property {property_obj.id} - AI Override Applied: "
                    f"Road access changed from {old_access} ({old_distance}m) to "
                    f"{override_check['new_road_access']} ({override_check['new_road_distance']}m). "
                    f"Overall risk: {old_risk} -> {updated_risk}. "
                    f"Reason: {override_check['reason']}"
                )

        # Store results in database
        ai_record = AIAnalysisResult(
            property_id=property_obj.id,
            upload_id=upload_id,
            satellite_image_url=satellite_url,
            street_image_url=street_url_1,  # Using first street view for database
            satellite_image_source=satellite_source,
            street_image_source=street_source_1,  # Using first street view source
            road_condition_type=ai_result.get('road_condition', {}).get('type'),
            road_condition_confidence=ai_result.get('road_condition', {}).get('confidence'),
            power_lines_visible=ai_result.get('power_lines', {}).get('visible', False),
            power_line_confidence=ai_result.get('power_lines', {}).get('confidence'),
            power_line_distance_meters=ai_result.get('power_lines', {}).get('distance_meters'),
            power_line_geometry=ai_result.get('power_lines', {}).get('geometry'),
            nearby_dev_type=ai_result.get('nearby_development', {}).get('type'),
            nearby_dev_count=ai_result.get('nearby_development', {}).get('count'),
            nearby_dev_confidence=ai_result.get('nearby_development', {}).get('confidence'),
            nearby_dev_details=ai_result.get('nearby_development', {}).get('details'),
            structures_detected=ai_result.get('nearby_structures', {}).get('structures_detected', False),
            structures_count=ai_result.get('nearby_structures', {}).get('count'),
            structures_types=json.dumps(ai_result.get('nearby_structures', {}).get('types', [])),
            structures_density=ai_result.get('nearby_structures', {}).get('density'),
            structures_confidence=ai_result.get('nearby_structures', {}).get('confidence'),
            structures_details=ai_result.get('nearby_structures', {}).get('details'),
            ai_risk_level=ai_result.get('overall_ai_risk', {}).get('level', 'UNKNOWN'),
            ai_risk_confidence=ai_result.get('overall_ai_risk', {}).get('confidence', 0.0),
            processing_time_seconds=processing_time,
            error_message=ai_result.get('error'),
            model_version='v1.0'
        )

        db.add(ai_record)
        db.commit()

        total_time = time.time() - ai_start_time
        logger.info(f"✅ AI analysis saved to database")
        logger.info(f"🏁 Property {property_obj.id} AI processing complete in {total_time:.2f}s")
        logger.info(f"╚═══════════════════════════════════════════════════════════════╝\n")
        return True

    except Exception as e:
        logger.error(f"❌ Error processing AI for property {property_obj.id}: {str(e)}", exc_info=True)
        db.rollback()

        # Store error record
        try:
            ai_record = AIAnalysisResult(
                property_id=property_obj.id,
                upload_id=upload_id,
                error_message=str(e),
                model_version='v1.0'
            )
            db.add(ai_record)
            db.commit()
        except Exception as e2:
            logger.error(f"Failed to store error record: {str(e2)}")

        return False
    finally:
        db.close()


@app.get("/ai-results/{job_id}")
async def get_ai_results(job_id: str, db: Session = Depends(get_db)):
    """Get AI analysis results for a job"""
    try:
        upload_id = uuid.UUID(job_id)
        upload = db.query(Upload).filter(Upload.id == upload_id).first()

        if not upload:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get AI analysis results
        results = db.query(Property, AIAnalysisResult).join(
            AIAnalysisResult, Property.id == AIAnalysisResult.property_id
        ).filter(Property.upload_id == upload_id).all()

        formatted_results = []
        for prop, ai in results:
            formatted_results.append({
                "property_id": prop.id,
                "address": prop.full_address,
                "coordinates": {
                    "latitude": prop.latitude,
                    "longitude": prop.longitude
                },
                "imagery": {
                    "satellite": {
                        "url": ai.satellite_image_url,
                        "source": ai.satellite_image_source
                    },
                    "street": {
                        "url": ai.street_image_url,
                        "source": ai.street_image_source
                    }
                },
                "road_condition": {
                    "type": ai.road_condition_type,
                    "confidence": ai.road_condition_confidence
                },
                "power_lines": {
                    "visible": ai.power_lines_visible,
                    "confidence": ai.power_line_confidence,
                    "distance_meters": ai.power_line_distance_meters,
                    "geometry": ai.power_line_geometry
                },
                "nearby_development": {
                    "type": ai.nearby_dev_type,
                    "count": ai.nearby_dev_count,
                    "confidence": ai.nearby_dev_confidence,
                    "details": getattr(ai, 'nearby_dev_details', None)
                },
                "nearby_structures": {
                    "structures_detected": getattr(ai, 'structures_detected', False),
                    "count": getattr(ai, 'structures_count', None),
                    "types": json.loads(getattr(ai, 'structures_types', '[]') or '[]'),
                    "density": getattr(ai, 'structures_density', None),
                    "confidence": getattr(ai, 'structures_confidence', None),
                    "details": getattr(ai, 'structures_details', None)
                },
                "overall_ai_risk": {
                    "level": ai.ai_risk_level,
                    "confidence": ai.ai_risk_confidence
                },
                "processing_time_seconds": ai.processing_time_seconds,
                "model_version": ai.model_version,
                "analyzed_at": ai.analyzed_at.isoformat() if ai.analyzed_at else None,
                "error": ai.error_message
            })

        return {
            "job_id": str(upload.id),
            "total_results": len(formatted_results),
            "results": formatted_results
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")


# ============================================================================
# SKIP TRACING ENDPOINTS
# ============================================================================

@app.post("/skip-trace/{job_id}")
async def trigger_skip_trace(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger skip tracing for all properties in a job.

    This endpoint starts background processing to find owner contact information
    for all properties in the specified job using BatchData API.
    """
    try:
        upload_id = uuid.UUID(job_id)

        # Check if upload exists
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get property count
        property_count = db.query(Property).filter(Property.upload_id == upload_id).count()
        if property_count == 0:
            raise HTTPException(status_code=400, detail="No properties found for this job")

        # Check how many already have skip trace data
        existing_count = db.query(PropertyOwnerInfo).filter(
            PropertyOwnerInfo.upload_id == upload_id
        ).count()

        logger.info(f"Starting skip trace for job {job_id}: {property_count} properties, {existing_count} already traced")

        # Queue background task
        background_tasks.add_task(process_skip_trace, str(upload_id))

        return {
            "job_id": job_id,
            "message": "Skip trace processing started",
            "total_properties": property_count,
            "already_traced": existing_count,
            "status": "processing"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")


def process_skip_trace(upload_id: str):
    """
    Background worker to process skip tracing for all properties in a job.
    Uses ThreadPoolExecutor for concurrent processing.
    """
    db = SessionLocal()

    try:
        upload_uuid = uuid.UUID(upload_id)

        # Get all properties for this upload that don't have skip trace data yet
        properties = db.query(Property).filter(
            Property.upload_id == upload_uuid
        ).outerjoin(
            PropertyOwnerInfo,
            Property.id == PropertyOwnerInfo.property_id
        ).filter(
            PropertyOwnerInfo.id == None  # Only properties without owner info
        ).all()

        logger.info(f"Processing skip trace for {len(properties)} properties")

        # Skip if no properties to process
        if len(properties) == 0:
            logger.info("No properties need skip tracing")
            return

        # Process properties concurrently
        max_workers = min(5, len(properties))  # Max 5 concurrent skip traces

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for prop in properties:
                future = executor.submit(
                    process_single_property_skip_trace,
                    prop.id,
                    upload_id
                )
                futures.append(future)

            # Wait for all to complete
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Skip trace processing error: {str(e)}")

        logger.info(f"Skip trace processing completed for upload {upload_id}")

    except Exception as e:
        logger.error(f"Skip trace batch processing failed: {str(e)}", exc_info=True)
    finally:
        db.close()


def process_single_property_skip_trace(property_id: int, upload_id: str):
    """Process skip tracing for a single property using BatchData API"""
    db = SessionLocal()

    try:
        # Get property
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            logger.error(f"Property {property_id} not found")
            return

        logger.info(f"Skip tracing property: {prop.full_address}")

        # Perform skip trace with BatchData API
        result = skip_trace_service.skip_trace_property(
            property_address=prop.street_address,
            city=prop.city,
            state=prop.state,
            zip_code=prop.postal_code,
            owner_name=f"{prop.first_name or ''} {prop.last_name or ''}".strip() or None
        )

        # Create owner info record
        owner_info = PropertyOwnerInfo(
            property_id=property_id,
            upload_id=uuid.UUID(upload_id),
            source=result.get('source', 'BatchData API'),
            confidence_score=result.get('confidence_score', 0.0),
            processing_time_seconds=result.get('processing_time_seconds', 0.0),
            owner_info_status='complete' if result.get('owner_found') else 'not_found',
            error_message=result.get('error')
        )

        # Add owner data if found
        if result.get('owner_found') and result.get('owner_info'):
            owner_data = result['owner_info']

            # Name fields
            owner_info.owner_first_name = owner_data.get('first_name')
            owner_info.owner_middle_name = owner_data.get('middle_name')
            owner_info.owner_last_name = owner_data.get('last_name')
            owner_info.owner_full_name = owner_data.get('full_name')
            owner_info.owner_name = owner_data.get('full_name')  # Legacy field

            # Phone fields - individual
            owner_info.phone_primary = owner_data.get('phone_primary')
            owner_info.phone_mobile = owner_data.get('phone_mobile')
            owner_info.phone_secondary = owner_data.get('phone_secondary')
            owner_info.phone = owner_data.get('phone_primary')  # Legacy field
            owner_info.phone_count = owner_data.get('phone_count', 0)
            owner_info.phone_list = owner_data.get('phone_list')  # Full JSONB list

            # Email fields - individual
            owner_info.email_primary = owner_data.get('email_primary')
            owner_info.email_secondary = owner_data.get('email_secondary')
            owner_info.email = owner_data.get('email_primary')  # Legacy field
            owner_info.email_count = owner_data.get('email_count', 0)
            owner_info.email_list = owner_data.get('email_list')  # Full JSONB list

            # Mailing address - full details
            owner_info.mailing_street = owner_data.get('mailing_street')
            owner_info.mailing_city = owner_data.get('mailing_city')
            owner_info.mailing_state = owner_data.get('mailing_state')
            owner_info.mailing_zip = owner_data.get('mailing_zip')
            owner_info.mailing_zip_plus4 = owner_data.get('mailing_zip_plus4')
            owner_info.mailing_county = owner_data.get('mailing_county')
            owner_info.mailing_validity = owner_data.get('mailing_validity')
            owner_info.mailing_full_address = owner_data.get('mailing_full_address')
            owner_info.mailing_address = owner_data.get('mailing_full_address')  # Legacy field

            # Owner details
            owner_info.owner_type = owner_data.get('owner_type', 'Individual')
            owner_info.owner_occupied = owner_data.get('owner_occupied')

            # Compliance flags (critical for cold calling)
            owner_info.is_deceased = owner_data.get('is_deceased', False)
            owner_info.is_litigator = owner_data.get('is_litigator', False)
            owner_info.has_dnc = owner_data.get('has_dnc', False)
            owner_info.has_tcpa = owner_data.get('has_tcpa', False)
            owner_info.tcpa_blacklisted = owner_data.get('tcpa_blacklisted', False)

            # Bankruptcy and lien info
            owner_info.has_bankruptcy = owner_data.get('has_bankruptcy', False)
            owner_info.bankruptcy_info = owner_data.get('bankruptcy_info')
            owner_info.has_involuntary_lien = owner_data.get('has_involuntary_lien', False)
            owner_info.lien_info = owner_data.get('lien_info')

            # Property ID from skip trace
            owner_info.skip_trace_property_id = owner_data.get('property_id')

        # Store all persons (up to 3 from BatchData)
        if result.get('all_persons'):
            owner_info.all_persons = result.get('all_persons')

        # Store raw response for debugging
        if result.get('raw_response'):
            owner_info.raw_response = result.get('raw_response')

        db.add(owner_info)
        db.commit()

        logger.info(f"Skip trace completed for property {property_id}: {owner_info.owner_info_status}")

    except Exception as e:
        logger.error(f"Skip trace failed for property {property_id}: {str(e)}", exc_info=True)
        db.rollback()

        # Store error in database
        try:
            error_record = PropertyOwnerInfo(
                property_id=property_id,
                upload_id=uuid.UUID(upload_id),
                owner_info_status='error',
                error_message=str(e),
                source='BatchData API'
            )
            db.add(error_record)
            db.commit()
        except Exception as e2:
            logger.error(f"Failed to store error record: {str(e2)}")
            db.rollback()

    finally:
        db.close()


@app.get("/skip-trace/{job_id}")
async def get_skip_trace_results(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get skip trace results for all properties in a job.

    Returns owner contact information for each property.
    """
    try:
        upload_id = uuid.UUID(job_id)

        # Check if upload exists
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get all properties with their owner info
        results = db.query(Property, PropertyOwnerInfo).join(
            PropertyOwnerInfo,
            Property.id == PropertyOwnerInfo.property_id
        ).filter(
            Property.upload_id == upload_id
        ).all()

        # Count statistics
        total_properties = db.query(Property).filter(Property.upload_id == upload_id).count()
        traced_count = len(results)
        found_count = sum(1 for _, owner in results if owner.owner_info_status == 'complete')

        formatted_results = []
        for prop, owner in results:
            formatted_results.append({
                "property_id": prop.id,
                "address": {
                    "street": prop.street_address,
                    "city": prop.city,
                    "state": prop.state,
                    "zip": prop.postal_code,
                    "full_address": prop.full_address
                },
                "owner_info": {
                    "status": owner.owner_info_status,
                    "found": owner.owner_info_status == 'complete',
                    "name": {
                        "first": owner.owner_first_name,
                        "middle": owner.owner_middle_name,
                        "last": owner.owner_last_name,
                        "full": owner.owner_full_name
                    },
                    "contact": {
                        "phone_primary": owner.phone_primary,
                        "phone_mobile": owner.phone_mobile,
                        "phone_secondary": owner.phone_secondary,
                        "phone_count": owner.phone_count,
                        "phone_list": owner.phone_list,  # Full list with carrier, DNC, TCPA, score
                        "email_primary": owner.email_primary,
                        "email_secondary": owner.email_secondary,
                        "email_count": owner.email_count,
                        "email_list": owner.email_list  # Full list with tested status
                    },
                    "mailing_address": {
                        "street": owner.mailing_street,
                        "city": owner.mailing_city,
                        "state": owner.mailing_state,
                        "zip": owner.mailing_zip,
                        "zip_plus4": owner.mailing_zip_plus4,
                        "county": owner.mailing_county,
                        "validity": owner.mailing_validity,
                        "full": owner.mailing_full_address
                    },
                    "compliance": {
                        "is_deceased": owner.is_deceased,
                        "is_litigator": owner.is_litigator,
                        "has_dnc": owner.has_dnc,
                        "has_tcpa": owner.has_tcpa,
                        "tcpa_blacklisted": owner.tcpa_blacklisted,
                        "has_bankruptcy": owner.has_bankruptcy,
                        "has_involuntary_lien": owner.has_involuntary_lien
                    },
                    "details": {
                        "owner_type": owner.owner_type,
                        "owner_occupied": owner.owner_occupied,
                        "skip_trace_property_id": owner.skip_trace_property_id
                    },
                    "all_persons": owner.all_persons,  # Up to 3 persons from BatchData
                    "metadata": {
                        "source": owner.source,
                        "confidence": owner.confidence_score,
                        "retrieved_at": owner.retrieved_at.isoformat() if owner.retrieved_at else None,
                        "processing_time_seconds": owner.processing_time_seconds,
                        "error": owner.error_message
                    }
                }
            })

        return {
            "job_id": job_id,
            "statistics": {
                "total_properties": total_properties,
                "traced": traced_count,
                "found": found_count,
                "not_found": traced_count - found_count,
                "pending": total_properties - traced_count
            },
            "results": formatted_results
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
