# Simple test client for Counsel API
import requests
import json

# Define the base URL
BASE_URL = "http://localhost:8000"

def print_response(response):
    """Pretty print a JSON response"""
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print(f"Status code: {response.status_code}")
    print("-" * 50)

# 1. Test the welcome endpoint
print("Testing the welcome endpoint...")
response = requests.get(BASE_URL)
print_response(response)

# 2. Test a simple legal query
print("\nTesting a simple legal query...")
query_data = {
    "query": "What are the legal requirements for terminating an employee under Kenyan law?"
}
response = requests.post(f"{BASE_URL}/query", json=query_data)
print_response(response)

# 3. Test the performance status endpoint
print("\nTesting the performance status endpoint...")
response = requests.get(f"{BASE_URL}/performance/status")
print_response(response)

# 4. Test the crawler status endpoint
print("\nTesting the crawler status endpoint...")
response = requests.get(f"{BASE_URL}/crawler/status")
print_response(response)

print("\nTests completed.")
