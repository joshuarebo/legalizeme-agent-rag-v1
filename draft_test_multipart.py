"""
Test script for the draft endpoint using multipart/form-data
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"

def test_draft_multipart():
    """Test the draft endpoint using multipart/form-data"""
    print("Testing /draft endpoint with multipart/form-data")

    # Create the draft request
    draft_request = {
        "document_type": "Lease Agreement",
        "context": "Draft a standard residential lease agreement between John Doe (lessor) and Jane Smith (lessee) for the property at 123 Main St, Nairobi. The lease term is 12 months starting July 1, 2023, with a monthly rent of 50,000 KES.",
        "urls": None
    }

    # Convert to JSON string for the draft_data field
    draft_data_json = json.dumps(draft_request)

    # Create the multipart/form-data request
    # The API expects a 'draft_data' field that contains a JSON string
    files = {
        'draft_data': (None, draft_data_json, 'application/json'),
        # No files to upload for this test
    }

    try:
        response = requests.post(
            f"{BASE_URL}/draft",
            files=files
        )
        
        print(f"Status Code: {response.status_code}")
        print(response.text)
        
        if response.status_code == 200:
            result = response.json()
            print("\nFormatted Response:")
            pprint(result)
            return result
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    test_draft_multipart()
