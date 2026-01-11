"""
BatchData Skip Tracing Service
API Documentation: https://developer.batchdata.com/docs/batchdata/batchdata-v1/operations/create-a-property-skip-trace
"""

import requests
import json
import csv
from typing import List, Dict, Optional
import os

class BatchDataSkipTracing:
    """
    BatchData Skip Tracing API Integration

    API Key provided: fK481Qi8ebi0nm41ULdiBZmcbkwdT00XsBHrGzRP

    Endpoints:
    - Skip Trace: POST https://api.batchdata.com/api/v1/property/skip-trace
    - Async Skip Trace: POST https://api.batchdata.com/api/v1/property/skip-trace/async

    Features:
    - Up to 100 properties per request
    - Returns phone numbers (mobile & landline), emails, mailing addresses
    - DNC (Do Not Call) status verification
    - TCPA compliance data
    """

    BASE_URL = "https://api.batchdata.com/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def skip_trace_by_address(self, properties: List[Dict]) -> Dict:
        """
        Skip trace properties by address.

        Args:
            properties: List of property dicts with address info
                Each dict should have:
                - street: Street address
                - city: City name
                - state: State abbreviation
                - zip: Postal code

        Returns:
            API response with owner contact information

        Example request body:
        {
            "requests": [
                {
                    "propertyAddress": {
                        "street": "757 Cane St E",
                        "city": "Lehigh Acres",
                        "state": "FL",
                        "zip": "33974"
                    }
                }
            ]
        }
        """
        endpoint = f"{self.BASE_URL}/property/skip-trace"

        # Format properties for API request
        requests_data = []
        for prop in properties:
            request_item = {
                "propertyAddress": {
                    "street": prop.get("street", ""),
                    "city": prop.get("city", ""),
                    "state": prop.get("state", ""),
                    "zip": prop.get("zip", "").split("-")[0]  # Use 5-digit zip
                }
            }
            requests_data.append(request_item)

        payload = {"requests": requests_data}

        print(f"Making skip trace request for {len(properties)} properties...")
        print(f"Endpoint: {endpoint}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error Response: {response.text}")
                return {"error": response.text, "status_code": response.status_code}

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return {"error": str(e)}

    def skip_trace_by_name(self, persons: List[Dict]) -> Dict:
        """
        Skip trace by person name and address.

        Args:
            persons: List of person dicts with:
                - firstName: First name
                - lastName: Last name
                - street: Street address (optional)
                - city: City name (optional)
                - state: State abbreviation (optional)
                - zip: Postal code (optional)
        """
        endpoint = f"{self.BASE_URL}/property/skip-trace"

        requests_data = []
        for person in persons:
            request_item = {
                "name": {
                    "first": person.get("firstName", ""),
                    "last": person.get("lastName", "")
                }
            }

            # Add address if available
            if person.get("street"):
                request_item["propertyAddress"] = {
                    "street": person.get("street", ""),
                    "city": person.get("city", ""),
                    "state": person.get("state", ""),
                    "zip": person.get("zip", "").split("-")[0]
                }

            requests_data.append(request_item)

        payload = {"requests": requests_data}

        print(f"Making skip trace request for {len(persons)} persons...")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            print(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error Response: {response.text}")
                return {"error": response.text, "status_code": response.status_code}

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return {"error": str(e)}

    def validate_api_key(self) -> bool:
        """Test if the API key is valid"""
        # Try a simple request to validate credentials
        endpoint = f"{self.BASE_URL}/property/skip-trace"

        # Minimal test payload
        payload = {
            "requests": [{
                "propertyAddress": {
                    "street": "123 Test St",
                    "city": "Miami",
                    "state": "FL",
                    "zip": "33101"
                }
            }]
        }

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            # 200 = success, 401/403 = invalid key
            if response.status_code == 200:
                print("API key is valid!")
                return True
            elif response.status_code in [401, 403]:
                print(f"API key invalid or unauthorized: {response.status_code}")
                return False
            else:
                print(f"Unexpected response: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Connection error: {str(e)}")
            return False


def load_properties_from_csv(csv_path: str) -> List[Dict]:
    """Load properties from the CSV file"""
    properties = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prop = {
                "firstName": row.get("First Name", ""),
                "lastName": row.get("Last Name", ""),
                "street": row.get("Street address", ""),
                "city": row.get("City", ""),
                "state": row.get("State", ""),
                "zip": row.get("Postal Code", "")
            }
            properties.append(prop)

    return properties


def main():
    """Test the BatchData Skip Tracing API"""

    # Your API key
    API_KEY = "fK481Qi8ebi0nm41ULdiBZmcbkwdT00XsBHrGzRP"

    # Initialize the service
    skip_tracer = BatchDataSkipTracing(API_KEY)

    # First, validate the API key
    print("=" * 60)
    print("VALIDATING API KEY")
    print("=" * 60)

    # Load properties from CSV
    csv_path = "/Users/ahmadraza/Documents/property-anyslis/backend/Export_Contacts_Cleaned Target Best Lehigh_Dec_2025_5_41_PM.csv"

    print("\n" + "=" * 60)
    print("LOADING PROPERTIES FROM CSV")
    print("=" * 60)

    properties = load_properties_from_csv(csv_path)
    print(f"Loaded {len(properties)} properties from CSV")

    # Show first 3 properties
    print("\nFirst 3 properties:")
    for i, prop in enumerate(properties[:3]):
        print(f"  {i+1}. {prop['firstName']} {prop['lastName']}")
        print(f"      {prop['street']}, {prop['city']}, {prop['state']} {prop['zip']}")

    # Test skip trace with first property
    print("\n" + "=" * 60)
    print("TESTING SKIP TRACE API")
    print("=" * 60)

    # Try skip trace by address for first property
    test_property = properties[0] if properties else None

    if test_property:
        print(f"\nSkip tracing: {test_property['firstName']} {test_property['lastName']}")
        print(f"Address: {test_property['street']}, {test_property['city']}, {test_property['state']} {test_property['zip']}")

        # Method 1: Skip trace by address only
        result = skip_tracer.skip_trace_by_address([{
            "street": test_property['street'],
            "city": test_property['city'],
            "state": test_property['state'],
            "zip": test_property['zip']
        }])

        print("\n" + "=" * 60)
        print("SKIP TRACE RESULT")
        print("=" * 60)
        print(json.dumps(result, indent=2))

        # Save result to file
        with open("/Users/ahmadraza/Documents/property-anyslis/backend/skip_trace_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\nResult saved to skip_trace_result.json")


if __name__ == "__main__":
    main()
