"""
Improved AI Analysis with better power line detection and rate limiting.

This module provides enhanced image analysis focusing on:
1. Power line detection (TOP PRIORITY)
2. Structure detection (buildings, houses, garages)
3. Property condition assessment
4. Road condition analysis
"""

import logging
import time
import json
import base64
import requests
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)


def detect_power_lines_enhanced(image_bytes: bytes, image_type: str = "satellite") -> Dict:
    """
    Enhanced power line detection with multiple strategies and comprehensive debugging.

    Args:
        image_bytes: Image data
        image_type: "satellite" or "street"

    Returns:
        Detection result with high accuracy
    """
    logger.info("="*70)
    logger.info(f"🔍 ENHANCED POWER LINE DETECTION - Image Type: {image_type.upper()}")
    logger.info("="*70)

    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        logger.error("❌ No OpenAI API key found in environment")
        logger.warning("⚠️  Returning default negative result")
        return {
            "visible": False,
            "confidence": 0.0,
            "source": "no_api_key"
        }

    logger.debug(f"✓ API key found (length: {len(api_key)})")
    logger.debug(f"📊 Image size: {len(image_bytes)} bytes")

    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    logger.debug(f"📤 Base64 encoded: {len(image_b64)} characters")

    if image_type == "satellite":
        prompt = """You are an expert property analyst examining satellite imagery for power lines and electrical infrastructure.

🎯 **IMPORTANT: This image has a RED MARKER showing the TARGET PROPERTY**

Your task: Detect power lines and measure distance FROM THE RED MARKER to nearest power lines.

🔍 WHAT TO LOOK FOR:

1. **Power Line Shadows**: Thin parallel shadows on ground
2. **Transmission Towers**: Metal lattice structures (crosses/H-shapes)
3. **Power Line Corridors**: Straight cleared paths through trees
4. **Utility Poles**: Small dots in line patterns
5. **Thin Lines**: Gray/black cables crossing the image
6. **Transformer Stations**: Small fenced areas

📏 CRITICAL - DISTANCE FROM RED MARKER:
- Measure distance FROM RED MARKER to nearest power lines
- Estimate in meters: 20m, 50m, 100m, 150m, 200m+
- Be as accurate as possible

🔍 SCAN STRATEGY:
- Check all four corners and edges
- Look for thin straight/curved lines
- Look for shadows cast by lines
- Power lines often parallel roads

Respond ONLY with JSON:
{
    "visible": true or false,
    "confidence": 0.0 to 1.0,
    "distance_meters": distance from RED MARKER to nearest power line (REQUIRED if visible),
    "details": "EXACT location relative to RED MARKER (e.g., '150m north of marker along road', 'transmission lines 200m east')"
}

CRITICAL: If power lines visible, MUST provide distance from RED MARKER!"""

    else:  # street view
        prompt = """You are an expert at detecting power lines in street-level photography.

CRITICAL TASK: Look at this street view image for power lines and utility infrastructure.

WHAT TO LOOK FOR (look UP in the image):

1. **Overhead Wires**: Thin black/dark lines against the sky running along the street
2. **Utility Poles**: Wooden or metal poles along the roadside with wires attached
3. **Power Line Crossings**: Wires crossing above the street
4. **Transformers**: Cylindrical gray equipment mounted on poles
5. **Service Drops**: Wires going from poles to nearby buildings/houses
6. **Multiple Parallel Lines**: Power lines often run in groups of 2-6 parallel lines

DETECTION TIPS:
- Look at the TOP portion of the image (power lines are overhead)
- Lines are often thin and black against light sky
- They may have birds sitting on them
- Poles are usually visible as vertical structures
- Even barely visible thin lines in the sky are likely power lines

⚠️ CRITICAL: Identify the POSITION of power lines relative to the property:
- **"directly_above"**: Lines running directly over the property/street in front
- **"in_front_close"**: Lines very close, in front of property, within 10-30 meters
- **"nearby"**: Lines visible nearby but not directly overhead, 30-100 meters
- **"far"**: Lines visible in distance, beyond 100 meters
- **"none"**: No power lines visible anywhere

Respond with ONLY this JSON (no markdown):
{
    "visible": true or false,
    "confidence": 0.0 to 1.0,
    "type": "overhead_lines" or "utility_poles" or "transmission_lines" or "none",
    "position": "directly_above" or "in_front_close" or "nearby" or "far" or "none",
    "proximity": "very_close" or "close" or "moderate" or "far",
    "details": "specific description - mention WHERE you see lines (e.g., 'across top of image', 'along left side') and their POSITION relative to the property"
}

IMPORTANT: Power lines in streets are COMMON - if you see thin lines or poles, they're likely power infrastructure"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}",
                        "detail": "high"  # Request high-resolution analysis
                    }
                }
            ]
        }],
        "max_tokens": 600,
        "temperature": 0.1  # Low temperature for consistency
    }

    # Retry logic for rate limits
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Wait between calls to avoid rate limits
            if attempt > 0:
                wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                logger.info(f"Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                time.sleep(wait_time)

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 5))
                logger.warning(f"Rate limited. Waiting {retry_after}s")
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']

            # Parse JSON response
            try:
                # Remove markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                logger.debug(f"📄 Parsing JSON response...")
                parsed = json.loads(content)
                parsed["source"] = f"openai_vision_{image_type}"

                logger.info("="*70)
                logger.info(f"✅ DETECTION SUCCESS ({image_type.upper()})")
                logger.info(f"   👁️  Visible: {parsed.get('visible')}")
                logger.info(f"   📊 Confidence: {parsed.get('confidence', 0):.2f}")
                if image_type == "street":
                    logger.info(f"   📍 Position: {parsed.get('position', 'N/A')}")
                    logger.info(f"   📏 Proximity: {parsed.get('proximity', 'N/A')}")
                    logger.info(f"   🔌 Type: {parsed.get('type', 'N/A')}")
                else:  # satellite
                    logger.info(f"   📏 Distance: {parsed.get('distance_meters', 'N/A')}m")
                logger.info(f"   📝 Details: {parsed.get('details', 'N/A')[:150]}")
                logger.info("="*70)

                return parsed

            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON parsing failed: {str(e)}")
                logger.debug(f"   Raw content: {content[:300]}")
                # Fallback: keyword detection in response
                content_lower = content.lower()
                keywords = ['power line', 'powerline', 'utility pole', 'transmission',
                           'overhead', 'wire', 'cable', 'electrical', 'transformer']
                visible = any(kw in content_lower for kw in keywords)

                logger.info(f"🔍 Keyword fallback detection: visible={visible}")
                if visible:
                    logger.info(f"   Found keywords: {[kw for kw in keywords if kw in content_lower]}")

                return {
                    "visible": visible,
                    "confidence": 0.6 if visible else 0.2,
                    "source": f"openai_vision_{image_type}_text",
                    "details": content[:200]
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return {
                    "visible": False,
                    "confidence": 0.0,
                    "source": "api_failed",
                    "error": str(e)
                }

    return {
        "visible": False,
        "confidence": 0.0,
        "source": "max_retries_exceeded"
    }


def analyze_with_rate_limit_handling(image_bytes: bytes, analysis_type: str) -> Dict:
    """
    Generic analysis function with built-in rate limit handling.

    Args:
        image_bytes: Image data
        analysis_type: Type of analysis ('power_lines', 'structures', 'property_condition')

    Returns:
        Analysis results
    """
    if analysis_type == "power_lines_satellite":
        return detect_power_lines_enhanced(image_bytes, "satellite")
    elif analysis_type == "power_lines_street":
        return detect_power_lines_enhanced(image_bytes, "street")
    else:
        logger.warning(f"Unknown analysis type: {analysis_type}")
        return {"error": "unknown_type"}


# Export functions
__all__ = ['detect_power_lines_enhanced', 'analyze_with_rate_limit_handling']
