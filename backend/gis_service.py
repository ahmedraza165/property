import os
import requests
import urllib3
import time
import warnings
from typing import Dict, Optional, Tuple
from math import radians, sin, cos, sqrt, atan2
import logging

logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', category=Warning)


class GISRiskService:
    """
    GIS-based risk analysis service
    Integrates multiple public GIS datasets to assess property risks

    Note: Many government APIs may be blocked by network restrictions.
    This version includes fallback methods and alternative data sources.
    """

    def __init__(self):
        """Initialize GIS service"""
        self.session = self._create_session()

        # Known flood-prone regions in Florida (for fallback)
        self.florida_high_flood_counties = [
            'miami-dade', 'broward', 'monroe', 'collier', 'lee',
            'charlotte', 'manatee', 'pinellas', 'hillsborough'
        ]

        # County Property Appraiser URLs for legal descriptions
        self.county_appraiser_apis = {
            'lee': 'https://www.leepa.org/Search/PropertySearch.aspx',
            'collier': 'https://www.collierappraiser.com/',
            'charlotte': 'https://www.ccappraiser.com/',
        }

    def _create_session(self):
        """Create a requests session with retry logic and SSL configuration"""
        import ssl
        from requests.adapters import HTTPAdapter
        from urllib3.util.ssl_ import create_urllib3_context

        session = requests.Session()
        session.headers.update({
            'User-Agent': 'PropertyRiskAnalysis/2.0'
        })

        # Custom SSL context for government APIs (FEMA requires TLS 1.2+)
        class SSLAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                context = create_urllib3_context()
                context.load_default_certs()
                context.set_ciphers('DEFAULT@SECLEVEL=1')
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                kwargs['ssl_context'] = context
                return super().init_poolmanager(*args, **kwargs)

        session.mount('https://', SSLAdapter())
        return session

    def analyze_property(self, latitude: float, longitude: float,
                        address: str = None, city: str = None,
                        state: str = None) -> Dict:
        """
        Comprehensive property risk analysis

        Args:
            latitude: Property latitude
            longitude: Property longitude
            address: Optional street address
            city: Optional city name
            state: Optional state code

        Returns:
            Dict containing all risk assessments
        """
        start_time = time.time()

        try:
            # Run all analyses
            wetlands = self.check_wetlands(latitude, longitude, state)
            flood_zone = self.check_flood_zone(latitude, longitude, city, state)
            slope = self.check_slope(latitude, longitude, state)
            road_access = self.check_road_access(latitude, longitude)
            # CRITICAL: landlocked is simply the inverse of road_access
            # If has_access=True, then landlocked=False, and vice versa
            landlocked = not road_access.get("has_access", True)
            protected_land = self.check_protected_land(latitude, longitude)

            # Calculate overall risk
            overall_risk = self._calculate_overall_risk(
                wetlands, flood_zone, slope, road_access, landlocked, protected_land
            )

            processing_time = time.time() - start_time

            return {
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "address": address,
                    "city": city,
                    "state": state
                },
                "wetlands": wetlands,
                "flood_zone": flood_zone,
                "slope": slope,
                "road_access": road_access,
                "landlocked": landlocked,
                "protected_land": protected_land,
                "overall_risk": overall_risk,
                "processing_time_seconds": round(processing_time, 2),
                "error": None
            }

        except Exception as e:
            logger.error(f"Error in property analysis: {str(e)}")
            processing_time = time.time() - start_time
            return {
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "address": address
                },
                "wetlands": {"status": False, "confidence": "LOW", "source": "Error"},
                "flood_zone": {"zone": "Unknown", "severity": "UNKNOWN", "source": "Error"},
                "slope": {"percentage": 0, "severity": "UNKNOWN", "source": "Error"},
                "road_access": {"has_access": False, "distance_meters": 0, "source": "Error"},
                "landlocked": False,
                "protected_land": {"is_protected": False, "type": None, "source": "Error"},
                "overall_risk": "UNKNOWN",
                "processing_time_seconds": round(processing_time, 2),
                "error": str(e)
            }

    def check_wetlands(self, latitude: float, longitude: float,
                      state: str = None) -> Dict:
        """
        Check if property is in or near wetlands

        Primary: ESRI Living Atlas USA Wetlands (most reliable free API)
        Fallback: USFWS NWI Direct
        Final fallback: Geographic heuristics for Florida
        """
        # Try ESRI Living Atlas USA Wetlands (RECOMMENDED - No API key required)
        try:
            url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Wetlands/FeatureServer/0/query"

            params = {
                "geometry": f'{{"x":{longitude},"y":{latitude},"spatialReference":{{"wkid":4326}}}}',
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "WETLAND_TYPE",
                "returnGeometry": "false",
                "f": "json"
            }

            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                logger.debug(f"ESRI Wetlands response: {data}")
                if data.get("features") and len(data["features"]) > 0:
                    wetland_type = data["features"][0]["attributes"].get("WETLAND_TYPE", "Unknown")
                    return {
                        "status": True,
                        "type": wetland_type,
                        "confidence": "HIGH",
                        "source": "ESRI Living Atlas (USFWS NWI)"
                    }
                else:
                    return {
                        "status": False,
                        "confidence": "HIGH",
                        "source": "ESRI Living Atlas (USFWS NWI)"
                    }
        except Exception as e:
            logger.warning(f"ESRI Living Atlas API error: {str(e)}")

        # Try USFWS Direct API (alternative)
        try:
            url = "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/0/query"

            params = {
                "geometry": f'{{"x":{longitude},"y":{latitude},"spatialReference":{{"wkid":4326}}}}',
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "WETLAND_TYPE,ATTRIBUTE",
                "returnGeometry": "false",
                "f": "json"
            }

            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                logger.debug(f"USFWS Direct response: {data}")
                if data.get("features") and len(data["features"]) > 0:
                    return {
                        "status": True,
                        "type": data["features"][0]["attributes"].get("WETLAND_TYPE", "Unknown"),
                        "confidence": "HIGH",
                        "source": "USFWS NWI Direct"
                    }
                else:
                    return {
                        "status": False,
                        "confidence": "HIGH",
                        "source": "USFWS NWI Direct"
                    }
        except Exception as e:
            logger.debug(f"USFWS Direct API error: {str(e)}")
        
        # Fallback: Geographic analysis for Florida
        if state and state.upper() == "FL":
            # Florida-specific heuristics
            # Southwest Florida (including Lehigh Acres) has wetlands concerns
            if 26.0 <= latitude <= 27.5 and -82.0 <= longitude <= -81.0:
                return {
                    "status": True,
                    "confidence": "MEDIUM",
                    "source": "Geographic heuristic (SW Florida wetlands zone)",
                    "note": "Area known for wetlands. Verify with local survey."
                }
        
        return {
            "status": False,
            "confidence": "LOW",
            "source": "Unable to verify (API unavailable)"
        }

    def check_flood_zone(self, latitude: float, longitude: float,
                         city: str = None, state: str = None) -> Dict:
        """
        Check FEMA flood zone with improved accuracy

        Tries multiple FEMA APIs in order:
        1. ESRI Living Atlas FEMA Flood Hazards (Most reliable)
        2. FEMA NFHL (National Flood Hazard Layer) - Official source
        3. FEMA MSC (Map Service Center) - Alternative source
        4. Geographic heuristics - Fallback
        """
        api_results = []

        # Try ESRI Living Atlas FEMA Flood Hazards (more reliable than direct FEMA API)
        try:
            # This ESRI endpoint mirrors FEMA data but has better reliability
            url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_Flood_Hazard_Reduced_Set_gdb/FeatureServer/0/query"

            params = {
                "geometry": f'{{"x":{longitude},"y":{latitude},"spatialReference":{{"wkid":4326}}}}',
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF",
                "returnGeometry": "false",
                "f": "json"
            }

            response = self.session.get(url, params=params, timeout=20)
            logger.debug(f"ESRI FEMA Flood request: {url}")

            if response.status_code == 200:
                data = response.json()
                logger.debug(f"ESRI FEMA Flood response: {data}")

                if data.get("features") and len(data["features"]) > 0:
                    feature = data["features"][0]
                    attrs = feature["attributes"]
                    zone = attrs.get("FLD_ZONE", "X").strip() if attrs.get("FLD_ZONE") else "X"
                    zone_subty = attrs.get("ZONE_SUBTY", "").strip() if attrs.get("ZONE_SUBTY") else ""
                    sfha = attrs.get("SFHA_TF", "F")

                    # Combine zone and subtype for more detail
                    if zone_subty and zone_subty != "":
                        full_zone = f"{zone} ({zone_subty})"
                    else:
                        full_zone = zone

                    severity = self._classify_flood_zone(zone, sfha)

                    logger.info(f"ESRI FEMA Flood returned zone: {full_zone}, SFHA: {sfha}")

                    return {
                        "zone": full_zone,
                        "severity": severity,
                        "in_sfha": sfha == "T",
                        "confidence": "HIGH",
                        "source": "ESRI Living Atlas (FEMA Data)"
                    }
                else:
                    logger.debug(f"ESRI FEMA returned no features for {latitude}, {longitude}")
                    api_results.append(("ESRI_FEMA", "no_data"))
        except Exception as e:
            logger.warning(f"ESRI FEMA Flood API error: {str(e)}")
            api_results.append(("ESRI_FEMA", f"error: {str(e)}"))
        
        # Alternative FEMA endpoint
        try:
            url = "https://msc.fema.gov/arcgis/rest/services/public/NFHLWMS/MapServer/identify"
            
            params = {
                "geometry": f"{longitude},{latitude}",
                "geometryType": "esriGeometryPoint",
                "sr": "4326",
                "layers": "all",
                "tolerance": "1",
                "mapExtent": f"{longitude-0.01},{latitude-0.01},{longitude+0.01},{latitude+0.01}",
                "imageDisplay": "400,400,96",
                "returnGeometry": "false",
                "f": "json"
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    # Parse flood zone from results
                    for result in data["results"]:
                        if "FLD_ZONE" in result.get("attributes", {}):
                            zone = result["attributes"]["FLD_ZONE"]
                            severity = self._classify_flood_zone(zone)
                            return {
                                "zone": zone,
                                "severity": severity,
                                "confidence": "HIGH",
                                "source": "FEMA MSC"
                            }
        except Exception as e:
            logger.debug(f"FEMA MSC API error: {str(e)}")
        
        # Try FEMA Flood Map Service Center (alternative endpoint)
        try:
            url = "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query"

            # Try with a slightly larger buffer to catch nearby zones
            params = {
                "geometry": f"{longitude},{latitude}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "outSR": "4326",
                "spatialRel": "esriSpatialRelWithin",
                "distance": "10",
                "units": "esriSRUnit_Meter",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json"
            }

            response = self.session.get(url, params=params, timeout=20)

            if response.status_code == 200:
                data = response.json()
                if data.get("features") and len(data["features"]) > 0:
                    feature = data["features"][0]
                    attrs = feature["attributes"]
                    zone = attrs.get("FLD_ZONE", "X").strip()
                    zone_subty = attrs.get("ZONE_SUBTY", "").strip()
                    sfha = attrs.get("SFHA_TF", "F")

                    # Combine zone and subtype
                    if zone_subty:
                        full_zone = f"{zone} ({zone_subty})"
                    else:
                        full_zone = zone

                    severity = self._classify_flood_zone(zone, sfha)

                    logger.info(f"FEMA NFHL (buffered) returned zone: {full_zone}, SFHA: {sfha}")

                    return {
                        "zone": full_zone,
                        "severity": severity,
                        "in_sfha": sfha == "T",
                        "confidence": "HIGH",
                        "source": "FEMA NFHL"
                    }
        except Exception as e:
            logger.debug(f"FEMA NFHL buffered query error: {str(e)}")

        # Fallback: Geographic risk assessment for Florida - IMPROVED
        if state and state.upper() == "FL":
            city_lower = city.lower() if city else ""

            # Check if in high-risk coastal or known flood areas
            if any(county in city_lower for county in self.florida_high_flood_counties):
                return {
                    "zone": "A (estimated)",
                    "severity": "HIGH",
                    "confidence": "LOW",
                    "source": "Geographic estimate (coastal area)",
                    "note": "FEMA data unavailable - verify with official flood map"
                }

            # For inland Florida areas (including Lehigh Acres)
            # Most inland SW Florida is genuinely Zone X (minimal flood risk)
            return {
                "zone": "X",
                "severity": "LOW",
                "confidence": "LOW",
                "source": "Geographic estimate (inland FL)",
                "note": "FEMA data unavailable - individual properties may vary"
            }

        # Default for unknown areas
        return {
            "zone": "X",
            "severity": "LOW",
            "confidence": "LOW",
            "source": "Data unavailable",
            "note": "Unable to verify flood zone - recommend official FEMA map check"
        }

    def _classify_flood_zone(self, zone: str, sfha: str = None) -> str:
        """
        Classify flood zone severity with improved accuracy.

        HIGH RISK zones (Insurance required):
        - A, AE, AH, AO, A99, AR - 100-year floodplain
        - V, VE, V1-30 - Coastal high-hazard areas

        MEDIUM RISK zones:
        - B, X500, X-SHADED - 500-year floodplain (0.2% annual chance)

        LOW RISK zones:
        - X, X-UNSHADED, C - Minimal flood risk
        """
        zone = zone.upper() if zone else "X"

        # High risk zones (100-year floodplain)
        high_risk = ["AE", "AH", "AO", "A99", "AR", "VE"]
        high_risk_prefixes = ["A ", "V"]

        # Medium risk zones (500-year floodplain)
        moderate_risk = ["B", "X500", "X-SHADED", "SHADED", "0.2 PCT ANNUAL CHANCE"]

        # Check if in SFHA (Special Flood Hazard Area)
        if sfha == "T":
            return "HIGH"

        # Check exact matches for high risk
        if zone in high_risk:
            return "HIGH"

        # Check if zone starts with high-risk prefix (e.g., "A ", "V")
        for prefix in high_risk_prefixes:
            if zone.startswith(prefix):
                return "HIGH"

        # Check for moderate risk
        if zone in moderate_risk:
            return "MEDIUM"

        # Check if zone contains moderate risk indicators
        if "SHADED" in zone or "X500" in zone or "0.2" in zone:
            return "MEDIUM"

        # Default to LOW for X, C, or unknown zones
        return "LOW"

    def check_slope(self, latitude: float, longitude: float, 
                   state: str = None) -> Dict:
        """
        Check terrain slope
        
        Primary: USGS Elevation Point Query Service
        Alternative: Open-Elevation API
        Fallback: State-based terrain estimates
        """
        # Try USGS Elevation API
        try:
            url = "https://epqs.nationalmap.gov/v1/json"
            
            elevations = []
            offset = 0.0001  # ~10 meters
            
            points = [
                (latitude, longitude),
                (latitude + offset, longitude),
                (latitude, longitude + offset),
            ]
            
            for lat, lon in points:
                params = {
                    "x": lon,
                    "y": lat,
                    "units": "Meters",
                    "output": "json"
                }
                
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    elev = data.get("value")
                    if elev is not None and elev != -1000000:
                        elevations.append(float(elev))
            
            if len(elevations) >= 2:
                elevation_change = abs(max(elevations) - min(elevations))
                distance = offset * 111000
                slope_percentage = (elevation_change / distance) * 100
                
                severity = self._classify_slope(slope_percentage)
                
                return {
                    "percentage": round(slope_percentage, 2),
                    "severity": severity,
                    "confidence": "HIGH",
                    "source": "USGS Elevation API"
                }
        except Exception as e:
            logger.debug(f"USGS API error: {str(e)}")
        
        # Try Open-Elevation API (open source alternative)
        try:
            url = "https://api.open-elevation.com/api/v1/lookup"
            
            locations = [
                {"latitude": latitude, "longitude": longitude},
                {"latitude": latitude + 0.0001, "longitude": longitude},
                {"latitude": latitude, "longitude": longitude + 0.0001}
            ]
            
            response = self.session.post(url, json={"locations": locations}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                elevations = [r["elevation"] for r in data.get("results", [])]
                
                if len(elevations) >= 2:
                    elevation_change = abs(max(elevations) - min(elevations))
                    distance = 0.0001 * 111000
                    slope_percentage = (elevation_change / distance) * 100
                    
                    severity = self._classify_slope(slope_percentage)
                    
                    return {
                        "percentage": round(slope_percentage, 2),
                        "severity": severity,
                        "confidence": "HIGH",
                        "source": "Open-Elevation API"
                    }
        except Exception as e:
            logger.debug(f"Open-Elevation API error: {str(e)}")
        
        # Fallback: State-based terrain estimates
        if state and state.upper() == "FL":
            return {
                "percentage": 0.5,
                "severity": "LOW",
                "confidence": "MEDIUM",
                "source": "Geographic estimate (Florida is generally flat)",
                "note": "Florida terrain is typically 0-2% slope"
            }
        
        return {
            "percentage": 0,
            "severity": "UNKNOWN",
            "confidence": "LOW",
            "source": "Unable to calculate (API unavailable)"
        }

    def _classify_slope(self, percentage: float) -> str:
        """Classify slope severity"""
        if percentage > 15:
            return "HIGH"
        elif percentage > 8:
            return "MEDIUM"
        else:
            return "LOW"

    def check_road_access(self, latitude: float, longitude: float,
                          distance_threshold: int = 200) -> Dict:
        """
        Check road access
        
        Primary: OpenStreetMap Overpass API
        Fallback: Assume access exists (most properties have road access)
        """
        # Try Overpass API (OpenStreetMap)
        try:
            url = "https://overpass-api.de/api/interpreter"
            
            # Query for roads within 200m
            query = f"""
            [out:json][timeout:10];
            (
              way["highway"](around:200,{latitude},{longitude});
            );
            out center;
            """
            
            response = self.session.post(url, data=query, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                elements = data.get("elements", [])
                
                if elements:
                    # Calculate distance to nearest road
                    min_distance = float('inf')
                    
                    for element in elements:
                        if 'center' in element:
                            road_lat = element['center']['lat']
                            road_lon = element['center']['lon']
                        elif 'lat' in element and 'lon' in element:
                            road_lat = element['lat']
                            road_lon = element['lon']
                        else:
                            continue
                        
                        distance = self._haversine_distance(
                            latitude, longitude, road_lat, road_lon
                        )
                        min_distance = min(min_distance, distance)
                    
                    if min_distance != float('inf'):
                        has_access = min_distance <= distance_threshold
                        
                        return {
                            "has_access": has_access,
                            "distance_meters": round(min_distance, 2),
                            "confidence": "HIGH",
                            "source": "OpenStreetMap (Overpass API)"
                        }
        except Exception as e:
            logger.debug(f"Overpass API error: {str(e)}")
        
        # Fallback: Assume road access (most properties have it)
        return {
            "has_access": True,
            "distance_meters": 0,
            "confidence": "LOW",
            "source": "Assumed accessible (verification unavailable)",
            "note": "Unable to verify. Most developed properties have road access."
        }

    def _haversine_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371000  # Earth radius in meters
        
        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c

    def check_landlocked(self, latitude: float, longitude: float) -> bool:
        """Check if property is landlocked (no road access)"""
        try:
            road_access = self.check_road_access(latitude, longitude, distance_threshold=200)
            return not road_access.get("has_access", True)
        except Exception as e:
            logger.error(f"Landlocked check error: {str(e)}")
            return False

    def check_protected_land(self, latitude: float, longitude: float) -> Dict:
        """
        Check if property is on protected/conservation land
        
        Primary: PAD-US (Protected Areas Database) API
        Fallback: Return not protected with low confidence
        """
        # Try PAD-US API
        try:
            url = "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services/Protected_Areas_Database_US_PAD_US3_0/FeatureServer/0/query"
            
            params = {
                "geometry": f"{longitude},{latitude}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "Category,Mang_Name,Unit_Nm",
                "returnGeometry": "false",
                "f": "json"
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("features"):
                    feature = data["features"][0]
                    attrs = feature["attributes"]
                    
                    return {
                        "is_protected": True,
                        "type": attrs.get("Category", "Unknown"),
                        "manager": attrs.get("Mang_Name", "Unknown"),
                        "name": attrs.get("Unit_Nm", ""),
                        "confidence": "HIGH",
                        "source": "PAD-US"
                    }
                else:
                    return {
                        "is_protected": False,
                        "type": None,
                        "confidence": "HIGH",
                        "source": "PAD-US"
                    }
        except Exception as e:
            logger.debug(f"PAD-US API error: {str(e)}")
        
        # Fallback
        return {
            "is_protected": False,
            "type": None,
            "confidence": "LOW",
            "source": "Unable to verify (API unavailable)"
        }

    def _calculate_overall_risk(self, wetlands, flood_zone, slope,
                                road_access, landlocked, protected_land) -> str:
        """
        Calculate overall property risk level

        CRITICAL RULES:
        1. HIGH flood zone = HIGH risk (immediate disqualifier)
        2. Landlocked property = HIGH risk (immediate disqualifier)
        3. If has_access=True, then landlocked MUST be False

        Returns: "LOW", "MEDIUM", "HIGH", or "UNKNOWN"
        """
        risk_score = 0
        confidence_penalties = 0

        # CRITICAL: HIGH flood zone automatically makes property HIGH risk
        flood_severity = flood_zone.get("severity", "LOW")
        if flood_severity == "HIGH":
            logger.info("⚠️  HIGH FLOOD ZONE detected - Setting risk to HIGH")
            return "HIGH"

        # CRITICAL: Landlocked property automatically makes it HIGH risk
        # Landlocked means NO road access - property is inaccessible
        if landlocked or not road_access.get("has_access", True):
            logger.info("⚠️  LANDLOCKED property (no road access) - Setting risk to HIGH")
            return "HIGH"

        # If property has road access, it CANNOT be landlocked
        if road_access.get("has_access", True) and landlocked:
            logger.warning("⚠️  Inconsistency: Property has road access but marked landlocked. Correcting landlocked to False.")
            landlocked = False

        # Wetlands (+2 if present)
        if wetlands.get("status"):
            risk_score += 2
        if wetlands.get("confidence") != "HIGH":
            confidence_penalties += 1

        # Flood zone (0-2 points) - HIGH already handled above
        if flood_severity == "MEDIUM":
            risk_score += 2
        elif flood_severity == "UNKNOWN":
            confidence_penalties += 1

        if flood_zone.get("confidence") != "HIGH":
            confidence_penalties += 1

        # Slope (0-2 points)
        slope_severity = slope.get("severity", "LOW")
        if slope_severity == "HIGH":
            risk_score += 2
        elif slope_severity == "MEDIUM":
            risk_score += 1
        elif slope_severity == "UNKNOWN":
            confidence_penalties += 1

        # Protected land (+2 if protected)
        if protected_land.get("is_protected"):
            risk_score += 2

        # If too many unknowns, return UNKNOWN
        if confidence_penalties >= 3:
            return "UNKNOWN"

        # Classify overall risk
        if risk_score >= 5:
            return "HIGH"
        elif risk_score >= 3:
            return "MEDIUM"
        else:
            return "LOW"


def analyze_address(address: str, city: str = None, state: str = None,
                   zip_code: str = None) -> Dict:
    """
    Convenience function to analyze a property by address
    
    Args:
        address: Street address
        city: City name
        state: State code (e.g., 'FL')
        zip_code: ZIP code
    
    Returns:
        Property risk analysis dict
    """
    # For demonstration, use approximate coordinates for Lehigh Acres, FL
    # In production, use a geocoding service
    
    if city and "lehigh" in city.lower():
        # Approximate center of Lehigh Acres
        lat, lon = 26.6254, -81.6437
    else:
        # Default to provided coordinates or estimate
        lat, lon = 26.6254, -81.6437
    
    service = GISRiskService()
    full_address = f"{address}, {city}, {state} {zip_code}" if all([address, city, state, zip_code]) else address
    
    return service.analyze_property(
        latitude=lat,
        longitude=lon,
        address=full_address,
        city=city,
        state=state
    )