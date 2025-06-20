# Test the minimal API endpoint to debug issues
import requests
import json

BASE_URL = "http://localhost:8000"
test_data = {
    "query": "What is the Employment Act in Kenya?"
}

# Try using form data which seems to work
response = requests.post(
    f"{BASE_URL}/query", 
    data={"query_text": "What is the Employment Act in Kenya?"}
)
print(f"Form data status: {response.status_code}")
print(response.text)
print("-" * 50)

# Let's create a workaround function for our test
def test_query(query):
    """Test the query endpoint with form data"""
    response = requests.post(
        f"{BASE_URL}/query", 
        data={"query_text": query}
    )
    return response.json()

def test_summarize(query):
    """Test the summarize endpoint with form data"""
    response = requests.post(
        f"{BASE_URL}/summarize", 
        data={"query_text": query}
    )
    return response.status_code, response.text

def test_draft(doc_type, context):
    """Test the draft endpoint"""
    response = requests.post(
        f"{BASE_URL}/draft", 
        json={"type": doc_type, "context": context}
    )
    return response.status_code, response.text

# Test the query endpoint
print("\nTest 1: Basic legal query")
result = test_query("What are the requirements for business registration in Kenya?")
print(json.dumps(result, indent=2))

print("\nTest 2: Employment law query")
result = test_query("Explain the process of terminating an employee in Kenya")
print(json.dumps(result, indent=2))

print("\nTest 3: Summarize attempt")
status, result = test_summarize("Summarize the Children Act of Kenya")
print(f"Status: {status}")
print(result)

print("\nTest 4: Draft a demand letter")
status, result = test_draft("demand_letter", "I purchased a defective laptop and need a refund")
print(f"Status: {status}")
print(result)

print("\nTests completed.")
