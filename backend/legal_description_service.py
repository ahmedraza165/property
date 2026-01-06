import requests
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class LegalDescriptionService:
    """
    Service to fetch legal descriptions and parcel data
    Uses multiple free sources with fallbacks
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PropertyAnalysisTool/1.0'
        })

    def get_legal_description(self, latitude: float, longitude: float, county: str = None) -> Optional[Dict]:
        """
        Attempt to get legal description from multiple sources
        """
        # Try OpenStreetMap first (free)
        osm_result = self._get_from_osm(latitude, longitude)
        if osm_result:
            return osm_result

        # Fallback: Generate basic description from coordinates
        return self._generate_basic_description(latitude, longitude, county)

    def _get_from_osm(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Query OpenStreetMap for parcel/property information
        """
        overpass_url = "https://overpass-api.de/api/interpreter"

        # Query for land parcels, cadastre, or property boundaries near the point
        query = f"""
        [out:json][timeout:10];
        (
          way["landuse"](around:50,{latitude},{longitude});
          way["boundary"="cadastre"](around:50,{latitude},{longitude});
          relation["type"="multipolygon"]["landuse"](around:50,{latitude},{longitude});
        );
        out tags;
        """

        try:
            response = self.session.post(overpass_url, data={"data": query}, timeout=15)
            response.raise_for_status()
            data = response.json()

            if data.get("elements"):
                element = data["elements"][0]
                tags = element.get("tags", {})

                # Extract relevant parcel information
                legal_desc_parts = []

                if tags.get("ref:parcelle"):
                    legal_desc_parts.append(f"Parcel: {tags['ref:parcelle']}")
                if tags.get("addr:street"):
                    legal_desc_parts.append(f"Street: {tags['addr:street']}")
                if tags.get("landuse"):
                    legal_desc_parts.append(f"Land Use: {tags['landuse']}")

                if legal_desc_parts:
                    return {
                        "legal_description": ", ".join(legal_desc_parts),
                        "source": "OpenStreetMap",
                        "parcel_id": tags.get("ref:parcelle"),
                        "land_use": tags.get("landuse")
                    }

        except Exception as e:
            logger.debug(f"OSM query failed: {str(e)}")

        return None

    def _generate_basic_description(self, latitude: float, longitude: float, county: str = None) -> Dict:
        """
        Generate a basic legal description from coordinates
        Uses Public Land Survey System (PLSS) format approximation
        """
        # Convert to degrees, minutes, seconds for legal description format
        lat_deg = int(latitude)
        lat_min = int((latitude - lat_deg) * 60)
        lat_sec = ((latitude - lat_deg) * 60 - lat_min) * 60

        lon_deg = int(abs(longitude))
        lon_min = int((abs(longitude) - lon_deg) * 60)
        lon_sec = ((abs(longitude) - lon_deg) * 60 - lon_min) * 60

        lat_dir = "N" if latitude >= 0 else "S"
        lon_dir = "W" if longitude < 0 else "E"

        description = f"Located at {lat_deg}°{lat_min}'{lat_sec:.1f}\"{lat_dir}, {lon_deg}°{lon_min}'{lon_sec:.1f}\"{lon_dir}"

        if county:
            description += f", {county} County"

        return {
            "legal_description": description,
            "source": "Generated from coordinates",
            "parcel_id": None,
            "land_use": None
        }

    def estimate_lot_size(self, latitude: float, longitude: float) -> Dict:
        """
        Attempt to estimate lot size from parcel boundaries
        Returns size in acres and square feet
        """
        # This is a placeholder - actual implementation would require parcel boundary data
        # For now, return None to indicate unavailable
        return {
            "lot_size_acres": None,
            "lot_size_sqft": None,
            "source": "Not available"
        }
