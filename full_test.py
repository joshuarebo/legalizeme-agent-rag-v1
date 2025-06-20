# Simple test client for testing all endpoints
import requests
import json

# Define the base URL
BASE_URL = "http://localhost:8000"

def print_response(response):
    """Pretty print a JSON response"""
    print(f"Status code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print("-" * 50)

# 1. Test the welcome endpoint
print("Testing the welcome endpoint...")
response = requests.get(BASE_URL)
print_response(response)

# 2. Test a simple legal query
print("\nTesting a simple legal query...")
query_data = {
    "query": "What is the Employment Act in Kenya?"
}
response = requests.post(f"{BASE_URL}/query", json=query_data)
print_response(response)

# 3. Test the summarize endpoint
print("\nTesting the summarize endpoint...")
summarize_data = {
    "query": "Summarize the Children Act"
}
response = requests.post(f"{BASE_URL}/summarize", json=summarize_data)
print_response(response)

# 4. Test the draft endpoint
print("\nTesting the draft endpoint...")
draft_data = {
    "type": "demand_letter",
    "context": "I purchased a defective laptop on June 1, 2023, and the seller has refused to honor the warranty",
    "requirements": "I want a full refund plus compensation for inconvenience"
}
response = requests.post(f"{BASE_URL}/draft", json=draft_data)
print_response(response)

# 5. Test the performance status endpoint
print("\nTesting the performance status endpoint...")
response = requests.get(f"{BASE_URL}/performance/status")
print_response(response)

# 6. Test the crawler status endpoint
print("\nTesting the crawler status endpoint...")
response = requests.get(f"{BASE_URL}/crawler/status")
print_response(response)

print("\nTests completed.")
