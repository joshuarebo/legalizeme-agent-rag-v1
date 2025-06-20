"""
Focused test script for draft and summarize endpoints
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

def test_draft_endpoint():
    """Test the /draft endpoint with correct format."""
    print_separator("TESTING DRAFT ENDPOINT")
    
    # Create the draft request
    draft_data = {
        "document_type": "Lease Agreement",
        "context": "Draft a standard residential lease agreement between John Doe (lessor) and Jane Smith (lessee) for the property at 123 Main St, Nairobi. The lease term is 12 months starting July 1, 2023, with a monthly rent of 50,000 KES."
    }
    
    print(f"Drafting a {draft_data['document_type']}")
    
    # Based on the error message, it seems FastAPI expects a 'draft_data' wrapper
    payload = {"draft_data": draft_data}
    
    try:
        # Try with Form data
        response = requests.post(
            f"{BASE_URL}/draft",
            data={"draft_data": json.dumps(draft_data)}
        )
        
        if response.status_code == 422:  # If form data fails, try JSON
            print("Form data approach failed, trying with JSON...")
            response = requests.post(
                f"{BASE_URL}/draft",
                json=payload
            )
    except Exception as e:
        print(f"Error: {str(e)}")
        return
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        try:
            result = response.json()
            print("\nResponse:")
            pprint(result)
            return result
        except:
            print("Could not parse JSON response")
            print(response.text)
    else:
        print(f"Error: {response.text}")
    
    return None

def test_summarize_endpoint():
    """Test the /summarize endpoint with a file."""
    print_separator("TESTING SUMMARIZE ENDPOINT")
    
    pdf_path = os.path.join(os.getcwd(), "test_document.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"Error: Test PDF file not found at {pdf_path}")
        return None
    
    print(f"Summarizing file: {pdf_path}")
    
    files = {"files": open(pdf_path, "rb")}
    data = {"query_text": "Summarize this legal document"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/summarize",
            data=data,
            files=files
        )
        files["files"].close()
    except Exception as e:
        print(f"Error: {str(e)}")
        if "files" in files and hasattr(files["files"], "close"):
            files["files"].close()
        return
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        try:
            result = response.json()
            print("\nResponse:")
            pprint(result)
            return result
        except:
            print("Could not parse JSON response")
            print(response.text)
    else:
        print(f"Error: {response.text}")
    
    return None

def check_server():
    """Check if the server is running."""
    try:
        response = requests.get(BASE_URL)
        print(f"Server is running at {BASE_URL}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"Server is not running at {BASE_URL}")
        return False

if __name__ == "__main__":
    if check_server():
        test_draft_endpoint()
        test_summarize_endpoint()
    else:
        print("Please start the server with 'python start_app.py' before running tests")
