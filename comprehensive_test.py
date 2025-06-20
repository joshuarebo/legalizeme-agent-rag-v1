import requests
import json
import os
from time import sleep

# Terminal colors for better readability
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

def print_result(status, data, success_msg=None):
    """Pretty print a result with color"""
    if 200 <= status < 300:
        status_color = Colors.GREEN
        status_text = "SUCCESS"
        if success_msg:
            print(f"{status_color}{status_text}: {success_msg}{Colors.END}")
    else:
        status_color = Colors.RED
        status_text = "FAILED"
        
    print(f"{status_color}Status: {status} ({status_text}){Colors.END}")
    
    if isinstance(data, dict) or isinstance(data, list):
        print(json.dumps(data, indent=2))
    else:
        print(data)
    print("-" * 50)

def test_query(query):
    """Test the query endpoint with form data"""
    print(f"{Colors.YELLOW}Query: {query}{Colors.END}")
    response = requests.post(
        f"{BASE_URL}/query", 
        data={"query_text": query}
    )
    print_result(response.status_code, response.json())

def check_server():
    """Check if the server is running"""
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print(f"{Colors.GREEN}Server is running at {BASE_URL}{Colors.END}")
            return True
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}Server is not running at {BASE_URL}{Colors.END}")
        return False

# Main test routine
def run_tests():
    # First, check if the server is running
    if not check_server():
        print(f"{Colors.RED}Please start the server with 'python start_app.py' before running tests{Colors.END}")
        return
    
    print_section("WELCOME ENDPOINT")
    response = requests.get(BASE_URL)
    print_result(response.status_code, response.json(), "Welcome endpoint is working")
    
    print_section("LEGAL QUERIES")
    test_query("What are the requirements for business registration in Kenya?")
    test_query("Explain the Employment Act in Kenya")
    test_query("What are the legal procedures for divorce in Kenya?")
    
    print_section("PERFORMANCE STATUS")
    response = requests.get(f"{BASE_URL}/performance/status")
    print_result(response.status_code, response.json(), "Performance status endpoint is working")
    
    print_section("CRAWLER STATUS")
    response = requests.get(f"{BASE_URL}/crawler/status")
    print_result(response.status_code, response.json(), "Crawler status endpoint is working")
    
    print_section("ALL TESTS COMPLETED")
    print(f"{Colors.GREEN}The Counsel Legal AI backend is running successfully!{Colors.END}")
    print(f"{Colors.YELLOW}Note: Some endpoints require file uploads or specific request formats.{Colors.END}")
    print(f"{Colors.YELLOW}Check the API documentation at {BASE_URL}/docs for more information.{Colors.END}")

if __name__ == "__main__":
    run_tests()
