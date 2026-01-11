import requests
import logging
import base64
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ImageryService:
    """
    Service for fetching satellite and street-level imagery from multiple providers.
    Supports caching and fallback mechanisms.
    """

    def __init__(self):
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'PropertyAnalysis/1.0'
        })
        return session

    def fetch_imagery(
        self,
        latitude: float,
        longitude: float,
        cache_db=None
    ) -> Dict[str, any]:
        """
        Fetch satellite and multiple street-level imagery angles for a property.
        Returns URLs for frontend display + base64 for AI analysis.

        NEW: Fetches 3 images total:
        - 1 satellite (top view with marker)
        - 2 street views (different angles for better AI analysis)

        Args:
            latitude: Property latitude
            longitude: Property longitude
            cache_db: Optional database session for caching

        Returns:
            Dictionary with:
            - satellite: {url, base64, source, error}
            - street_view_1: {url, base64, source, error, heading}
            - street_view_2: {url, base64, source, error, heading}
        """
        result = {
            "satellite": {
                "url": None,
                "base64": None,
                "source": None,
                "error": None
            },
            "street_view_1": {
                "url": None,
                "base64": None,
                "source": None,
                "error": None,
                "heading": 0
            },
            "street_view_2": {
                "url": None,
                "base64": None,
                "source": None,
                "error": None,
                "heading": 180
            }
        }

        # Fetch MARKED satellite imagery (Mapbox with red marker)
        logger.info("Fetching marked satellite imagery (top view)...")
        satellite_data = self._fetch_marked_satellite(latitude, longitude)
        result["satellite"] = satellite_data

        # Fetch Google Street View - Angle 1 (heading 0 degrees - North)
        logger.info("Fetching Street View - Angle 1 (heading 0°)...")
        street_data_1 = self._fetch_google_streetview(latitude, longitude, heading=0)
        result["street_view_1"] = street_data_1

        # Fetch Google Street View - Angle 2 (heading 180 degrees - South, opposite direction)
        logger.info("Fetching Street View - Angle 2 (heading 180°)...")
        street_data_2 = self._fetch_google_streetview(latitude, longitude, heading=180)
        result["street_view_2"] = street_data_2

        return result

    def _fetch_marked_satellite(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, any]:
        """
        Fetch Google Maps satellite imagery with red marker.
        Returns both URL (for frontend) and base64 (for AI).
        """
        import os

        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            logger.error("GOOGLE_MAPS_API_KEY not set")
            return {
                "url": None,
                "base64": None,
                "source": None,
                "error": "Google Maps API key not configured"
            }

        # Build Google Maps Static API satellite URL with marker
        zoom = 18
        width = 800
        height = 800

        # Google Static Maps with satellite + marker
        url = (
            f"https://maps.googleapis.com/maps/api/staticmap?"
            f"center={latitude},{longitude}"
            f"&zoom={zoom}"
            f"&size={width}x{height}"
            f"&maptype=satellite"
            f"&markers=color:red%7C{latitude},{longitude}"
            f"&key={api_key}"
        )

        # Download image and convert to base64
        try:
            logger.info(f"Downloading satellite image from Google Maps Static API...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            image_bytes = response.content
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            base64_url = f"data:image/jpeg;base64,{image_base64}"

            logger.info(f"✅ Google satellite image downloaded ({len(image_bytes)} bytes)")

            return {
                "url": url,
                "base64": base64_url,
                "source": "Google Maps Satellite",
                "error": None
            }
        except Exception as e:
            logger.error(f"Failed to fetch Google satellite: {str(e)}")
            return {
                "url": None,
                "base64": None,
                "source": None,
                "error": str(e)
            }

    def _fetch_google_streetview(
        self,
        latitude: float,
        longitude: float,
        heading: int = 0
    ) -> Dict[str, any]:
        """
        Fetch Google Street View image with specific heading angle.
        Returns both URL (for frontend) and base64 (for AI).

        Args:
            latitude: Property latitude
            longitude: Property longitude
            heading: Camera heading (0-360 degrees, 0=North, 90=East, 180=South, 270=West)
        """
        import os

        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            logger.error("GOOGLE_MAPS_API_KEY not set")
            return {
                "url": None,
                "base64": None,
                "source": None,
                "error": "Google Maps API key not configured",
                "heading": heading
            }

        # Check if Street View is available
        metadata_url = (
            f"https://maps.googleapis.com/maps/api/streetview/metadata?"
            f"location={latitude},{longitude}&key={api_key}"
        )

        try:
            logger.info(f"Checking Street View availability (heading {heading}°)...")
            metadata_response = self.session.get(metadata_url, timeout=10)
            metadata_response.raise_for_status()
            metadata = metadata_response.json()

            if metadata.get('status') != 'OK':
                logger.warning(f"Street View not available: {metadata.get('status')}")
                return {
                    "url": None,
                    "base64": None,
                    "source": None,
                    "error": "Street View not available for this location",
                    "heading": heading
                }

            # Build Street View URL with heading parameter
            width = 800
            height = 600
            fov = 90  # Field of view
            streetview_url = (
                f"https://maps.googleapis.com/maps/api/streetview?"
                f"size={width}x{height}&location={latitude},{longitude}"
                f"&heading={heading}&fov={fov}&pitch=0"
                f"&key={api_key}"
            )

            # Download image and convert to base64
            logger.info(f"Downloading Street View (heading {heading}°) from Google...")
            response = self.session.get(streetview_url, timeout=30)
            response.raise_for_status()

            image_bytes = response.content
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            base64_url = f"data:image/jpeg;base64,{image_base64}"

            logger.info(f"✅ Street View image (heading {heading}°) downloaded ({len(image_bytes)} bytes)")

            return {
                "url": streetview_url,
                "base64": base64_url,
                "source": f"Google Street View (heading {heading}°)",
                "error": None,
                "heading": heading
            }
        except Exception as e:
            logger.error(f"Failed to fetch Street View (heading {heading}°): {str(e)}")
            return {
                "url": None,
                "base64": None,
                "source": None,
                "error": str(e),
                "heading": heading
            }

    def _fetch_satellite_imagery(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, any]:
        """
        Fetch satellite imagery with fallback providers.

        Providers tried in order:
        1. Mapbox Static Images API
        2. Google Maps Static API
        3. OpenStreetMap/Bing fallback
        """
        # Try Mapbox first (most reliable for satellite imagery)
        try:
            mapbox_url = self._get_mapbox_satellite(latitude, longitude)
            if mapbox_url:
                return {
                    "url": mapbox_url,
                    "source": "Mapbox Satellite",
                    "error": None
                }
        except Exception as e:
            logger.debug(f"Mapbox satellite failed: {str(e)}")

        # Try Google Maps Static API
        try:
            google_url = self._get_google_satellite(latitude, longitude)
            if google_url:
                return {
                    "url": google_url,
                    "source": "Google Maps Satellite",
                    "error": None
                }
        except Exception as e:
            logger.debug(f"Google satellite failed: {str(e)}")

        # Fallback to OpenStreetMap base map (not satellite, but better than nothing)
        try:
            osm_url = self._get_osm_map(latitude, longitude)
            return {
                "url": osm_url,
                "source": "OpenStreetMap (Fallback)",
                "error": "Satellite imagery unavailable, using map view"
            }
        except Exception as e:
            logger.error(f"All satellite imagery providers failed: {str(e)}")
            return {
                "url": None,
                "source": None,
                "error": "Unable to fetch satellite imagery"
            }

    def _fetch_street_imagery(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, any]:
        """
        Fetch street-level imagery with fallback providers.

        Providers tried in order:
        1. Mapillary API
        2. Google Street View API
        3. Bing Streetside API
        """
        # Try Mapillary first (open-source street imagery)
        try:
            mapillary_url = self._get_mapillary_image(latitude, longitude)
            if mapillary_url:
                return {
                    "url": mapillary_url,
                    "source": "Mapillary",
                    "error": None
                }
        except Exception as e:
            logger.debug(f"Mapillary failed: {str(e)}")

        # Try Google Street View
        try:
            streetview_url = self._get_google_streetview(latitude, longitude)
            if streetview_url:
                return {
                    "url": streetview_url,
                    "source": "Google Street View",
                    "error": None
                }
        except Exception as e:
            logger.debug(f"Google Street View failed: {str(e)}")

        # No street imagery available
        return {
            "url": None,
            "source": None,
            "error": "No street-level imagery available for this location"
        }

    def _get_mapbox_satellite(
        self,
        latitude: float,
        longitude: float,
        zoom: int = 18,  # Balanced zoom: clear structures + surrounding area
        width: int = 800,
        height: int = 800  # Square image for better AI analysis
    ) -> Optional[str]:
        """
        Get Mapbox satellite imagery URL with property marker.

        Features:
        - Zoom 18: Shows ~200m radius with clear structures
        - Red marker: Identifies exact property location for AI
        - High resolution: @2x for detailed analysis

        Note: Requires MAPBOX_ACCESS_TOKEN environment variable.
        Free tier: 50,000 requests/month
        """
        import os

        access_token = os.getenv('MAPBOX_ACCESS_TOKEN')
        if not access_token:
            logger.warning("MAPBOX_ACCESS_TOKEN not set")
            return None

        # Add red marker pin at property location to help AI identify target
        # Format: pin-SIZE+COLOR(lon,lat)
        marker_spec = f"pin-s+ff0000({longitude},{latitude})"

        # Mapbox Static Images API with marker overlay
        # @2x = high resolution for better AI detection
        url = (
            f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/"
            f"{marker_spec}/{longitude},{latitude},{zoom},0/{width}x{height}@2x"
            f"?access_token={access_token}"
        )

        logger.debug(f"Mapbox satellite URL: zoom={zoom}, marked property at {latitude},{longitude}")

        # Verify the URL is accessible
        try:
            response = self.session.head(url, timeout=5)
            if response.status_code == 200:
                return url
        except Exception as e:
            logger.debug(f"Mapbox URL verification failed: {e}")

        return None

    def _get_google_satellite(
        self,
        latitude: float,
        longitude: float,
        zoom: int = 19,
        width: int = 800,
        height: int = 600
    ) -> Optional[str]:
        """
        Get Google Maps Static API satellite imagery URL.

        Note: Requires GOOGLE_MAPS_API_KEY environment variable.
        """
        import os

        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not set")
            return None

        url = (
            f"https://maps.googleapis.com/maps/api/staticmap?"
            f"center={latitude},{longitude}&zoom={zoom}&size={width}x{height}"
            f"&maptype=satellite&key={api_key}"
        )

        # Verify the URL is accessible
        response = self.session.head(url, timeout=5)
        if response.status_code == 200:
            return url

        return None

    def _get_osm_map(
        self,
        latitude: float,
        longitude: float,
        zoom: int = 17,
        width: int = 800,
        height: int = 600
    ) -> str:
        """
        Get OpenStreetMap static map URL (fallback).
        Uses staticmap.openstreetmap.de service.
        """
        # Using StaticMap service
        url = (
            f"https://staticmap.openstreetmap.de/staticmap.php?"
            f"center={latitude},{longitude}&zoom={zoom}&size={width}x{height}"
            f"&maptype=mapnik&markers={latitude},{longitude},red"
        )

        return url

    def _get_mapillary_image(
        self,
        latitude: float,
        longitude: float,
        radius: int = 50
    ) -> Optional[str]:
        """
        Get Mapillary street-level imagery.

        Note: Requires MAPILLARY_CLIENT_TOKEN environment variable.
        """
        import os

        client_token = os.getenv('MAPILLARY_CLIENT_TOKEN')
        if not client_token:
            logger.warning("MAPILLARY_CLIENT_TOKEN not set")
            return None

        # Search for images near the location
        search_url = (
            f"https://graph.mapillary.com/images?"
            f"access_token={client_token}"
            f"&fields=id,thumb_2048_url"
            f"&bbox={longitude-0.0005},{latitude-0.0005},{longitude+0.0005},{latitude+0.0005}"
        )

        try:
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('data') and len(data['data']) > 0:
                # Return the first available image
                return data['data'][0].get('thumb_2048_url')
        except Exception as e:
            logger.debug(f"Mapillary API error: {str(e)}")

        return None

    def _get_google_streetview(
        self,
        latitude: float,
        longitude: float,
        width: int = 800,
        height: int = 600
    ) -> Optional[str]:
        """
        Get Google Street View imagery.

        Note: Requires GOOGLE_MAPS_API_KEY environment variable.
        """
        import os

        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not set")
            return None

        # First check if Street View is available
        metadata_url = (
            f"https://maps.googleapis.com/maps/api/streetview/metadata?"
            f"location={latitude},{longitude}&key={api_key}"
        )

        try:
            response = self.session.get(metadata_url, timeout=10)
            response.raise_for_status()
            metadata = response.json()

            if metadata.get('status') == 'OK':
                # Street View is available
                streetview_url = (
                    f"https://maps.googleapis.com/maps/api/streetview?"
                    f"size={width}x{height}&location={latitude},{longitude}"
                    f"&key={api_key}"
                )
                return streetview_url
        except Exception as e:
            logger.debug(f"Google Street View API error: {str(e)}")

        return None

    def _get_cached_image(
        self,
        db,
        latitude: float,
        longitude: float,
        image_type: str,
        max_age_days: int = 30
    ) -> Optional[Dict[str, any]]:
        """
        Retrieve cached image from database.

        Args:
            db: Database session
            latitude: Property latitude
            longitude: Property longitude
            image_type: 'satellite' or 'street'
            max_age_days: Maximum age of cached image in days

        Returns:
            Cached image data or None
        """
        from models import ImageCache
        from sqlalchemy import and_

        # Find cached image within a small radius (0.0001 degrees ~ 11 meters)
        radius = 0.0001
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

        cached = db.query(ImageCache).filter(
            and_(
                ImageCache.latitude.between(latitude - radius, latitude + radius),
                ImageCache.longitude.between(longitude - radius, longitude + radius),
                ImageCache.image_type == image_type,
                ImageCache.fetched_at >= cutoff_date
            )
        ).first()

        if cached and cached.image_url:
            logger.info(f"Using cached {image_type} image from {cached.source}")
            return {
                "url": cached.image_url,
                "source": cached.source + " (cached)",
                "error": None
            }

        return None

    def _cache_image(
        self,
        db,
        latitude: float,
        longitude: float,
        image_type: str,
        image_url: str,
        source: str
    ) -> None:
        """
        Cache image in database.

        Args:
            db: Database session
            latitude: Property latitude
            longitude: Property longitude
            image_type: 'satellite' or 'street'
            image_url: URL of the image
            source: Provider name
        """
        from models import ImageCache

        cached_image = ImageCache(
            latitude=latitude,
            longitude=longitude,
            image_type=image_type,
            image_url=image_url,
            source=source
        )

        db.add(cached_image)
        db.commit()
        logger.info(f"Cached {image_type} image from {source}")
