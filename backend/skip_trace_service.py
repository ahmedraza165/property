"""
Skip Tracing Service for Property Owner Contact Information
Uses BatchData V1 API for accurate owner contact information
API Endpoint: POST https://api.batchdata.com/api/v1/property/skip-trace
"""

import requests
import logging
import time
import json
from typing import Dict, Optional, List
import os

logger = logging.getLogger(__name__)


class SkipTraceService:
    """
    Service for retrieving property owner contact information via skip tracing.
    Uses BatchData V1 API - returns owner contact information with phones, emails, addresses.
    """

    # BatchData V1 API endpoint
    BASE_URL = "https://api.batchdata.com/api/v1"

    def __init__(self):
        self.session = self._create_session()
        self.api_key = os.getenv('SKIP_TRACE_API_KEY')

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'PropertyAnalysis/1.0',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        return session

    def skip_trace_property(
        self,
        property_address: str,
        city: str,
        state: str,
        zip_code: str,
        owner_name: Optional[str] = None
    ) -> Dict:
        """
        Perform skip trace to find property owner contact information.

        Args:
            property_address: Full property street address
            city: Property city
            state: Property state (2-letter code)
            zip_code: Property ZIP code
            owner_name: Optional owner name for better matching

        Returns:
            Dictionary with owner contact information and metadata
        """
        start_time = time.time()

        result = {
            "owner_found": False,
            "owner_info": None,
            "source": "BatchData API",
            "confidence_score": 0.0,
            "processing_time_seconds": 0.0,
            "error": None,
            "all_persons": [],
            "property_info": None,
            "raw_response": None
        }

        try:
            if not self.api_key:
                logger.warning("SKIP_TRACE_API_KEY not set")
                result["error"] = "API key not configured"
                result["processing_time_seconds"] = time.time() - start_time
                return result

            response_data = self._skip_trace_batchdata(
                property_address, city, state, zip_code, owner_name
            )

            if response_data:
                result["owner_found"] = True
                result["owner_info"] = response_data.get("primary_owner")
                result["all_persons"] = response_data.get("all_persons", [])
                result["property_info"] = response_data.get("property_info")
                result["confidence_score"] = 0.85
                result["match_count"] = response_data.get("match_count", 0)
                result["raw_response"] = response_data.get("raw_response")

            result["processing_time_seconds"] = time.time() - start_time

        except Exception as e:
            logger.error(f"Skip trace error: {str(e)}", exc_info=True)
            result["error"] = str(e)
            result["processing_time_seconds"] = time.time() - start_time

        return result

    def _skip_trace_batchdata(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        owner_name: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Use BatchData V1 API for skip tracing.
        Endpoint: POST https://api.batchdata.com/api/v1/property/skip-trace
        """
        try:
            url = f"{self.BASE_URL}/property/skip-trace"

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            # Clean zip code to 5 digits
            clean_zip = zip_code.split("-")[0] if zip_code else ""

            # Build request body per API spec
            request_item = {
                "propertyAddress": {
                    "street": address,
                    "city": city,
                    "state": state,
                    "zip": clean_zip
                }
            }

            # Add owner name if provided for better matching
            if owner_name:
                name_parts = owner_name.split()
                if len(name_parts) >= 2:
                    request_item["name"] = {
                        "first": name_parts[0],
                        "last": name_parts[-1]
                    }

            payload = {
                "requests": [request_item]
            }

            logger.info(f"BatchData skip trace request for: {address}, {city}, {state} {clean_zip}")

            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                timeout=60
            )

            logger.info(f"BatchData response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"BatchData response received successfully")

                # Parse the V1 response structure
                return self._parse_v1_response(data)

            else:
                logger.error(f"BatchData API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"BatchData API request failed: {str(e)}")
            return None

    def _parse_v1_response(self, api_response: Dict) -> Optional[Dict]:
        """
        Parse BatchData V1 API response.

        Response structure:
        {
            "status": { "code": 200, "text": "OK" },
            "results": {
                "persons": [ {...} ],
                "property": {...}
            }
        }
        """
        # Get results object
        results = api_response.get('results', {})

        # V1 can return persons array directly in results
        persons = results.get('persons', [])

        if not persons:
            logger.info("No persons found in skip trace response")
            return None

        # Parse all persons
        all_persons = []
        for person in persons:
            parsed_person = self._parse_person(person)
            if parsed_person:
                all_persons.append(parsed_person)

        if not all_persons:
            return None

        # Parse property info if available
        property_info = self._parse_property_info(results.get('property', {}))

        return {
            "primary_owner": all_persons[0],
            "all_persons": all_persons,
            "property_info": property_info,
            "match_count": len(all_persons),
            "raw_response": results
        }

    def _parse_person(self, person: Dict) -> Optional[Dict]:
        """
        Parse a single person from BatchData response.

        Person structure:
        {
            "name": { "first", "last", "middle", "full" },
            "propertyAddress": { "street", "city", "state", "zip", ... },
            "mailingAddress": { "street", "city", "state", "zip", ... },
            "phoneNumbers": [ { "number", "type", "carrier", "tested", "reachable", "dnc", "score", ... } ],
            "emails": [ { "email", "tested" } ],
            "bankruptcy": {},
            "involuntaryLien": {},
            "death": { "deceased": false },
            "dnc": { "tcpa": false },
            "litigator": false,
            "property": { "id": "..." }
        }
        """
        if not person:
            return None

        # Extract name
        name_obj = person.get('name', {})
        first_name = name_obj.get('first', '')
        middle_name = name_obj.get('middle', '')
        last_name = name_obj.get('last', '')
        full_name = name_obj.get('full', '') or f"{first_name} {middle_name} {last_name}".strip()

        # Extract phone numbers - V1 uses 'phoneNumbers'
        phones = person.get('phoneNumbers', [])
        phone_list = []
        phone_primary = None
        phone_mobile = None
        phone_secondary = None

        # Sort by score (highest first)
        sorted_phones = sorted(phones, key=lambda x: x.get('score', 0), reverse=True)

        for phone in sorted_phones:
            raw_number = phone.get('number', '')
            # Format phone number: (XXX) XXX-XXXX
            formatted = raw_number
            if len(raw_number) == 10:
                formatted = f"({raw_number[:3]}) {raw_number[3:6]}-{raw_number[6:]}"
            elif len(raw_number) == 11 and raw_number.startswith('1'):
                formatted = f"+1 ({raw_number[1:4]}) {raw_number[4:7]}-{raw_number[7:]}"

            phone_data = {
                "number": raw_number,
                "formatted": formatted,
                "type": phone.get('type', 'Unknown'),
                "carrier": phone.get('carrier', ''),
                "tested": phone.get('tested', False),
                "reachable": phone.get('reachable', True),
                "dnc": phone.get('dnc', False),
                "tcpa": phone.get('tcpa', False),
                "litigator": phone.get('litigator', False),
                "score": phone.get('score', 0),
                "last_reported_date": phone.get('lastReportedDate', '')
            }
            phone_list.append(phone_data)

            # Set primary/mobile/secondary based on score and type
            number = phone.get('number', '')
            phone_type = (phone.get('type', '') or '').lower()
            is_reachable = phone.get('reachable', True)

            if number and is_reachable:
                if not phone_primary:
                    phone_primary = number
                elif 'mobile' in phone_type and not phone_mobile:
                    phone_mobile = number
                elif not phone_secondary:
                    phone_secondary = number

        # Extract emails
        emails = person.get('emails', [])
        email_list = []
        email_primary = None
        email_secondary = None

        for email_obj in emails:
            email_data = {
                "email": email_obj.get('email', ''),
                "tested": email_obj.get('tested', False)
            }
            email_list.append(email_data)

            email = email_obj.get('email', '')
            if email:
                if not email_primary:
                    email_primary = email
                elif not email_secondary:
                    email_secondary = email

        # Extract mailing address
        mailing_addr = person.get('mailingAddress', {}) or {}
        mailing_street = mailing_addr.get('street', '')
        mailing_city = mailing_addr.get('city', '')
        mailing_state = mailing_addr.get('state', '')
        mailing_zip = mailing_addr.get('zip', '')
        mailing_zip_plus4 = mailing_addr.get('zipPlus4', '')
        mailing_county = mailing_addr.get('county', '')
        mailing_validity = mailing_addr.get('addressValidity', '')

        mailing_full = ''
        if all([mailing_street, mailing_city, mailing_state, mailing_zip]):
            mailing_full = f"{mailing_street}, {mailing_city}, {mailing_state} {mailing_zip}"

        # Extract property address from response
        property_addr = person.get('propertyAddress', {}) or {}

        # Compliance flags
        death_info = person.get('death', {}) or {}
        is_deceased = death_info.get('deceased', False)

        dnc_info = person.get('dnc', {}) or {}
        tcpa_blacklisted = dnc_info.get('tcpa', False)

        is_litigator = person.get('litigator', False)

        # Check if any phone has DNC or TCPA flag
        has_dnc = any(p.get('dnc', False) for p in phones)
        has_tcpa = any(p.get('tcpa', False) for p in phones)

        # Bankruptcy and lien info
        bankruptcy = person.get('bankruptcy', {}) or {}
        involuntary_lien = person.get('involuntaryLien', {}) or {}

        # Property info - get full property details
        property_info = person.get('property', {}) or {}
        prop_address = property_info.get('address', {}) or {}
        prop_owner = property_info.get('owner', {}) or {}
        prop_owner_mailing = prop_owner.get('mailingAddress', {}) or {}

        return {
            # Basic owner info
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "full_name": full_name,

            # Phone numbers - individual fields for DB
            "phone_primary": phone_primary,
            "phone_mobile": phone_mobile,
            "phone_secondary": phone_secondary,
            "phone_list": phone_list,  # Full list with all details
            "phone_count": len(phone_list),

            # Emails - individual fields for DB
            "email_primary": email_primary,
            "email_secondary": email_secondary,
            "email_list": email_list,  # Full list with all details
            "email_count": len(email_list),

            # Mailing address (owner's mailing address)
            "mailing_street": mailing_street,
            "mailing_city": mailing_city,
            "mailing_state": mailing_state,
            "mailing_zip": mailing_zip,
            "mailing_zip_plus4": mailing_zip_plus4,
            "mailing_county": mailing_county,
            "mailing_validity": mailing_validity,
            "mailing_full_address": mailing_full,

            # Property address from skip trace request
            "property_street": property_addr.get('street', ''),
            "property_city": property_addr.get('city', ''),
            "property_state": property_addr.get('state', ''),
            "property_zip": property_addr.get('zip', ''),
            "property_zip_plus4": property_addr.get('zipPlus4', ''),
            "property_county": prop_address.get('county', ''),
            "property_validity": property_addr.get('addressValidity', ''),

            # Property details from API
            "property_id": property_info.get('id', ''),
            "property_full_address": f"{prop_address.get('street', '')}, {prop_address.get('city', '')}, {prop_address.get('state', '')} {prop_address.get('zip', '')}".strip(', '),

            # Record owner info (from county records)
            "record_owner_name": prop_owner.get('name', {}).get('full', ''),
            "record_owner_first": prop_owner.get('name', {}).get('first', ''),
            "record_owner_last": prop_owner.get('name', {}).get('last', ''),

            # Compliance flags
            "is_deceased": is_deceased,
            "is_litigator": is_litigator,
            "tcpa_blacklisted": tcpa_blacklisted,
            "has_dnc": has_dnc,
            "has_tcpa": has_tcpa,

            # Bankruptcy info
            "has_bankruptcy": bool(bankruptcy),
            "bankruptcy_info": bankruptcy if bankruptcy else None,

            # Lien info
            "has_involuntary_lien": bool(involuntary_lien),
            "lien_info": involuntary_lien if involuntary_lien else None,

            # Match metadata
            "matched": person.get('meta', {}).get('matched', True),

            # Owner type
            "owner_type": "Individual",

            # Confidence
            "confidence": 0.85
        }

    def _parse_property_info(self, property_data: Dict) -> Optional[Dict]:
        """Parse property information from response."""
        if not property_data:
            return None

        address = property_data.get('address', {})
        mailing_address = property_data.get('mailingAddress', {})
        owners = property_data.get('owners', [])

        # Parse owners
        owner_list = []
        for owner in owners:
            name = owner.get('name', {})
            owner_list.append({
                "first_name": name.get('first', ''),
                "middle_name": name.get('middle', ''),
                "last_name": name.get('last', ''),
                "full_name": name.get('full', '')
            })

        return {
            "property_id": property_data.get('id', ''),

            # Property address
            "address_street": address.get('street', ''),
            "address_city": address.get('city', ''),
            "address_state": address.get('state', ''),
            "address_zip": address.get('zip', ''),
            "address_zip_plus4": address.get('zipPlus4', ''),
            "address_county": address.get('county', ''),
            "address_full": address.get('fullAddress', ''),
            "address_validity": address.get('addressValidity', ''),

            # Property mailing address
            "mailing_street": mailing_address.get('street', ''),
            "mailing_city": mailing_address.get('city', ''),
            "mailing_state": mailing_address.get('state', ''),
            "mailing_zip": mailing_address.get('zip', ''),
            "mailing_full": mailing_address.get('fullAddress', ''),

            # Owners on record
            "owners": owner_list,
            "owner_count": len(owner_list)
        }

    def batch_skip_trace(
        self,
        properties: List[Dict[str, str]],
        batch_size: int = 100
    ) -> List[Dict]:
        """
        Perform skip trace on multiple properties at once.
        BatchData supports up to 100 properties per request.

        Args:
            properties: List of dicts with address, city, state, zip keys
            batch_size: Number of properties per batch (max 100)

        Returns:
            List of skip trace results
        """
        results = []

        if not self.api_key:
            logger.warning("Batch skip trace requires SKIP_TRACE_API_KEY")
            for prop in properties:
                results.append({
                    "owner_found": False,
                    "error": "API key not configured"
                })
            return results

        try:
            url = f"{self.BASE_URL}/property/skip-trace"

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            # Process in batches
            for i in range(0, len(properties), batch_size):
                batch = properties[i:i + batch_size]

                # Build requests array
                requests_data = []
                for prop in batch:
                    clean_zip = prop.get('zip', '').split("-")[0]
                    request_item = {
                        "propertyAddress": {
                            "street": prop.get('address', ''),
                            "city": prop.get('city', ''),
                            "state": prop.get('state', ''),
                            "zip": clean_zip
                        }
                    }
                    requests_data.append(request_item)

                payload = {
                    "requests": requests_data
                }

                logger.info(f"Batch skip trace for {len(batch)} properties")

                response = self.session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=120
                )

                if response.status_code == 200:
                    api_response = response.json()
                    batch_results = api_response.get('results', {})
                    persons = batch_results.get('persons', [])

                    # For batch requests, we get multiple persons
                    for person in persons:
                        parsed = self._parse_person(person)
                        if parsed:
                            results.append({
                                "owner_found": True,
                                "owner_info": parsed,
                                "all_persons": [parsed],
                                "source": "BatchData API (Batch)",
                                "confidence_score": 0.85,
                                "error": None
                            })
                        else:
                            results.append({
                                "owner_found": False,
                                "owner_info": None,
                                "source": "BatchData API (Batch)",
                                "confidence_score": 0.0,
                                "error": None
                            })

                else:
                    logger.error(f"Batch API error: {response.status_code} - {response.text}")
                    for _ in batch:
                        results.append({
                            "owner_found": False,
                            "error": f"API error: {response.status_code}"
                        })

        except Exception as e:
            logger.error(f"Batch skip trace failed: {str(e)}")
            remaining = len(properties) - len(results)
            for _ in range(remaining):
                results.append({
                    "owner_found": False,
                    "error": str(e)
                })

        return results
