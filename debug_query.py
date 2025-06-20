# Debug the query endpoint
import requests
import json

BASE_URL = "http://localhost:8000"

# Try with different request formats
print("Method 1: Using json parameter with query field")
query_data = {
    "query": "What is the Employment Act in Kenya?"
}
response = requests.post(f"{BASE_URL}/query", json=query_data)
print(f"Status code: {response.status_code}")
print(response.text)
print("-" * 50)

print("Method 2: Using data parameter with json string")
query_data = json.dumps({
    "query": "What is the Employment Act in Kenya?"
})
response = requests.post(
    f"{BASE_URL}/query", 
    data=query_data, 
    headers={"Content-Type": "application/json"}
)
print(f"Status code: {response.status_code}")
print(response.text)
print("-" * 50)

print("Method 3: Using Form data")
response = requests.post(
    f"{BASE_URL}/query", 
    data={"query_text": "What is the Employment Act in Kenya?"}
)
print(f"Status code: {response.status_code}")
print(response.text)
print("-" * 50)

print("Method 4: Debug request")
# Print more details about the request and response
query_data = {
    "query": "What is the Employment Act in Kenya?"
}
response = requests.post(f"{BASE_URL}/query", json=query_data)
print(f"Status code: {response.status_code}")
print(f"Request URL: {response.request.url}")
print(f"Request headers: {response.request.headers}")
print(f"Request body: {response.request.body}")
print(f"Response headers: {response.headers}")
print(response.text)
print("-" * 50)
