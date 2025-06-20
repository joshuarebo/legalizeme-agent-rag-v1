"""
Script to inspect FastAPI route definitions
"""

import requests
from pprint import pprint

BASE_URL = "http://localhost:8000"

# Get the OpenAPI schema
print("Fetching OpenAPI schema to inspect API definitions...")
try:
    response = requests.get(f"{BASE_URL}/openapi.json")
    if response.status_code == 200:
        schema = response.json()
        
        # Print all paths and their operations
        print("\nAPI Paths and Operations:")
        for path, operations in schema.get("paths", {}).items():
            print(f"\nPath: {path}")
            for method, operation in operations.items():
                print(f"  Method: {method.upper()}")
                print(f"  Summary: {operation.get('summary', 'No summary')}")
                print(f"  Description: {operation.get('description', 'No description')}")
                
                # Print request body details if they exist
                if "requestBody" in operation:
                    print("  Request Body:")
                    content = operation["requestBody"].get("content", {})
                    for content_type, content_schema in content.items():
                        print(f"    Content-Type: {content_type}")
                        if "schema" in content_schema:
                            print(f"    Schema: {content_schema['schema']}")
                
                # Print parameters if they exist
                if "parameters" in operation:
                    print("  Parameters:")
                    for param in operation["parameters"]:
                        print(f"    - {param.get('name')} ({param.get('in')}): {param.get('description', 'No description')}")
        
        # Specifically look for the /draft endpoint
        print("\n\nDetailed inspection of /draft endpoint:")
        draft_path = schema.get("paths", {}).get("/draft", {})
        if draft_path:
            draft_post = draft_path.get("post", {})
            print(f"Summary: {draft_post.get('summary', 'No summary')}")
            print(f"Description: {draft_post.get('description', 'No description')}")
            
            # Print request body details
            if "requestBody" in draft_post:
                print("Request Body:")
                content = draft_post["requestBody"].get("content", {})
                for content_type, content_schema in content.items():
                    print(f"  Content-Type: {content_type}")
                    if "schema" in content_schema:
                        schema_ref = content_schema["schema"]
                        print(f"  Schema: {schema_ref}")
                        
                        # If the schema is a reference, resolve it
                        if "$ref" in schema_ref:
                            ref_path = schema_ref["$ref"].split("/")[1:]
                            ref_schema = schema
                            for part in ref_path:
                                ref_schema = ref_schema.get(part, {})
                            print(f"  Referenced Schema: {ref_schema}")
            
            # Print parameters
            if "parameters" in draft_post:
                print("Parameters:")
                for param in draft_post["parameters"]:
                    print(f"  - {param.get('name')} ({param.get('in')}): {param.get('description', 'No description')}")
        else:
            print("Could not find /draft endpoint in the OpenAPI schema")
    else:
        print(f"Failed to fetch OpenAPI schema: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {str(e)}")
