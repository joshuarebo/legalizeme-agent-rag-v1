# LegalizeMe: Advanced Legal AI Assistant for Kenyan Law

LegalizeMe is an intelligent legal AI backend system deployed at [https://www.legalizeme.site](https://www.legalizeme.site). It provides comprehensive legal assistance based on Kenyan law, leveraging advanced AI techniques to retrieve information, parse documents, and generate legal responses with citations and detailed reasoning.

## System Architecture Overview

The LegalizeMe system consists of three main phases:
1. **Phase 1**: Basic RAG pipeline with document processing
2. **Phase 2**: Enhanced RAG with hybrid search and performance optimization
3. **Phase 3**: Full agent-based system with LangGraph workflow and reasoning capabilities

The current implementation is **Phase 3**, which incorporates all features from previous phases with added agent capabilities.

### Core Components

- **KenyaLawRetriever**: Advanced RAG component with hybrid search, query expansion, and filtering
- **CounselAgent**: LangGraph-based agent with multi-step reasoning and citation generation
- **Document Processing**: PDF and web content parsing with enhanced metadata extraction
- **Crawling System**: Automated crawling of Kenya Law website for up-to-date legal information
- **Performance Optimization**: Automatic tuning of vector database and LLM parameters

## Features

- **Real-time Legal Data**: Retrieves and reasons over Kenyan legal data from [Kenya Law](https://new.kenyalaw.org/)
- **Document Understanding**: Parses and understands PDFs, legal texts, judgments, etc.
- **Citation Support**: Provides citations and reasoning traces for all responses
- **Legal Document Drafting**: Creates drafts of legal documents like contracts and notices
- **Automated Data Crawling**: Regularly crawls Kenya Law website to keep legal data up-to-date
- **Advanced Legal Reasoning**: Implements multi-step legal reasoning with issue identification, rule application, and conclusion generation
- **Performance Optimization**: Automatic tuning of vector store and LLM parameters for faster responses

## Tech Stack

LegalizeMe is built with a fully open-source stack:

- **LangGraph** – For memory-based graph-agent workflows
- **Haystack** – For RAG pipeline with FAISS vector database
- **Hugging Face Transformers** – For open-source LLMs (Mixtral)
- **Unstructured.io**, **PyMuPDF** – For parsing PDFs and HTML legal documents
- **FastAPI** – For exposing API endpoints
- **MiniMax-01** – GitHub fallback model
- **BeautifulSoup4 & aiocron** - For web crawling and scheduling
- **FAISS & Ray** - For optimized vector indexing and distributed computing

## Getting Started

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/joshuarebo/legalizeme-agent-rag-v1.git
   cd legalizeme-agent-rag-v1
   ```

2. Run the application using one of the provided scripts:
   
   **For Windows users (Recommended):**
   ```bash
   # Full installation with all features (PowerShell script with fallback to batch)
   run_app.bat
   
   # Minimal installation for development (lighter dependencies)
   run_minimal.bat
   
   # Run Phase 3 specific tests
   run_phase3_test.bat
   ```
   
   **For PowerShell users:**
   ```powershell
   # Full installation with all features
   .\run_app.ps1
   ```

   **Manual installation:**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run the application
   python -m app.main
   ```

3. Access the API at http://localhost:8000

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Core settings
OPENAI_API_KEY=your_openai_key_here  # Optional, used as fallback
HUGGINGFACE_API_KEY=your_hf_key_here  # Optional, for HF model access
FAISS_INDEX_PATH=data/vector_db  # Default location for vector database

# Optional settings
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
ENABLE_CRAWLER=true  # Set to false to disable auto-crawling
ENABLE_PERFORMANCE_OPTIMIZER=true  # Set to false to disable auto-optimization
```

## API Endpoints for Frontend Integration

LegalizeMe exposes the following API endpoints for frontend integration:

### Main Endpoints

- `POST /api/v1/query` – Primary endpoint for legal questions
- `POST /api/v1/summarize` – Summarizes legal documents with context
- `POST /api/v1/draft` – Drafts legal documents based on requirements

### Enhanced Endpoints (Phase 2 & 3)

- `POST /api/v1/enhanced/query` – Advanced query endpoint with multi-step reasoning
- `POST /api/v1/enhanced/analyze` – Analyzes legal documents with detailed structure
- `POST /api/v1/enhanced/compare` – Compares multiple legal documents or scenarios

### Admin & Monitoring Endpoints

- `GET /api/v1/crawler/status` – Get the current status of the Kenya Law crawler
- `POST /api/v1/crawler/trigger/full` – Manually trigger a full crawl of Kenya Law
- `POST /api/v1/crawler/trigger/quick` – Trigger a quick update of recent content
- `GET /api/v1/performance/status` – Get the status of the performance optimization
- `POST /api/v1/performance/optimize` – Manually trigger performance optimization

### MCP Server for Advanced Integration

For frontend applications requiring streaming responses and complex interactions, use the Model Context Protocol (MCP) server:

- Server Location: `mcp_server/legal_mcp_server.py`
- Endpoint: `ws://localhost:8765` (when running locally)
- Protocol: WebSocket with [MCP Protocol](https://github.com/microsoft/MCP)

## Detailed API Request/Response Examples

### 1. Basic Query Endpoint

**Request:**
```json
POST /api/v1/query
Content-Type: application/json

{
  "query": "What are the legal requirements for terminating an employee under Kenyan law?",
  "options": {
    "include_citations": true,
    "include_reasoning": true
  }
}
```

**Response:**
```json
{
  "response": "Under Kenyan law, terminating an employee requires following these requirements: ...",
  "citations": [
    {
      "text": "Employment Act, 2007",
      "url": "https://new.kenyalaw.org/legislation/employment-act-2007/",
      "section": "Section 35",
      "relevance": 0.92
    }
  ],
  "reasoning_trace": "1. Identified the query relates to employment termination in Kenya\n2. Retrieved relevant statutes and case law...",
  "confidence_score": 0.87
}
```

### 2. Document Upload and Analysis

**Request:**
```
POST /api/v1/enhanced/analyze
Content-Type: multipart/form-data

file: [binary PDF data]
query: "Is this employment contract compliant with Kenyan law?"
options: {
  "detailed_analysis": true,
  "highlight_issues": true
}
```

**Response:**
```json
{
  "document_type": "Employment Contract",
  "analysis": "This employment contract contains several provisions that may not comply with Kenyan law:",
  "issues": [
    {
      "clause": "Termination Notice (Section 4.2)",
      "issue": "The 7-day notice period is below the statutory minimum of 1 month for monthly-paid employees",
      "reference": "Employment Act, Section 35(1)(c)",
      "recommendation": "Increase notice period to at least 1 month"
    }
  ],
  "compliance_score": 0.68,
  "highlighted_document": "[Base64 encoded PDF with highlights]"
}
```

### 3. Legal Document Drafting

**Request:**
```json
POST /api/v1/draft
Content-Type: application/json

{
  "document_type": "demand_letter",
  "parameters": {
    "sender_name": "John Doe",
    "recipient_name": "ABC Corporation",
    "issue": "Unpaid wages for March 2023",
    "amount_due": "KES 45,000",
    "payment_deadline": "14 days"
  },
  "options": {
    "format": "docx",
    "legal_references": true
  }
}
```

**Response:**
```json
{
  "document": "[Base64 encoded DOCX]",
  "preview_text": "DEMAND LETTER\n\nDated: June 19, 2025\n\nTo: ABC Corporation...",
  "legal_references": [
    "Employment Act, Section 17 - Payment of Wages",
    "Employment Act, Section 85 - Complaints and jurisdiction in cases of dispute"
  ],
  "download_url": "/api/v1/documents/temp/demand_letter_20250619_123456.docx"
}
```

## Frontend Integration Guide

### Authentication

All API endpoints require authentication using Bearer tokens:

```javascript
const headers = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json'
};

fetch('https://api.legalizeme.site/api/v1/query', {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({
    query: "What are the requirements for registering a company in Kenya?"
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### File Upload Integration

For endpoints that accept file uploads, use multipart/form-data:

```javascript
const formData = new FormData();
formData.append('file', documentFile); // File object from input
formData.append('query', 'Analyze this contract');

const headers = {
  'Authorization': `Bearer ${API_KEY}`
};

fetch('https://api.legalizeme.site/api/v1/enhanced/analyze', {
  method: 'POST',
  headers: headers,
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### Streaming Responses with MCP Server

For real-time streaming responses, use the WebSocket MCP server:

```javascript
const ws = new WebSocket('wss://api.legalizeme.site/mcp');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'query',
    payload: {
      query: 'Explain Kenyan intellectual property law',
      stream: true
    }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'content') {
    // Append streaming content to UI
    appendToResponseUI(data.payload.content);
  } else if (data.type === 'citations') {
    // Display citations when they arrive
    displayCitations(data.payload.citations);
  }
};
```

## Error Handling

The API uses standard HTTP status codes:
- 200 - Success
- 400 - Bad request (invalid parameters)
- 401 - Unauthorized (invalid or missing API key)
- 404 - Resource not found
- 422 - Validation error (invalid file format, etc.)
- 500 - Server error

Error responses follow this format:

```json
{
  "error": {
    "code": "invalid_document",
    "message": "The uploaded file is not a valid legal document",
    "details": {
      "accepted_formats": ["pdf", "docx", "txt"],
      "received_format": "jpg"
    }
  }
}
```

## Testing and Development

For frontend developers testing the integration:

1. Use `test_api.py` for quick API tests
2. Run `phase3_simple_test.py` for simple end-to-end testing
3. Use `phase3_comprehensive_test.py` for full system testing

A mock server is available for development without the full backend:
```bash
python -m app.api.mock_server
```

This runs on http://localhost:8001 and implements all API endpoints with mock data.

## Deployment

The production API is available at:
- Main API: https://api.legalizeme.site
- WebSocket: wss://api.legalizeme.site/mcp

For staging and testing:
- Staging API: https://staging-api.legalizeme.site
- Development API: https://dev-api.legalizeme.site

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Kenya Law](https://new.kenyalaw.org/) for providing access to legal information
- All the open-source projects that make LegalizeMe possible
