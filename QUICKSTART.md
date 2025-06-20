# Counsel: Quick Start Guide

This guide will help you get started with Counsel, the Legal AI Assistant for Kenyan Law.

## Setup Instructions

### For Windows Users (Recommended):

1. Simply double-click on `run_app.bat` in the root folder.
   - This will create a virtual environment
   - Install all required dependencies (with fallbacks for problematic ones)
   - Create necessary data directories
   - Start the application with all available features

2. **Minimal Mode (Faster Setup)**: 
   - If you have issues with the standard setup, double-click `run_minimal.bat`
   - This installs only essential dependencies and uses stubs for others
   - Some advanced features may be limited, but core functionality will work

3. Access the API at: http://localhost:8000

### For PowerShell Users:

1. Right-click on `run_app.ps1` and select "Run with PowerShell"
   - This provides the most comprehensive setup with better error handling
   - The script will automatically handle problematic dependencies

### Manual Setup:

If you prefer to set up manually:

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create necessary directories:
   ```
   mkdir -p data/vector_db data/model_cache data/temp_pdfs data/llm_config logs
   ```

5. Start the application:
   ```
   python -m app.main
   ```

## Troubleshooting

If you encounter issues during setup:

1. **Error Messages**: Check the terminal for specific error messages that identify the problem

2. **Dependency Issues**: Some packages might fail to install depending on your system:
   - If you see errors about missing wheels or compilation failures, try the minimal setup
   - Run `run_minimal.bat` which uses fewer dependencies

3. **Import Errors**: If the application starts but shows import errors:
   - The patching system should handle most missing modules automatically
   - Check if any files in `app/utils/stubs` need to be created or fixed

4. **Common Runtime Errors**:
   - **"Document.__init__() missing 1 required positional argument: 'page_content'"** - Fixed in updated stubs
   - **"'StateGraph' object has no attribute 'add_conditional_edges'"** - Fixed in updated stubs
   - **"invalid literal for int() with base 10"** - Caused by comments in environment variables, fixed in latest version
   - **"Error initializing Mixtral model"** - Normal when running with stubs, application will use fallback LLM

5. **Application Won't Start**: If the API server won't start:
   - Check that port 8000 is not already in use by another application
   - Try running `python start_app.py` directly to see detailed error messages

6. **Minimal Dependencies**: The application can run with just these packages:
   ```
   fastapi
   uvicorn
   pydantic
   python-dotenv
   python-multipart
   langchain
   langchain-community
   ```
## Using the API

Once the application is running, you can interact with it using the following endpoints:

- `GET /` - Welcome message and available endpoints
- `POST /query` - Submit legal questions
- `POST /summarize` - Summarize legal documents
- `POST /draft` - Generate legal document drafts
- `GET /crawler/status` - Check crawler status
- `GET /performance/status` - Check performance optimization status

## Example Usage

### Simple Query:
```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query": "What are the requirements for business registration in Kenya?"}'
```

### With Document Upload:
```bash
curl -X POST "http://localhost:8000/query" -F "query_text=Analyze this employment contract" -F "files=@path/to/contract.pdf"
```

### With Web Link:
```bash
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"query": "Explain this case", "urls": ["https://new.kenyalaw.org/search/?query=civil+case+123"]}'
```

### Document Summarization:
```bash
curl -X POST "http://localhost:8000/summarize" -F "files=@path/to/legal_document.pdf"
```

### Draft a Legal Document:
```bash
curl -X POST "http://localhost:8000/draft" -H "Content-Type: application/json" -d '{"type": "demand_letter", "context": "I purchased a defective laptop on June 1, 2023, and the seller has refused to honor the warranty", "requirements": "I want a full refund plus compensation for inconvenience"}'
```

### Status Checks:
```bash
# Check crawler status
curl -X GET "http://localhost:8000/crawler/status"

# Check performance optimization status
curl -X GET "http://localhost:8000/performance/status"
```

## Next Steps

1. Read the full README.md for detailed information on all features
2. Explore the API through the FastAPI documentation at http://localhost:8000/docs
3. Check the logs directory for detailed application logs

### Testing the Application

Once the application is running, you can verify it's working correctly by:

1. **Quick Test**: Run `test_all.bat` to perform a comprehensive test of all API endpoints
   ```
   test_all.bat
   ```

2. **Manual Testing**: Access the API at http://localhost:8000
   - API documentation is available at http://localhost:8000/docs
   - You can use the Swagger UI to test all endpoints interactively

3. **Using curl or other API tools**:
   ```
   # Example query (using form data)
   curl -X POST "http://localhost:8000/query" -F "query_text=What is the Employment Act in Kenya?"
   ```
