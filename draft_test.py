"""
Test script specifically for the draft endpoint
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"

def print_separator():
    print("\n" + "="*80 + "\n")

# Create the draft request based on the DraftRequest model definition
draft_data = {
    "document_type": "Lease Agreement",
    "context": "Draft a standard residential lease agreement between John Doe (lessor) and Jane Smith (lessee) for the property at 123 Main St, Nairobi. The lease term is 12 months starting July 1, 2023, with a monthly rent of 50,000 KES.",
    "urls": []  # Optional field
}

print("Testing /draft endpoint with various approaches")
print_separator()

# Test 1: Using draft_data as Form Data
print("Approach 1: Using Form Data")
try:
    response = requests.post(
        f"{BASE_URL}/draft",
        data={"document_type": draft_data["document_type"], "context": draft_data["context"]}
    )
    
    print(f"Status Code: {response.status_code}")
    print(response.text)
except Exception as e:
    print(f"Error: {str(e)}")

print_separator()

# Test 2: Using draft_data as JSON
print("Approach 2: Using JSON data directly")
try:
    response = requests.post(
        f"{BASE_URL}/draft",
        json=draft_data
    )
    
    print(f"Status Code: {response.status_code}")
    print(response.text)
except Exception as e:
    print(f"Error: {str(e)}")

print_separator()

# Test 3: Using 'draft_data' wrapper as JSON
print("Approach 3: Using 'draft_data' wrapper in JSON")
try:
    response = requests.post(
        f"{BASE_URL}/draft",
        json={"draft_data": draft_data}
    )
    
    print(f"Status Code: {response.status_code}")
    print(response.text)
except Exception as e:
    print(f"Error: {str(e)}")

print_separator()

# Test 4: Using Form Data with JSON string
print("Approach 4: Using Form Data with JSON string")
try:
    response = requests.post(
        f"{BASE_URL}/draft",
        data={"draft_data": json.dumps(draft_data)}
    )
    
    print(f"Status Code: {response.status_code}")
    print(response.text)
except Exception as e:
    print(f"Error: {str(e)}")

print_separator()
print("All tests completed")
