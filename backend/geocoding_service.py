import requests
import time
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class GeocodingService:
    """
    Robust geocoding service with multiple fallback providers

    Providers (in order of priority):
    1. US Census Geocoder (free, no API key)
    2. OpenStreetMap Nominatim (free, no API key)
    3. Geographic estimation (fallback for known areas)
    """

    def __init__(self):
        self.census_url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PropertyAnalysisService/2.0'
        })

        # ZIP code to approximate coordinates mapping (Florida focus)
        self.zip_coordinates = self._load_zip_coordinates()

    def _load_zip_coordinates(self) -> Dict[str, Tuple[float, float]]:
        """Load approximate coordinates for common ZIP codes"""
        return {
            # Southwest Florida
            "33971": (26.6254, -81.6437),  # Lehigh Acres
            "33976": (26.5731, -81.6881),  # Lehigh Acres
            "33974": (26.6531, -81.6209),  # Lehigh Acres
            "33972": (26.5920, -81.6570),  # Lehigh Acres
            "33973": (26.5731, -81.6881),  # Lehigh Acres
            # Add more as needed
        }

    def geocode_address(self, street: str, city: str, state: str, zip_code: str) -> Optional[Dict]:
        """
        Geocode an address using multiple providers with fallback
        Returns coordinates and address components including county
        """
        full_address = f"{street}, {city}, {state} {zip_code}"

        # Try Census API first
        result = self._try_census_geocoding(street, city, state, zip_code, full_address)
        if result:
            logger.info(f"Geocoded via Census API: {full_address}")
            return result

        # Try Nominatim (OpenStreetMap)
        result = self._try_nominatim_geocoding(street, city, state, zip_code, full_address)
        if result:
            logger.info(f"Geocoded via Nominatim: {full_address}")
            return result

        # Try ZIP code approximation
        result = self._try_zip_approximation(street, city, state, zip_code, full_address)
        if result:
            logger.info(f"Geocoded via ZIP approximation: {full_address}")
            return result

        logger.warning(f"All geocoding methods failed for: {full_address}")
        return None

    def _try_census_geocoding(self, street: str, city: str, state: str,
                              zip_code: str, full_address: str) -> Optional[Dict]:
        """Try US Census Geocoder API"""
        params = {
            "address": full_address,
            "benchmark": "Public_AR_Current",
            "format": "json"
        }

        try:
            response = self.session.get(self.census_url, params=params, timeout=8)
            response.raise_for_status()
            data = response.json()

            if data.get("result", {}).get("addressMatches"):
                match = data["result"]["addressMatches"][0]
                coords = match["coordinates"]
                address_components = match["addressComponents"]

                return {
                    "latitude": coords["y"],
                    "longitude": coords["x"],
                    "full_address": full_address,
                    "street": address_components.get("streetName", street),
                    "city": address_components.get("city", city),
                    "state": address_components.get("state", state),
                    "zip": address_components.get("zip", zip_code),
                    "county": address_components.get("county", None),
                    "accuracy": "HIGH",
                    "source": "US Census Geocoder"
                }
        except Exception as e:
            logger.debug(f"Census geocoding failed: {str(e)}")

        return None

    def _try_nominatim_geocoding(self, street: str, city: str, state: str,
                                  zip_code: str, full_address: str) -> Optional[Dict]:
        """Try OpenStreetMap Nominatim API"""
        params = {
            "q": full_address,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
            "countrycodes": "us"
        }

        try:
            # Add delay to respect Nominatim usage policy
            time.sleep(1)

            response = self.session.get(self.nominatim_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 0:
                result = data[0]
                address_details = result.get("address", {})

                return {
                    "latitude": float(result["lat"]),
                    "longitude": float(result["lon"]),
                    "full_address": full_address,
                    "street": street,
                    "city": address_details.get("city") or address_details.get("town") or city,
                    "state": address_details.get("state", state),
                    "zip": address_details.get("postcode", zip_code),
                    "county": address_details.get("county"),
                    "accuracy": "MEDIUM",
                    "source": "OpenStreetMap Nominatim"
                }
        except Exception as e:
            logger.debug(f"Nominatim geocoding failed: {str(e)}")

        return None

    def _try_zip_approximation(self, street: str, city: str, state: str,
                               zip_code: str, full_address: str) -> Optional[Dict]:
        """Approximate coordinates based on ZIP code"""
        # Clean ZIP code
        zip_clean = zip_code.split('-')[0].strip()

        if zip_clean in self.zip_coordinates:
            lat, lon = self.zip_coordinates[zip_clean]

            # Extract county from city name for Florida
            county = None
            if state.upper() == "FL":
                county = self._estimate_county_fl(city, zip_clean)

            return {
                "latitude": lat,
                "longitude": lon,
                "full_address": full_address,
                "street": street,
                "city": city,
                "state": state,
                "zip": zip_code,
                "county": county,
                "accuracy": "LOW",
                "source": "ZIP Code Approximation"
            }

        return None

    def _estimate_county_fl(self, city: str, zip_code: str = None) -> Optional[str]:
        """Estimate Florida county based on city name"""
        city_lower = city.lower()

        county_map = {
            "lehigh": "Lee County",
            "fort myers": "Lee County",
            "cape coral": "Lee County",
            "miami": "Miami-Dade County",
            "tampa": "Hillsborough County",
            "orlando": "Orange County",
            "jacksonville": "Duval County",
        }

        for key, county in county_map.items():
            if key in city_lower:
                return county

        return None

    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Reverse geocode coordinates to get address and county information
        """
        url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"

        params = {
            "x": longitude,
            "y": latitude,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json"
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("result", {}).get("geographies", {}).get("Counties"):
                county_info = data["result"]["geographies"]["Counties"][0]
                return {
                    "county": county_info.get("NAME"),
                    "state": county_info.get("STATE"),
                    "county_fips": county_info.get("GEOID")
                }

            return None

        except Exception as e:
            logger.error(f"Reverse geocoding error for ({latitude}, {longitude}): {str(e)}")
            return None
