from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class GeocodingCache(Base):
    __tablename__ = 'geocoding_cache'

    id = Column(Integer, primary_key=True)
    full_address = Column(Text, nullable=False, unique=True)
    latitude = Column(Float)
    longitude = Column(Float)
    accuracy = Column(String(50))
    match_type = Column(String(50))
    geocoded_at = Column(DateTime, server_default=func.current_timestamp())
    source = Column(String(100), default='US Census Geocoder')


class Upload(Base):
    __tablename__ = 'uploads'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    total_rows = Column(Integer, nullable=False)
    processed_rows = Column(Integer, default=0)
    status = Column(String(50), default='processing')
    uploaded_at = Column(DateTime, server_default=func.current_timestamp())
    completed_at = Column(DateTime)
    error_message = Column(Text)


class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True)
    upload_id = Column(UUID(as_uuid=True), ForeignKey('uploads.id', ondelete='CASCADE'))
    contact_id = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    full_name = Column(String(255))
    tags = Column(Text)
    street_address = Column(Text, nullable=False)
    postal_code = Column(String(20))
    state = Column(String(2))
    city = Column(String(255))
    county = Column(String(255))
    full_address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    geocode_accuracy = Column(String(50))

    # Additional property details
    legal_description = Column(Text)
    lot_size_acres = Column(Float)
    lot_size_sqft = Column(Float)

    # Original CSV data preservation (stores entire row as JSON)
    original_data = Column(JSONB)

    created_at = Column(DateTime, server_default=func.current_timestamp())


class RiskResult(Base):
    __tablename__ = 'risk_results'

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id', ondelete='CASCADE'))
    upload_id = Column(UUID(as_uuid=True), ForeignKey('uploads.id', ondelete='CASCADE'))

    # Wetlands
    wetlands_status = Column(Boolean, default=False)
    wetlands_source = Column(String(200))

    # Flood zone
    flood_zone = Column(String(50))
    flood_severity = Column(String(20))
    flood_source = Column(String(200))

    # Slope
    slope_percentage = Column(Float)
    slope_severity = Column(String(20))
    slope_source = Column(String(200))

    # Road access
    road_access = Column(Boolean, default=False)
    road_distance_meters = Column(Float)
    road_source = Column(String(200))

    # Landlocked
    landlocked = Column(Boolean, default=False)

    # Protected land
    protected_land = Column(Boolean, default=False)
    protected_land_type = Column(String(255))
    protected_land_source = Column(String(200))

    # Water Utility
    water_available = Column(Boolean)
    sewer_available = Column(Boolean)
    water_provider = Column(String(255))
    sewer_provider = Column(String(255))
    utility_source = Column(String(200))

    # Overall risk
    overall_risk = Column(String(20))

    # Metadata
    processed_at = Column(DateTime, server_default=func.current_timestamp())
    processing_time_seconds = Column(Float)
    error_message = Column(Text)


class AIAnalysisResult(Base):
    __tablename__ = 'ai_analysis_results'

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id', ondelete='CASCADE'))
    upload_id = Column(UUID(as_uuid=True), ForeignKey('uploads.id', ondelete='CASCADE'))

    # Image URLs
    satellite_image_url = Column(Text)
    street_image_url = Column(Text)
    satellite_image_source = Column(String(100))  # Provider name
    street_image_source = Column(String(100))  # Provider name

    # Road condition
    road_condition_type = Column(String(50))
    road_condition_confidence = Column(Float)

    # Power lines
    power_lines_visible = Column(Boolean, default=False)
    power_line_confidence = Column(Float)
    power_line_distance_meters = Column(Float)
    power_line_geometry = Column(Text)  # GeoJSON for detected power lines

    # Nearby development
    nearby_dev_type = Column(String(50))
    nearby_dev_count = Column(Integer)
    nearby_dev_confidence = Column(Float)
    nearby_dev_details = Column(Text)

    # Nearby structures (detailed breakdown)
    structures_detected = Column(Boolean, default=False)
    structures_count = Column(Integer)
    structures_types = Column(Text)  # JSON array of types
    structures_density = Column(String(20))
    structures_confidence = Column(Float)
    structures_details = Column(Text)

    # Overall AI risk
    ai_risk_level = Column(String(10))
    ai_risk_confidence = Column(Float)

    # Metadata
    analyzed_at = Column(DateTime, server_default=func.current_timestamp())
    processing_time_seconds = Column(Float)
    error_message = Column(Text)
    model_version = Column(String(50), default='v1.0')


class ImageCache(Base):
    __tablename__ = 'image_cache'

    id = Column(Integer, primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    image_type = Column(String(20), nullable=False)
    image_url = Column(Text)
    fetched_at = Column(DateTime, server_default=func.current_timestamp())
    source = Column(String(100))


class APIRateLimit(Base):
    __tablename__ = 'api_rate_limits'

    id = Column(Integer, primary_key=True)
    api_name = Column(String(100), nullable=False, unique=True)
    request_count = Column(Integer, default=0)
    window_start = Column(DateTime, server_default=func.current_timestamp())
    last_request_at = Column(DateTime)


class PropertyOwnerInfo(Base):
    __tablename__ = 'property_owner_info'

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id', ondelete='CASCADE'), nullable=False)
    upload_id = Column(UUID(as_uuid=True), ForeignKey('uploads.id', ondelete='CASCADE'))

    # Owner information
    owner_name = Column(String(500))
    owner_first_name = Column(String(255))
    owner_middle_name = Column(String(255))
    owner_last_name = Column(String(255))
    owner_full_name = Column(String(500))
    owner_type = Column(String(50))
    owner_occupied = Column(Boolean)

    # Contact - Phone
    phone = Column(String(50))  # Legacy field
    phone_primary = Column(String(50))
    phone_mobile = Column(String(50))
    phone_secondary = Column(String(50))
    phone_count = Column(Integer)
    phone_list = Column(JSONB)  # Full list with all phone details

    # Contact - Email
    email = Column(String(255))  # Legacy field
    email_primary = Column(String(255))
    email_secondary = Column(String(255))
    email_count = Column(Integer)
    email_list = Column(JSONB)  # Full list with all email details

    # Mailing Address
    mailing_address = Column(Text)  # Legacy field
    mailing_street = Column(Text)
    mailing_city = Column(String(255))
    mailing_state = Column(String(10))
    mailing_zip = Column(String(20))
    mailing_zip_plus4 = Column(String(10))
    mailing_county = Column(String(255))
    mailing_validity = Column(String(50))
    mailing_full_address = Column(Text)

    # All persons from skip trace (up to 3)
    all_persons = Column(JSONB)

    # Compliance Flags (important for cold calling)
    is_deceased = Column(Boolean, default=False)
    is_litigator = Column(Boolean, default=False)
    has_dnc = Column(Boolean, default=False)  # Do Not Call
    has_tcpa = Column(Boolean, default=False)  # TCPA blacklisted
    tcpa_blacklisted = Column(Boolean, default=False)

    # Bankruptcy and Lien info
    has_bankruptcy = Column(Boolean, default=False)
    bankruptcy_info = Column(JSONB)
    has_involuntary_lien = Column(Boolean, default=False)
    lien_info = Column(JSONB)

    # Property info from skip trace
    skip_trace_property_id = Column(String(255))

    # Metadata
    source = Column(String(100))
    retrieved_at = Column(DateTime, server_default=func.current_timestamp())
    owner_info_status = Column(String(20), default='pending')
    confidence_score = Column(Float)
    error_message = Column(Text)
    processing_time_seconds = Column(Float)

    # Additional fields for tracking retries
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime)

    # Raw API response for debugging
    raw_response = Column(JSONB)
