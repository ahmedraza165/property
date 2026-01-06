import requests
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class WaterUtilityService:
    """
    Service to check water and sewer utility availability
    Uses OpenStreetMap Overpass API to detect infrastructure
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PropertyAnalysisTool/1.0'
        })
        self.overpass_url = "https://overpass-api.de/api/interpreter"

    def check_utilities(self, latitude: float, longitude: float, search_radius: int = 500) -> Dict:
        """
        Check for water and sewer utility infrastructure near the property

        Args:
            latitude: Property latitude
            longitude: Property longitude
            search_radius: Search radius in meters (default 500m)

        Returns:
            Dict with water and sewer availability info
        """
        # Check for water infrastructure
        water_result = self._check_water_infrastructure(latitude, longitude, search_radius)

        # Check for sewer infrastructure
        sewer_result = self._check_sewer_infrastructure(latitude, longitude, search_radius)

        return {
            "water_available": water_result.get("available"),
            "water_provider": water_result.get("provider"),
            "water_distance_meters": water_result.get("distance"),
            "sewer_available": sewer_result.get("available"),
            "sewer_provider": sewer_result.get("provider"),
            "sewer_distance_meters": sewer_result.get("distance"),
            "source": "OpenStreetMap"
        }

    def _check_water_infrastructure(self, latitude: float, longitude: float, radius: int) -> Dict:
        """
        Check for water infrastructure (pipes, treatment plants, water towers)
        """
        query = f"""
        [out:json][timeout:10];
        (
          way["man_made"="pipeline"]["substance"="water"](around:{radius},{latitude},{longitude});
          way["man_made"="water_works"](around:{radius},{latitude},{longitude});
          node["man_made"="water_tower"](around:{radius},{latitude},{longitude});
          node["man_made"="water_well"](around:{radius},{latitude},{longitude});
          node["amenity"="drinking_water"](around:{radius},{latitude},{longitude});
        );
        out tags;
        """

        try:
            response = self.session.post(self.overpass_url, data={"data": query}, timeout=15)
            response.raise_for_status()
            data = response.json()

            if data.get("elements"):
                # Water infrastructure found
                element = data["elements"][0]
                tags = element.get("tags", {})

                provider = tags.get("operator") or tags.get("name") or "Municipal Water"

                return {
                    "available": True,
                    "provider": provider,
                    "distance": radius,  # Approximate distance
                    "infrastructure_type": tags.get("man_made") or tags.get("amenity")
                }
            else:
                # No water infrastructure found within radius
                return {
                    "available": None,  # Unknown
                    "provider": None,
                    "distance": None
                }

        except Exception as e:
            logger.error(f"Error checking water infrastructure: {str(e)}")
            return {
                "available": None,
                "provider": None,
                "distance": None
            }

    def _check_sewer_infrastructure(self, latitude: float, longitude: float, radius: int) -> Dict:
        """
        Check for sewer infrastructure (sewer lines, treatment plants)
        """
        query = f"""
        [out:json][timeout:10];
        (
          way["man_made"="pipeline"]["substance"="sewage"](around:{radius},{latitude},{longitude});
          way["man_made"="wastewater_plant"](around:{radius},{latitude},{longitude});
          node["man_made"="wastewater_plant"](around:{radius},{latitude},{longitude});
        );
        out tags;
        """

        try:
            response = self.session.post(self.overpass_url, data={"data": query}, timeout=15)
            response.raise_for_status()
            data = response.json()

            if data.get("elements"):
                # Sewer infrastructure found
                element = data["elements"][0]
                tags = element.get("tags", {})

                provider = tags.get("operator") or tags.get("name") or "Municipal Sewer"

                return {
                    "available": True,
                    "provider": provider,
                    "distance": radius,
                    "infrastructure_type": tags.get("man_made")
                }
            else:
                # No sewer infrastructure found
                return {
                    "available": None,  # Unknown
                    "provider": None,
                    "distance": None
                }

        except Exception as e:
            logger.error(f"Error checking sewer infrastructure: {str(e)}")
            return {
                "available": None,
                "provider": None,
                "distance": None
            }
