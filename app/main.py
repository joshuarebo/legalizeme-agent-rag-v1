"""
Main application entry point
"""
import os
import sys
import argparse
import uvicorn
from dotenv import load_dotenv

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def main():
    """Main entry point for the application."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Counsel - Legal AI Assistant for Kenyan Law")
    parser.add_argument("--host", type=str, default=os.getenv("API_HOST", "0.0.0.0"),
                        help="Host to run the API server on")
    parser.add_argument("--port", type=int, default=int(os.getenv("API_PORT", "8000")),
                        help="Port to run the API server on")
    parser.add_argument("--reload", action="store_true", default=os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t"),
                        help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    # Run the API server - use the correct import path for app.api.main:app
    uvicorn.run("app.api.main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()
