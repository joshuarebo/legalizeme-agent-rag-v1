"""
Final test script for the Counsel Legal AI API endpoints
"""

import requests
import json
import os
from pprint import pprint

BASE_URL = "http://localhost:8000"

def print_separator(title):
    """Print a separator with a title."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_query(query_text):
    """Test the query endpoint"""
    print(f"Query: {query_text}")
    
    response = requests.post(
        f"{BASE_URL}/query",
        data={"query_text": query_text}
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Response:")
        pprint(result)
        return result
    else:
        print(f"Error: {response.text}")
        return None

def test_summarize(file_path, query_text="Please summarize this document"):
    """Test the summarize endpoint with a file"""
    print(f"Summarizing file: {file_path}")
    print(f"Query: {query_text}")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None
    
    with open(file_path, "rb") as f:
        files = {"files": f}
        data = {"query_text": query_text}
        
        response = requests.post(
            f"{BASE_URL}/summarize",
            data=data,
            files=files
        )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Response:")
        pprint(result)
        return result
    else:
        print(f"Error: {response.text}")
        return None

def run_all_tests():
    """Run all tests"""
    print_separator("WELCOME ENDPOINT")
    response = requests.get(BASE_URL)
    print(f"Status Code: {response.status_code}")
    pprint(response.json())
    
    print_separator("QUERY ENDPOINT - Business Registration")
    test_query("What are the requirements for business registration in Kenya?")
    
    print_separator("QUERY ENDPOINT - Employment Law")
    test_query("Explain the Employment Act in Kenya regarding termination")
    
    print_separator("QUERY ENDPOINT - Family Law")
    test_query("What are the rights of children in divorce proceedings under Kenyan law?")
    
    print_separator("QUERY ENDPOINT - Contract Law")
    test_query("What are the essential elements of a valid contract under Kenyan law?")
    
    print_separator("QUERY ENDPOINT - Tax Law")
    test_query("What are the tax implications for foreign investors in Kenya?")
    
    print_separator("SUMMARIZE ENDPOINT")
    pdf_path = os.path.join(os.getcwd(), "test_document.pdf")
    test_summarize(pdf_path, "Provide a detailed summary of this legal document")
    
    print_separator("PERFORMANCE STATUS")
    response = requests.get(f"{BASE_URL}/performance/status")
    print(f"Status Code: {response.status_code}")
    pprint(response.json())
    
    print_separator("CRAWLER STATUS")
    response = requests.get(f"{BASE_URL}/crawler/status")
    print(f"Status Code: {response.status_code}")
    pprint(response.json())
    
    print_separator("ALL TESTS COMPLETED")
    print("The Counsel Legal AI backend has been tested!")

if __name__ == "__main__":
    # Check if the server is running
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print(f"Server is running at {BASE_URL}")
            run_all_tests()
        else:
            print(f"Server returned status code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"Server is not running at {BASE_URL}")
        print("Please start the server with 'python start_app.py' before running tests")
