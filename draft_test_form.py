"""
Test script specifically for the draft endpoint with application/x-www-form-urlencoded
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"

# Create the draft request based on the DraftRequest model definition
document_type = "Lease Agreement"
context = "Draft a standard residential lease agreement between John Doe (lessor) and Jane Smith (lessee) for the property at 123 Main St, Nairobi. The lease term is 12 months starting July 1, 2023, with a monthly rent of 50,000 KES."

print("Testing /draft endpoint with x-www-form-urlencoded")

# Approach 5: Using form-urlencoded with field names matching the model
print("Approach 5: Using form-urlencoded with field names matching the model")
try:
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'document_type': document_type,
        'context': context
    }
    response = requests.post(
        f"{BASE_URL}/draft",
        headers=headers,
        data=data
    )
    
    print(f"Status Code: {response.status_code}")
    print(response.text)
    
    if response.status_code == 200:
        result = response.json()
        print("\nFormatted Response:")
        pprint(result)
except Exception as e:
    print(f"Error: {str(e)}")

print("\nTest completed")
