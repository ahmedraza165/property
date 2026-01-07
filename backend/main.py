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

    try:
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

        if not all([street, city, state, postal_code]):
            logger.warning(f"Row {idx + 1}: Missing required address fields - Street: {street}, City: {city}, State: {state}, ZIP: {postal_code}")
            return False

        # Geocode address with fallback
        geocode_result = geocoding_service.geocode_address(street, city, state, postal_code)

        if not geocode_result:
            logger.warning(f"Row {idx + 1}: All geocoding methods failed for {street}, {city}, {state} {postal_code}")
            return False

        # Log geocoding source for monitoring
        logger.info(f"Row {idx + 1}: Geocoded via {geocode_result.get('source', 'unknown')} (accuracy: {geocode_result.get('accuracy', 'unknown')})")

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

        # Add original_data only if column exists in model (after migration)
        if hasattr(Property, 'original_data'):
            property_data['original_data'] = dict(row)

        property_record = Property(**property_data)

        db.add(property_record)
        db.flush()  # Get property ID

        # Perform GIS risk analysis with proper parameters
        risk_analysis = gis_service.analyze_property(
            latitude=geocode_result['latitude'],
            longitude=geocode_result['longitude'],
            address=street,
            city=city,
            state=state
        )

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

        logger.info(f"Processed property {idx + 1}")
        return True

    except Exception as e:
        logger.error(f"Error processing row {idx + 1}: {str(e)}")
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
                        "confidence": ai.nearby_dev_confidence
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


@app.get("/results/{job_id}/export")
async def export_results_csv(job_id: str, db: Session = Depends(get_db)):
    """
    Export results as CSV with original data + analysis.
    Preserves all original CSV columns and adds our risk analysis columns.
    """
    try:
        upload_id = uuid.UUID(job_id)
        upload = db.query(Upload).filter(Upload.id == upload_id).first()

        if not upload:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get all properties with their risk results
        results = db.query(Property, RiskResult).join(
            RiskResult, Property.id == RiskResult.property_id
        ).filter(Property.upload_id == upload_id).all()

        if not results:
            raise HTTPException(status_code=404, detail="No results found")

        # Create CSV in memory
        output = io.StringIO()

        # Get all unique column names from original data
        all_columns = set()
        for prop, _ in results:
            if prop.original_data:
                all_columns.update(prop.original_data.keys())

        # Define our analysis columns
        analysis_columns = [
            'Wetlands Status',
            'Wetlands Source',
            'Flood Zone',
            'Flood Severity',
            'Flood Source',
            'Slope Percentage',
            'Slope Severity',
            'Road Access',
            'Road Distance (m)',
            'Road Source',
            'Landlocked',
            'Protected Land',
            'Protected Land Type',
            'Overall Risk',
            'Processing Time (s)'
        ]

        # Combine: Original columns + Our analysis columns
        fieldnames = list(all_columns) + analysis_columns

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Write data rows
        for prop, risk in results:
            row_data = {}

            # Add original CSV data
            if prop.original_data:
                row_data.update(prop.original_data)

            # Add our analysis data
            row_data.update({
                'Wetlands Status': 'Yes' if risk.wetlands_status else 'No',
                'Wetlands Source': risk.wetlands_source,
                'Flood Zone': risk.flood_zone,
                'Flood Severity': risk.flood_severity,
                'Flood Source': risk.flood_source,
                'Slope Percentage': risk.slope_percentage,
                'Slope Severity': risk.slope_severity,
                'Road Access': 'Yes' if risk.road_access else 'No',
                'Road Distance (m)': risk.road_distance_meters,
                'Road Source': risk.road_source,
                'Landlocked': 'Yes' if risk.landlocked else 'No',
                'Protected Land': 'Yes' if risk.protected_land else 'No',
                'Protected Land Type': risk.protected_land_type,
                'Overall Risk': risk.overall_risk,
                'Processing Time (s)': risk.processing_time_seconds
            })

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

    try:
        # Skip if no coordinates
        if not property_obj.latitude or not property_obj.longitude:
            logger.warning(f"Skipping AI analysis for property {property_obj.id} - no coordinates")
            return False

        # Check if AI analysis already exists
        existing = db.query(AIAnalysisResult).filter(
            AIAnalysisResult.property_id == property_obj.id
        ).first()

        if existing:
            logger.info(f"AI analysis already exists for property {property_obj.id}")
            return True

        start_time = time.time()

        # Fetch imagery
        imagery = imagery_service.fetch_imagery(
            property_obj.latitude,
            property_obj.longitude,
            cache_db=db
        )

        satellite_url = imagery['satellite']['url']
        street_url = imagery['street']['url']
        satellite_source = imagery['satellite']['source']
        street_source = imagery['street']['source']

        # Perform AI analysis
        ai_result = ai_analysis_service.analyze_property(
            property_obj.latitude,
            property_obj.longitude,
            satellite_url,
            street_url
        )

        processing_time = time.time() - start_time

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
            street_image_url=street_url,
            satellite_image_source=satellite_source,
            street_image_source=street_source,
            road_condition_type=ai_result['road_condition']['type'] if ai_result['road_condition'] else None,
            road_condition_confidence=ai_result['road_condition']['confidence'] if ai_result['road_condition'] else None,
            power_lines_visible=ai_result['power_lines']['visible'] if ai_result['power_lines'] else False,
            power_line_confidence=ai_result['power_lines']['confidence'] if ai_result['power_lines'] else None,
            power_line_distance_meters=ai_result['power_lines']['distance_meters'] if ai_result['power_lines'] else None,
            power_line_geometry=ai_result['power_lines'].get('geometry') if ai_result['power_lines'] else None,
            nearby_dev_type=ai_result['nearby_development']['type'] if ai_result['nearby_development'] else None,
            nearby_dev_count=ai_result['nearby_development']['count'] if ai_result['nearby_development'] else None,
            nearby_dev_confidence=ai_result['nearby_development']['confidence'] if ai_result['nearby_development'] else None,
            ai_risk_level=ai_result['overall_ai_risk']['level'] if ai_result['overall_ai_risk'] else 'UNKNOWN',
            ai_risk_confidence=ai_result['overall_ai_risk']['confidence'] if ai_result['overall_ai_risk'] else 0.0,
            processing_time_seconds=processing_time,
            error_message=ai_result.get('error'),
            model_version='v1.0'
        )

        db.add(ai_record)
        db.commit()

        logger.info(f"AI analysis completed for property {property_obj.id}")
        return True

    except Exception as e:
        logger.error(f"Error processing AI for property {property_obj.id}: {str(e)}")
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
                    "confidence": ai.nearby_dev_confidence
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
    """Process skip tracing for a single property"""
    db = SessionLocal()

    try:
        # Get property
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            logger.error(f"Property {property_id} not found")
            return

        logger.info(f"Skip tracing property: {prop.full_address}")

        # Perform skip trace
        result = skip_trace_service.skip_trace_property(
            property_address=prop.street_address,
            city=prop.city,
            state=prop.state,
            zip_code=prop.postal_code,
            property_id=property_id
        )

        # Create owner info record
        owner_info = PropertyOwnerInfo(
            property_id=property_id,
            upload_id=uuid.UUID(upload_id),
            source=result.get('source', 'Unknown'),
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

            # Phone fields
            owner_info.phone_primary = owner_data.get('phone_primary')
            owner_info.phone_mobile = owner_data.get('phone_mobile')
            owner_info.phone_secondary = owner_data.get('phone_secondary')
            owner_info.phone = owner_data.get('phone_primary')  # Legacy field

            # Email fields
            owner_info.email_primary = owner_data.get('email_primary')
            owner_info.email_secondary = owner_data.get('email_secondary')
            owner_info.email = owner_data.get('email_primary')  # Legacy field

            # Mailing address
            owner_info.mailing_street = owner_data.get('mailing_street')
            owner_info.mailing_city = owner_data.get('mailing_city')
            owner_info.mailing_state = owner_data.get('mailing_state')
            owner_info.mailing_zip = owner_data.get('mailing_zip')
            owner_info.mailing_full_address = owner_data.get('mailing_full_address')
            owner_info.mailing_address = owner_data.get('mailing_full_address')  # Legacy field

            # Owner details
            owner_info.owner_type = owner_data.get('owner_type', 'Unknown')
            owner_info.owner_occupied = owner_data.get('owner_occupied')

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
                    "street": prop.street,
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
