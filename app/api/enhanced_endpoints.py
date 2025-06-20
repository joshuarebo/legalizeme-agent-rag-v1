"""
Enhanced API Endpoints for Phase 2
Provides comprehensive legal AI endpoints with advanced features
"""
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import asyncio
import os
import tempfile
import uuid
from datetime import datetime
import json

# Import enhanced components
from app.utils.llm_factory import get_enhanced_llm, create_legal_prompt
from app.crawlers.kenya_law_crawler import KenyaLawCrawler
from app.indexing.enhanced_indexer import EnhancedDocumentIndexer, SearchResult
from app.parsers.document_processor_enhanced import EnhancedDocumentProcessor
from app.utils.logger import get_logger
from mcp_server.legal_mcp_server import LegalMCPServer

logger = get_logger(__name__)

# Pydantic models for API requests/responses
class LegalQuery(BaseModel):
    query: str = Field(..., description="The legal question or query")
    context: Optional[str] = Field(None, description="Additional context for the query")
    area_of_law: Optional[str] = Field(None, description="Specific area of law")
    jurisdiction: str = Field("kenya", description="Legal jurisdiction")
    max_results: int = Field(10, description="Maximum number of search results")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    max_results: int = Field(10, description="Maximum number of results")
    search_type: str = Field("semantic", description="Type of search: semantic, citation, metadata")

class CitationSearch(BaseModel):
    citation: str = Field(..., description="Legal citation to search for")
    max_results: int = Field(5, description="Maximum number of results")

class DocumentDraft(BaseModel):
    document_type: str = Field(..., description="Type of document to draft")
    template: Optional[str] = Field(None, description="Template to use")
    variables: Dict[str, Any] = Field({}, description="Variables for document generation")
    instructions: Optional[str] = Field(None, description="Special instructions")

class LegalAnalysisRequest(BaseModel):
    question: str = Field(..., description="Legal question to analyze")
    context: Optional[str] = Field(None, description="Additional context")
    facts: Optional[str] = Field(None, description="Relevant facts")
    area_of_law: Optional[str] = Field(None, description="Area of law")
    depth: str = Field("standard", description="Analysis depth: quick, standard, comprehensive")

# Response models
class LegalResponse(BaseModel):
    answer: str
    reasoning: List[str]
    citations: List[Dict[str, Any]]
    confidence: float
    sources: List[str]
    legal_principles: List[str]
    processing_time: float

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    processing_time: float
    filters_applied: Optional[Dict[str, Any]]

class DocumentProcessingResponse(BaseModel):
    document_id: str
    title: str
    status: str
    chunks_created: int
    citations_found: int
    entities_extracted: Dict[str, int]
    processing_time: float

class IndexStats(BaseModel):
    total_documents: int
    total_chunks: int
    index_size: int
    last_updated: str
    embedding_model: str

# Authentication
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API token (placeholder implementation)."""
    token = credentials.credentials
    # In production, implement proper token verification
    if token != os.getenv("API_TOKEN", "default-token"):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# Initialize FastAPI app
app = FastAPI(
    title="Legal Tech AI API",
    description="Advanced Legal AI API with Kenya Law integration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Global components (initialized on startup)
llm = None
crawler = None
indexer = None
document_processor = None
mcp_server = None

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global llm, crawler, indexer, document_processor, mcp_server
    
    try:
        logger.info("Initializing Legal Tech API components...")
        
        # Initialize core components
        llm = get_enhanced_llm("huggingface", "legal_reasoning")
        crawler = KenyaLawCrawler()
        indexer = EnhancedDocumentIndexer()
        document_processor = EnhancedDocumentProcessor()
        
        # Initialize MCP server
        mcp_server = LegalMCPServer()
        
        logger.info("Legal Tech API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Legal Tech API shutdown")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "components": {
            "llm": llm is not None,
            "crawler": crawler is not None,
            "indexer": indexer is not None,
            "document_processor": document_processor is not None,
            "mcp_server": mcp_server is not None
        }
    }

# Core API Endpoints

@app.post("/api/v2/legal/query", response_model=LegalResponse)
async def legal_query(
    request: LegalQuery,
    token: str = Depends(verify_token)
):
    """
    Process a legal query with enhanced AI analysis.
    """
    start_time = datetime.now()
    
    try:
        if not llm:
            raise HTTPException(status_code=503, detail="LLM service not available")
        
        # Create enhanced legal prompt
        prompt = create_legal_prompt("legal_analysis", question=request.query)
        
        if request.context:
            prompt += f"\n\nAdditional Context: {request.context}"
        
        if request.area_of_law:
            prompt += f"\n\nArea of Law: {request.area_of_law}"
        
        # Get AI response
        ai_response = await llm.invoke(prompt)
        
        # Search for supporting documents
        supporting_docs = []
        if indexer:
            search_results = await indexer.search(request.query, k=request.max_results)
            supporting_docs = [result.document_id for result in search_results]
        
        # Extract reasoning steps (simple implementation)
        reasoning_lines = [line.strip() for line in ai_response.split('\n') if line.strip().startswith(('1.', '2.', '3.', '4.', '5.'))]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return LegalResponse(
            answer=ai_response,
            reasoning=reasoning_lines,
            citations=[],  # Would extract from response
            confidence=0.85,  # Would calculate based on model confidence
            sources=supporting_docs,
            legal_principles=[],  # Would extract legal principles
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error processing legal query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    token: str = Depends(verify_token)
):
    """
    Search legal documents with various search strategies.
    """
    start_time = datetime.now()
    
    try:
        if not indexer:
            raise HTTPException(status_code=503, detail="Search service not available")
        
        results = []
        
        if request.search_type == "semantic":
            search_results = await indexer.search(
                request.query,
                k=request.max_results,
                filters=request.filters
            )
        elif request.search_type == "citation":
            search_results = await indexer.search_by_citation(
                request.query,
                k=request.max_results
            )
        elif request.search_type == "metadata":
            search_results = await indexer.search_by_metadata(
                request.filters or {},
                k=request.max_results
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
        
        # Format results
        for result in search_results:
            results.append({
                "content": result.content,
                "score": result.score,
                "document_id": result.document_id,
                "chunk_id": result.chunk_id,
                "metadata": result.metadata
            })
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            processing_time=processing_time,
            filters_applied=request.filters
        )
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/legal/analyze", response_model=LegalResponse)
async def analyze_legal_question(
    request: LegalAnalysisRequest,
    token: str = Depends(verify_token)
):
    """
    Perform comprehensive legal analysis with reasoning traces.
    """
    start_time = datetime.now()
    
    try:
        if not llm:
            raise HTTPException(status_code=503, detail="LLM service not available")
        
        # Create reasoning prompt based on depth
        if request.depth == "comprehensive":
            prompt = create_legal_prompt("reasoning_trace", query=request.question)
        else:
            prompt = create_legal_prompt("legal_analysis", question=request.question)
        
        # Add context
        if request.context:
            prompt += f"\n\nContext: {request.context}"
        
        if request.facts:
            prompt += f"\n\nRelevant Facts: {request.facts}"
        
        if request.area_of_law:
            prompt += f"\n\nArea of Law: {request.area_of_law}"
        
        # Get AI analysis
        analysis = await llm.invoke(prompt)
        
        # Extract structured information
        reasoning_steps = []
        if "Reasoning:" in analysis:
            reasoning_section = analysis.split("Reasoning:")[1].split("Conclusion:")[0]
            reasoning_steps = [line.strip() for line in reasoning_section.split('\n') if line.strip() and line.strip().startswith(('1.', '2.', '3.', '4.', '5.'))]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return LegalResponse(
            answer=analysis,
            reasoning=reasoning_steps,
            citations=[],
            confidence=0.80,
            sources=[],
            legal_principles=[],
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error analyzing legal question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Query("auto", description="Document type"),
    token: str = Depends(verify_token)
):
    """
    Upload and process a legal document.
    """
    try:
        if not document_processor or not indexer:
            raise HTTPException(status_code=503, detail="Document processing service not available")
        
        # Save uploaded file to temporary location
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document in background
        background_tasks.add_task(process_document_background, file_path, document_type)
        
        return {
            "message": "Document upload successful",
            "filename": file.filename,
            "processing_status": "queued",
            "file_size": len(content)
        }
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_document_background(file_path: str, document_type: str):
    """Background task to process uploaded document."""
    try:
        # Process document
        processed_doc = await document_processor.process_document(file_path, document_type)
        
        if processed_doc:
            # Index document
            await indexer.add_document(processed_doc)
            logger.info(f"Successfully processed and indexed document: {processed_doc.id}")
        
        # Cleanup temp file
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        logger.error(f"Error processing document in background: {str(e)}")

@app.post("/api/v2/citations/search", response_model=SearchResponse)
async def search_citations(
    request: CitationSearch,
    token: str = Depends(verify_token)
):
    """
    Search for documents containing specific legal citations.
    """
    start_time = datetime.now()
    
    try:
        if not indexer:
            raise HTTPException(status_code=503, detail="Search service not available")
        
        search_results = await indexer.search_by_citation(
            request.citation,
            k=request.max_results
        )
        
        results = []
        for result in search_results:
            results.append({
                "content": result.content,
                "score": result.score,
                "document_id": result.document_id,
                "chunk_id": result.chunk_id,
                "metadata": result.metadata
            })
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return SearchResponse(
            query=request.citation,
            results=results,
            total_results=len(results),
            processing_time=processing_time,
            filters_applied=None
        )
        
    except Exception as e:
        logger.error(f"Error searching citations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/crawl/kenya-law")
async def crawl_kenya_law(
    background_tasks: BackgroundTasks,
    section: Optional[str] = Query(None, description="Specific section to crawl"),
    max_documents: int = Query(50, description="Maximum documents to process"),
    token: str = Depends(verify_token)
):
    """
    Trigger crawling of Kenya Law website.
    """
    try:
        if not crawler:
            raise HTTPException(status_code=503, detail="Crawler service not available")
        
        # Start crawling in background
        if section:
            background_tasks.add_task(crawler.crawl_with_enhanced_extraction, section, max_documents)
        else:
            background_tasks.add_task(crawler.crawl_all_sections)
        
        return {
            "message": "Crawling started",
            "section": section or "all",
            "max_documents": max_documents,
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"Error starting crawl: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/index/stats", response_model=IndexStats)
async def get_index_stats(token: str = Depends(verify_token)):
    """
    Get statistics about the document index.
    """
    try:
        if not indexer:
            raise HTTPException(status_code=503, detail="Indexer service not available")
        
        stats = await indexer.get_stats()
        
        return IndexStats(
            total_documents=stats.total_documents,
            total_chunks=stats.total_chunks,
            index_size=stats.index_size,
            last_updated=stats.last_updated,
            embedding_model=stats.embedding_model
        )
        
    except Exception as e:
        logger.error(f"Error getting index stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/documents/draft")
async def draft_legal_document(
    request: DocumentDraft,
    token: str = Depends(verify_token)
):
    """
    Draft a legal document using AI (placeholder implementation).
    """
    try:
        if not llm:
            raise HTTPException(status_code=503, detail="LLM service not available")
        
        # Create document drafting prompt
        prompt = f"""Draft a {request.document_type} document with the following specifications:

Document Type: {request.document_type}
Variables: {json.dumps(request.variables, indent=2)}
"""
        
        if request.template:
            prompt += f"\nTemplate: {request.template}"
        
        if request.instructions:
            prompt += f"\nSpecial Instructions: {request.instructions}"
        
        # Generate document
        document_content = await llm.invoke(prompt)
        
        return {
            "document_type": request.document_type,
            "content": document_content,
            "variables_used": request.variables,
            "generated_at": datetime.now().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error drafting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates (placeholder)
@app.websocket("/ws/updates")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(30)
            await websocket.send_json({
                "type": "status_update",
                "timestamp": datetime.now().isoformat(),
                "message": "System operational"
            })
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=False
    )
