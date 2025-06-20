"""
Main FastAPI application for Counsel - Legal AI Assistant
"""
import os
import asyncio
import time
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our LangGraph agent
from app.agents.counsel_agent import CounselAgent
from app.crawlers.scheduler import CrawlerScheduler
from app.optimization.performance_optimizer import PerformanceOptimizer
from app.api import crawler as crawler_router
from app.api import performance as performance_router

app = FastAPI(
    title="Counsel API",
    description="Legal AI Assistant API for Kenyan Law",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize our agent
counsel_agent = CounselAgent()

# Include the crawler router
app.include_router(crawler_router.router)

# Include the performance router
app.include_router(performance_router.router)

# Initialize performance optimizer
performance_optimizer = PerformanceOptimizer()

# Request timing middleware for performance tracking
@app.middleware("http")
async def add_performance_tracking(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = (time.time() - start_time) * 1000
    
    # Track response time for non-static endpoints
    if not request.url.path.startswith(("/static/", "/favicon.ico")):
        performance_optimizer.track_response_time(process_time_ms)
    
    # Add timing header
    response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
    return response

# Request models
class QueryRequest(BaseModel):
    query: str
    urls: Optional[List[HttpUrl]] = None

class SummarizeRequest(BaseModel):
    urls: Optional[List[HttpUrl]] = None
    query: Optional[str] = None

class DraftRequest(BaseModel):
    document_type: str
    context: str
    urls: Optional[List[HttpUrl]] = None

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Counsel API - Legal AI Assistant for Kenyan Law",
        "version": "1.0.0",
        "endpoints": ["/query", "/summarize", "/draft", "/crawler"],
    }

@app.post("/query")
async def query(
    query_data: Optional[QueryRequest] = None,
    query_text: Optional[str] = Form(None),
    files: List[UploadFile] = File(None),
):
    """Handle legal questions with optional files/links."""
    # Debug info
    print(f"query_data: {query_data}")
    print(f"query_text: {query_text}")
    print(f"files: {files}")
    
    # Get query from either form or JSON
    query = query_text if query_text else (query_data.query if query_data else None)
    urls = query_data.urls if query_data else []
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    # Process the query through our agent
    response = await counsel_agent.run_query(
        query=query,
        files=files,
        urls=urls,
    )
    
    return response

@app.post("/summarize")
async def summarize(
    summarize_data: Optional[SummarizeRequest] = None,
    query_text: Optional[str] = Form(None),
    files: List[UploadFile] = File(None),
):
    """Summarize documents or web pages."""
    # Get query from either form or JSON
    query = query_text if query_text else (summarize_data.query if summarize_data else "")
    urls = summarize_data.urls if summarize_data else []
    
    if not files and not urls:
        raise HTTPException(status_code=400, detail="At least one file or URL is required")
    
    # Process through our agent
    response = await counsel_agent.run_summarize(
        query=query,
        files=files,
        urls=urls,
    )
    
    return response

@app.post("/draft")
async def draft(
    draft_data: DraftRequest,
    files: List[UploadFile] = File(None),
):
    """Draft legal documents based on context and type."""
    if not draft_data.document_type or not draft_data.context:
        raise HTTPException(status_code=400, detail="Document type and context are required")
    
    # Process through our agent
    response = await counsel_agent.run_draft(
        document_type=draft_data.document_type,
        context=draft_data.context,
        files=files,
        urls=draft_data.urls,
    )
    
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize components on application startup."""
    # Start the performance optimizer if enabled
    if os.getenv("ENABLE_OPTIMIZATION", "True").lower() in ("true", "1", "t"):
        performance_optimizer.start()
        
    # Start the crawler scheduler if enabled
    if os.getenv("ENABLE_CRAWLER", "True").lower() in ("true", "1", "t"):
        scheduler = CrawlerScheduler()
        asyncio.create_task(scheduler.start())

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    # Stop the performance optimizer
    performance_optimizer.stop()

if __name__ == "__main__":
    # Run the API directly when this file is executed
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t")
    
    # Use the correct module path
    uvicorn.run("app.api.main:app", host=host, port=port, reload=debug)
