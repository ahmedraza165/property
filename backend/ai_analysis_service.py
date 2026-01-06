import logging
import time
import json
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import requests
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """
    Service for AI-based property analysis using computer vision models.
    Supports road condition detection and power line detection from imagery.
    """

    def __init__(self):
        self.session = self._create_session()
        self.model_version = "v1.0"

        # Initialize AI models (lazy loading)
        self._road_model = None
        self._powerline_model = None
        self._development_model = None

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'PropertyAnalysis-AI/1.0'
        })
        return session

    def analyze_property(
        self,
        latitude: float,
        longitude: float,
        satellite_image_url: Optional[str],
        street_image_url: Optional[str]
    ) -> Dict[str, any]:
        """
        Perform comprehensive AI analysis on property imagery.

        Args:
            latitude: Property latitude
            longitude: Property longitude
            satellite_image_url: URL to satellite imagery
            street_image_url: URL to street-level imagery

        Returns:
            Dictionary with all AI analysis results
        """
        start_time = time.time()

        result = {
            "road_condition": None,
            "power_lines": None,
            "nearby_development": None,
            "overall_ai_risk": None,
            "processing_time_seconds": 0,
            "error": None
        }

        try:
            # Download images for analysis
            satellite_image = None
            street_image = None

            if satellite_image_url:
                satellite_image = self._download_image(satellite_image_url)

            if street_image_url:
                street_image = self._download_image(street_image_url)

            # Perform road condition analysis
            if satellite_image or street_image:
                result["road_condition"] = self._analyze_road_condition(
                    satellite_image, street_image
                )

            # Perform power line detection
            if satellite_image:
                result["power_lines"] = self._detect_power_lines(
                    satellite_image, latitude, longitude
                )

            # Detect nearby development
            if satellite_image:
                result["nearby_development"] = self._detect_nearby_development(
                    satellite_image
                )

            # Calculate overall AI risk
            result["overall_ai_risk"] = self._calculate_overall_ai_risk(
                result["road_condition"],
                result["power_lines"],
                result["nearby_development"]
            )

        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}", exc_info=True)
            result["error"] = str(e)

        result["processing_time_seconds"] = time.time() - start_time
        return result

    def _download_image(self, image_url: str) -> Optional[bytes]:
        """
        Download image from URL.

        Args:
            image_url: URL to download

        Returns:
            Image bytes or None
        """
        try:
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {str(e)}")
            return None

    def _analyze_road_condition(
        self,
        satellite_image: Optional[bytes],
        street_image: Optional[bytes]
    ) -> Dict[str, any]:
        """
        Analyze road condition from imagery using AI classification.

        Classification categories:
        - PAVED: Well-maintained paved road
        - DIRT: Unpaved/dirt road
        - GRAVEL: Gravel road
        - POOR: Paved but poor condition
        - UNKNOWN: Unable to determine

        Args:
            satellite_image: Satellite image bytes
            street_image: Street-level image bytes

        Returns:
            Road condition analysis result
        """
        # Prefer street image for road analysis, fallback to satellite
        image_to_analyze = street_image if street_image else satellite_image

        if not image_to_analyze:
            return {
                "type": "UNKNOWN",
                "confidence": 0.0,
                "source": "no_imagery",
                "details": "No imagery available for analysis"
            }

        try:
            # Use computer vision model for road classification
            # For production, this would call a trained model
            # For now, we'll use a mock implementation with OpenAI Vision API as fallback

            result = self._classify_road_with_ai(image_to_analyze)

            return result

        except Exception as e:
            logger.error(f"Road condition analysis failed: {str(e)}")
            return {
                "type": "UNKNOWN",
                "confidence": 0.0,
                "source": "error",
                "details": str(e)
            }

    def _classify_road_with_ai(self, image_bytes: bytes) -> Dict[str, any]:
        """
        Classify road condition using AI vision model.

        This method can be replaced with:
        1. Local PyTorch/TensorFlow model
        2. Cloud AI service (AWS Rekognition, Azure Computer Vision, etc.)
        3. OpenAI Vision API
        4. Custom-trained road classification model

        Args:
            image_bytes: Image data

        Returns:
            Classification result
        """
        import os

        # Try OpenAI Vision API if available
        openai_api_key = os.getenv('OPENAI_API_KEY')

        if openai_api_key:
            try:
                result = self._classify_with_openai_vision(image_bytes, "road")
                return result
            except Exception as e:
                logger.warning(f"OpenAI Vision API failed: {str(e)}")

        # Fallback to heuristic-based classification
        # In production, replace with actual ML model
        logger.info("Using heuristic road classification (no AI model configured)")

        return {
            "type": "PAVED",  # Default assumption
            "confidence": 0.3,  # Low confidence without AI
            "source": "heuristic",
            "details": "AI model not configured, using default classification"
        }

    def _detect_power_lines(
        self,
        satellite_image: bytes,
        latitude: float,
        longitude: float
    ) -> Dict[str, any]:
        """
        Detect power lines in satellite imagery using object detection.

        Args:
            satellite_image: Satellite image bytes
            latitude: Property latitude
            longitude: Property longitude

        Returns:
            Power line detection result with geometry
        """
        if not satellite_image:
            return {
                "visible": False,
                "confidence": 0.0,
                "distance_meters": None,
                "geometry": None,
                "source": "no_imagery"
            }

        try:
            # Use object detection model for power line identification
            result = self._detect_with_ai(satellite_image, "power_lines")

            # If power lines detected, extract geometry
            if result.get("visible", False):
                # Convert detection boxes to GeoJSON geometry
                geometry = self._detections_to_geojson(
                    result.get("detections", []),
                    latitude,
                    longitude
                )

                result["geometry"] = json.dumps(geometry) if geometry else None

            return result

        except Exception as e:
            logger.error(f"Power line detection failed: {str(e)}")
            return {
                "visible": False,
                "confidence": 0.0,
                "distance_meters": None,
                "geometry": None,
                "source": "error",
                "error": str(e)
            }

    def _detect_with_ai(
        self,
        image_bytes: bytes,
        detection_type: str
    ) -> Dict[str, any]:
        """
        Perform object detection using AI model.

        Args:
            image_bytes: Image data
            detection_type: Type of detection ('power_lines', 'development')

        Returns:
            Detection result
        """
        import os

        openai_api_key = os.getenv('OPENAI_API_KEY')

        if openai_api_key:
            try:
                if detection_type == "power_lines":
                    return self._detect_powerlines_with_openai(image_bytes)
                elif detection_type == "development":
                    return self._detect_development_with_openai(image_bytes)
            except Exception as e:
                logger.warning(f"OpenAI detection failed: {str(e)}")

        # Fallback to basic detection
        logger.info(f"Using heuristic {detection_type} detection (no AI model configured)")

        if detection_type == "power_lines":
            return {
                "visible": False,
                "confidence": 0.1,
                "distance_meters": None,
                "detections": [],
                "source": "heuristic"
            }
        elif detection_type == "development":
            return {
                "type": "UNKNOWN",
                "count": 0,
                "confidence": 0.1,
                "source": "heuristic"
            }

    def _classify_with_openai_vision(
        self,
        image_bytes: bytes,
        classification_type: str
    ) -> Dict[str, any]:
        """
        Use OpenAI Vision API for image classification.

        Args:
            image_bytes: Image data
            classification_type: 'road' or other type

        Returns:
            Classification result
        """
        import os

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")

        # Encode image to base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        if classification_type == "road":
            prompt = """Analyze this image and classify the road condition.
            Respond with ONLY a JSON object in this exact format:
            {"type": "PAVED|DIRT|GRAVEL|POOR|UNKNOWN", "confidence": 0.0-1.0, "details": "brief description"}

            Classification guide:
            - PAVED: Well-maintained asphalt or concrete road
            - DIRT: Unpaved dirt road
            - GRAVEL: Gravel surface
            - POOR: Paved but with significant damage/deterioration
            - UNKNOWN: Cannot determine from image
            """
        else:
            prompt = "Analyze this property image and describe what you see."

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }

        response = self.session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        content = result['choices'][0]['message']['content']

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            parsed["source"] = "openai_vision"
            return parsed
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse OpenAI response as JSON: {content}")
            return {
                "type": "UNKNOWN",
                "confidence": 0.0,
                "source": "openai_vision",
                "details": content
            }

    def _detect_powerlines_with_openai(self, image_bytes: bytes) -> Dict[str, any]:
        """Detect power lines using OpenAI Vision API."""
        import os

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")

        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        prompt = """Analyze this satellite image for power lines and electrical infrastructure.
        Respond with ONLY a JSON object in this exact format:
        {"visible": true/false, "confidence": 0.0-1.0, "distance_meters": number or null, "details": "description"}

        Guidelines:
        - Look for power lines, transmission towers, electrical poles
        - Estimate distance from center of image if visible
        - Confidence should reflect certainty of detection
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }

        response = self.session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        content = result['choices'][0]['message']['content']

        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            parsed["source"] = "openai_vision"
            parsed["detections"] = []  # Would contain bounding boxes from detection model
            return parsed
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse OpenAI powerline response: {content}")
            return {
                "visible": False,
                "confidence": 0.0,
                "distance_meters": None,
                "detections": [],
                "source": "openai_vision"
            }

    def _detect_development_with_openai(self, image_bytes: bytes) -> Dict[str, any]:
        """Detect nearby development using OpenAI Vision API."""
        import os

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")

        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        prompt = """Analyze this satellite image for nearby development and structures.
        Respond with ONLY a JSON object in this exact format:
        {"type": "RESIDENTIAL|COMMERCIAL|INDUSTRIAL|AGRICULTURAL|UNDEVELOPED", "count": number, "confidence": 0.0-1.0, "details": "description"}

        Guidelines:
        - Identify dominant development type in the area
        - Count visible structures/buildings
        - Provide confidence in assessment
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }

        response = self.session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        content = result['choices'][0]['message']['content']

        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            parsed["source"] = "openai_vision"
            return parsed
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse OpenAI development response: {content}")
            return {
                "type": "UNKNOWN",
                "count": 0,
                "confidence": 0.0,
                "source": "openai_vision"
            }

    def _detect_nearby_development(self, satellite_image: bytes) -> Dict[str, any]:
        """
        Detect nearby development from satellite imagery.

        Args:
            satellite_image: Satellite image bytes

        Returns:
            Development detection result
        """
        if not satellite_image:
            return {
                "type": "UNKNOWN",
                "count": 0,
                "confidence": 0.0,
                "source": "no_imagery"
            }

        try:
            result = self._detect_with_ai(satellite_image, "development")
            return result
        except Exception as e:
            logger.error(f"Development detection failed: {str(e)}")
            return {
                "type": "UNKNOWN",
                "count": 0,
                "confidence": 0.0,
                "source": "error",
                "error": str(e)
            }

    def _detections_to_geojson(
        self,
        detections: List[Dict],
        center_lat: float,
        center_lon: float
    ) -> Optional[Dict]:
        """
        Convert detection bounding boxes to GeoJSON geometry.

        Args:
            detections: List of detection dictionaries with bounding boxes
            center_lat: Center latitude of image
            center_lon: Center longitude of image

        Returns:
            GeoJSON FeatureCollection or None
        """
        if not detections:
            return None

        features = []

        for detection in detections:
            # Each detection should have: bbox, confidence, class
            bbox = detection.get('bbox')
            if not bbox:
                continue

            # Convert pixel coordinates to lat/lon (approximate)
            # This is a simplified conversion; in production, use proper projection
            x1, y1, x2, y2 = bbox

            # Approximate meters per pixel at this latitude
            meters_per_pixel = 0.3  # Depends on zoom level and latitude

            # Convert to offset in degrees
            lon1 = center_lon + ((x1 - 400) * meters_per_pixel / 111320)
            lat1 = center_lat - ((y1 - 300) * meters_per_pixel / 110540)
            lon2 = center_lon + ((x2 - 400) * meters_per_pixel / 111320)
            lat2 = center_lat - ((y2 - 300) * meters_per_pixel / 110540)

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [lon1, lat1],
                        [lon2, lat1],
                        [lon2, lat2],
                        [lon1, lat2],
                        [lon1, lat1]
                    ]]
                },
                "properties": {
                    "confidence": detection.get('confidence', 0.0),
                    "class": detection.get('class', 'power_line')
                }
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features
        }

    def _calculate_overall_ai_risk(
        self,
        road_condition: Optional[Dict],
        power_lines: Optional[Dict],
        nearby_development: Optional[Dict]
    ) -> Dict[str, any]:
        """
        Calculate overall AI-based risk assessment.

        Risk factors:
        - Poor road condition: Increases risk
        - Power lines nearby: Moderate risk
        - Lack of development: May indicate remote/difficult access

        Args:
            road_condition: Road condition analysis
            power_lines: Power line detection
            nearby_development: Development detection

        Returns:
            Overall risk assessment
        """
        risk_score = 0.0
        confidence_scores = []
        risk_factors = []

        # Road condition risk
        if road_condition:
            road_type = road_condition.get('type', 'UNKNOWN')
            road_conf = road_condition.get('confidence', 0.0)

            if road_type == 'DIRT':
                risk_score += 30
                risk_factors.append('Unpaved road access')
            elif road_type == 'GRAVEL':
                risk_score += 20
                risk_factors.append('Gravel road access')
            elif road_type == 'POOR':
                risk_score += 25
                risk_factors.append('Poor road condition')

            confidence_scores.append(road_conf)

        # Power lines risk
        if power_lines and power_lines.get('visible', False):
            pl_conf = power_lines.get('confidence', 0.0)
            distance = power_lines.get('distance_meters')

            if distance and distance < 50:
                risk_score += 25
                risk_factors.append('Power lines very close')
            elif distance and distance < 100:
                risk_score += 15
                risk_factors.append('Power lines nearby')
            else:
                risk_score += 10
                risk_factors.append('Power lines visible')

            confidence_scores.append(pl_conf)

        # Development risk (isolation)
        if nearby_development:
            dev_type = nearby_development.get('type', 'UNKNOWN')
            dev_count = nearby_development.get('count', 0)
            dev_conf = nearby_development.get('confidence', 0.0)

            if dev_type == 'UNDEVELOPED' or dev_count == 0:
                risk_score += 20
                risk_factors.append('Remote/undeveloped area')
            elif dev_type == 'INDUSTRIAL':
                risk_score += 15
                risk_factors.append('Industrial area')

            confidence_scores.append(dev_conf)

        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        # Determine risk level
        if risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "level": risk_level,
            "score": risk_score,
            "confidence": overall_confidence,
            "factors": risk_factors
        }

    def check_and_determine_road_access_override(
        self,
        road_condition: Optional[Dict],
        gis_road_access: bool,
        gis_road_distance: float
    ) -> Dict[str, any]:
        """
        Determine if AI analysis should override GIS road access results.

        If AI detects poor/no road from imagery but GIS says there's access,
        or vice versa, determine which source to trust based on confidence.

        Args:
            road_condition: AI road condition analysis
            gis_road_access: GIS-detected road access (True/False)
            gis_road_distance: Distance to nearest road in meters

        Returns:
            Dict with override decision and updated values
        """
        should_override = False
        new_road_access = gis_road_access
        new_road_distance = gis_road_distance
        override_reason = None

        if not road_condition:
            return {
                "should_override": False,
                "new_road_access": gis_road_access,
                "new_road_distance": gis_road_distance,
                "reason": "No AI road analysis available"
            }

        road_type = road_condition.get('type', 'UNKNOWN')
        confidence = road_condition.get('confidence', 0.0)

        # High confidence AI detection should override low-confidence GIS
        if confidence >= 0.6:  # AI is confident
            # AI sees DIRT/GRAVEL but GIS says no access - AI is seeing unpaved road
            if road_type in ['DIRT', 'GRAVEL'] and not gis_road_access:
                should_override = True
                new_road_access = True
                new_road_distance = 50  # Estimate close proximity
                override_reason = f"AI detected {road_type} road (confidence: {confidence:.2f}) but GIS found no road access. Updated to reflect unpaved road access."

            # AI sees PAVED road but GIS says no access - GIS likely missed it
            elif road_type == 'PAVED' and not gis_road_access:
                should_override = True
                new_road_access = True
                new_road_distance = 30  # Close proximity assumed
                override_reason = f"AI detected PAVED road (confidence: {confidence:.2f}) but GIS found no road access. Updated to reflect road access."

            # AI sees no road/unknown but GIS says there's close access - trust GIS for now
            # (GIS is more accurate for geographic road network data)
            elif road_type == 'UNKNOWN' and gis_road_access and gis_road_distance > 100:
                # If GIS says road is far and AI can't see it, might be landlocked
                should_override = True
                new_road_access = False
                new_road_distance = gis_road_distance
                override_reason = f"AI cannot confirm road access and GIS shows road is {gis_road_distance:.0f}m away. Updated to no direct access."

        return {
            "should_override": should_override,
            "new_road_access": new_road_access,
            "new_road_distance": new_road_distance,
            "reason": override_reason
        }
