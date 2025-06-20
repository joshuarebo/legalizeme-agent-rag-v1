"""
MCP (Model Context Protocol) Server for Legal Tech Application
Provides structured access to legal data and AI capabilities
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import os

# MCP Protocol imports
try:
    from mcp import McpServer, Resource, Tool
    from mcp.types import TextContent, ImageContent, EmbeddedResource
    MCP_AVAILABLE = True
except ImportError:
    # Fallback implementations
    class McpServer:
        def __init__(self, name: str, version: str): pass
        def serve(self, **kwargs): pass
    
    class Resource:
        def __init__(self, uri: str, name: str, description: str, mimeType: str): pass
    
    class Tool:
        def __init__(self, name: str, description: str, inputSchema: Dict): pass
    
    class TextContent:
        def __init__(self, type: str, text: str): pass
    
    MCP_AVAILABLE = False

# Import our enhanced components
from app.utils.llm_factory import get_enhanced_llm, create_legal_prompt
from app.crawlers.kenya_law_crawler import KenyaLawCrawler
from app.indexing.enhanced_indexer import EnhancedDocumentIndexer, SearchResult
from app.parsers.document_processor_enhanced import EnhancedDocumentProcessor
from app.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class LegalQuery:
    """Represents a legal query with context."""
    query: str
    context: Optional[str] = None
    query_type: str = "general"
    jurisdiction: str = "kenya"
    area_of_law: Optional[str] = None
    urgency: str = "normal"

@dataclass
class LegalResponse:
    """Represents a legal AI response with citations."""
    answer: str
    reasoning: List[str]
    citations: List[Dict[str, Any]]
    confidence: float
    sources: List[str]
    legal_principles: List[str]

class LegalMCPServer:
    """
    MCP Server for legal tech application.
    
    Provides structured access to:
    - Legal document search and retrieval
    - AI-powered legal analysis
    - Document processing and indexing
    - Kenya Law data crawling
    """
    
    def __init__(self, name: str = "legal-tech-mcp", version: str = "1.0.0"):
        """Initialize the Legal MCP Server."""
        self.name = name
        self.version = version
        
        # Initialize components
        self.llm = None
        self.crawler = None
        self.indexer = None
        self.document_processor = None
        
        # MCP server instance
        self.server = McpServer(name, version)
        
        # Configuration
        self.max_search_results = int(os.getenv("MCP_MAX_SEARCH_RESULTS", "10"))
        self.default_temperature = float(os.getenv("MCP_LLM_TEMPERATURE", "0.3"))
        
        # Initialize async components
        asyncio.create_task(self._initialize_async())

    async def _initialize_async(self):
        """Initialize async components."""
        try:
            logger.info("Initializing Legal MCP Server components")
            
            # Initialize LLM
            self.llm = get_enhanced_llm("huggingface", "legal_reasoning")
            
            # Initialize other components
            self.crawler = KenyaLawCrawler()
            self.indexer = EnhancedDocumentIndexer()
            self.document_processor = EnhancedDocumentProcessor()
            
            logger.info("Legal MCP Server components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing MCP server components: {str(e)}")

    def setup_resources(self):
        """Setup MCP resources."""
        resources = [
            Resource(
                uri="legal://kenya-law/constitution",
                name="Kenya Constitution",
                description="Constitution of Kenya 2010",
                mimeType="text/plain"
            ),
            Resource(
                uri="legal://kenya-law/acts",
                name="Kenya Acts",
                description="Acts of Parliament of Kenya",
                mimeType="text/plain"
            ),
            Resource(
                uri="legal://kenya-law/cases",
                name="Kenya Case Law",
                description="Judgments and rulings from Kenyan courts",
                mimeType="text/plain"
            ),
            Resource(
                uri="legal://index/stats",
                name="Index Statistics",
                description="Statistics about the legal document index",
                mimeType="application/json"
            )
        ]
        
        for resource in resources:
            self.server.add_resource(resource)

    def setup_tools(self):
        """Setup MCP tools."""
        tools = [
            # Legal Search Tools
            Tool(
                name="search_legal_documents",
                description="Search legal documents in the knowledge base",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "filters": {"type": "object", "description": "Optional metadata filters"},
                        "max_results": {"type": "integer", "description": "Maximum number of results", "default": 10}
                    },
                    "required": ["query"]
                }
            ),
            
            # Legal Analysis Tools
            Tool(
                name="analyze_legal_question",
                description="Analyze a legal question using AI",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "question": {"type": "string", "description": "Legal question to analyze"},
                        "context": {"type": "string", "description": "Additional context"},
                        "area_of_law": {"type": "string", "description": "Area of law (e.g., constitutional, criminal)"},
                        "jurisdiction": {"type": "string", "description": "Legal jurisdiction", "default": "kenya"}
                    },
                    "required": ["question"]
                }
            ),
            
            # Citation Tools
            Tool(
                name="find_citations",
                description="Find documents containing specific legal citations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "citation": {"type": "string", "description": "Legal citation to search for"},
                        "max_results": {"type": "integer", "description": "Maximum number of results", "default": 5}
                    },
                    "required": ["citation"]
                }
            ),
            
            # Document Processing Tools
            Tool(
                name="process_document",
                description="Process and index a legal document",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the document file"},
                        "document_type": {"type": "string", "description": "Type of document", "default": "auto"}
                    },
                    "required": ["file_path"]
                }
            ),
            
            # Crawling Tools
            Tool(
                name="crawl_kenya_law",
                description="Crawl Kenya Law website for new documents",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "section": {"type": "string", "description": "Legal section to crawl"},
                        "max_documents": {"type": "integer", "description": "Maximum documents to process", "default": 50}
                    }
                }
            ),
            
            # Index Management Tools
            Tool(
                name="get_index_stats",
                description="Get statistics about the document index",
                inputSchema={"type": "object", "properties": {}}
            ),
            
            # Legal Reasoning Tools
            Tool(
                name="generate_legal_reasoning",
                description="Generate step-by-step legal reasoning for a query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Legal query requiring reasoning"},
                        "facts": {"type": "string", "description": "Relevant facts"},
                        "applicable_law": {"type": "string", "description": "Applicable legal provisions"}
                    },
                    "required": ["query"]
                }
            )
        ]
        
        for tool in tools:
            self.server.add_tool(tool)

    async def handle_resource_request(self, uri: str) -> Any:
        """Handle resource requests."""
        try:
            if uri == "legal://index/stats":
                if self.indexer:
                    stats = await self.indexer.get_stats()
                    return TextContent(type="text", text=json.dumps(asdict(stats), indent=2))
                else:
                    return TextContent(type="text", text=json.dumps({"error": "Indexer not available"}))
            
            elif uri.startswith("legal://kenya-law/"):
                section = uri.split("/")[-1]
                # Return information about the section
                return TextContent(
                    type="text", 
                    text=f"Kenya Law section: {section}\nAccess through search tools for specific documents."
                )
            
            else:
                return TextContent(type="text", text="Resource not found")
                
        except Exception as e:
            logger.error(f"Error handling resource request {uri}: {str(e)}")
            return TextContent(type="text", text=f"Error: {str(e)}")

    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Handle tool calls."""
        try:
            if tool_name == "search_legal_documents":
                return await self._search_legal_documents(arguments)
            
            elif tool_name == "analyze_legal_question":
                return await self._analyze_legal_question(arguments)
            
            elif tool_name == "find_citations":
                return await self._find_citations(arguments)
            
            elif tool_name == "process_document":
                return await self._process_document(arguments)
            
            elif tool_name == "crawl_kenya_law":
                return await self._crawl_kenya_law(arguments)
            
            elif tool_name == "get_index_stats":
                return await self._get_index_stats(arguments)
            
            elif tool_name == "generate_legal_reasoning":
                return await self._generate_legal_reasoning(arguments)
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Error handling tool call {tool_name}: {str(e)}")
            return {"error": str(e)}

    async def _search_legal_documents(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search legal documents."""
        try:
            if not self.indexer:
                return {"error": "Document indexer not available"}
            
            query = args.get("query", "")
            filters = args.get("filters", {})
            max_results = args.get("max_results", self.max_search_results)
            
            results = await self.indexer.search(query, k=max_results, filters=filters)
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.content,
                    "score": result.score,
                    "document_id": result.document_id,
                    "chunk_id": result.chunk_id,
                    "metadata": result.metadata
                })
            
            return {
                "query": query,
                "results_count": len(formatted_results),
                "results": formatted_results
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def _analyze_legal_question(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a legal question using AI."""
        try:
            if not self.llm:
                return {"error": "LLM not available"}
            
            question = args.get("question", "")
            context = args.get("context", "")
            area_of_law = args.get("area_of_law", "")
            jurisdiction = args.get("jurisdiction", "kenya")
            
            # Create legal analysis prompt
            prompt = create_legal_prompt(
                "legal_analysis",
                question=question
            )
            
            # Add context if provided
            if context:
                prompt += f"\n\nAdditional Context: {context}"
            
            if area_of_law:
                prompt += f"\n\nArea of Law: {area_of_law}"
            
            # Get AI response
            response = await self.llm.invoke(prompt)
            
            # Search for relevant documents
            search_results = []
            if self.indexer:
                search_results = await self.indexer.search(question, k=5)
            
            return {
                "question": question,
                "analysis": response,
                "supporting_documents": [
                    {
                        "content": result.content[:200] + "...",
                        "document_id": result.document_id,
                        "relevance_score": result.score
                    }
                    for result in search_results
                ],
                "jurisdiction": jurisdiction,
                "area_of_law": area_of_law
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def _find_citations(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find documents containing specific citations."""
        try:
            if not self.indexer:
                return {"error": "Document indexer not available"}
            
            citation = args.get("citation", "")
            max_results = args.get("max_results", 5)
            
            results = await self.indexer.search_by_citation(citation, k=max_results)
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.content,
                    "document_id": result.document_id,
                    "chunk_id": result.chunk_id,
                    "metadata": result.metadata
                })
            
            return {
                "citation": citation,
                "results_count": len(formatted_results),
                "results": formatted_results
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def _process_document(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process and index a document."""
        try:
            if not self.document_processor or not self.indexer:
                return {"error": "Document processing components not available"}
            
            file_path = args.get("file_path", "")
            document_type = args.get("document_type", "auto")
            
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            
            # Process document
            processed_doc = await self.document_processor.process_document(file_path, document_type)
            
            if not processed_doc:
                return {"error": "Failed to process document"}
            
            # Index document
            await self.indexer.add_document(processed_doc)
            
            return {
                "file_path": file_path,
                "document_id": processed_doc.id,
                "title": processed_doc.title,
                "chunks_created": len(processed_doc.chunks),
                "citations_found": len(processed_doc.citations),
                "entities_extracted": {k: len(v) for k, v in processed_doc.entities.items()},
                "status": "success"
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def _crawl_kenya_law(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl Kenya Law website."""
        try:
            if not self.crawler:
                return {"error": "Crawler not available"}
            
            section = args.get("section", "")
            max_documents = args.get("max_documents", 50)
            
            if section:
                # Crawl specific section
                processed_count = await self.crawler.crawl_with_enhanced_extraction(section, max_documents)
            else:
                # Crawl all sections
                await self.crawler.crawl_all_sections()
                processed_count = self.crawler.documents_crawled
            
            return {
                "section": section or "all",
                "documents_processed": processed_count,
                "status": "success"
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def _get_index_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            if not self.indexer:
                return {"error": "Indexer not available"}
            
            stats = await self.indexer.get_stats()
            return asdict(stats)
            
        except Exception as e:
            return {"error": str(e)}

    async def _generate_legal_reasoning(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate legal reasoning for a query."""
        try:
            if not self.llm:
                return {"error": "LLM not available"}
            
            query = args.get("query", "")
            facts = args.get("facts", "")
            applicable_law = args.get("applicable_law", "")
            
            # Create reasoning prompt
            prompt = create_legal_prompt("reasoning_trace", query=query)
            
            if facts:
                prompt += f"\n\nRelevant Facts: {facts}"
            
            if applicable_law:
                prompt += f"\n\nApplicable Law: {applicable_law}"
            
            # Get reasoning response
            reasoning = await self.llm.invoke(prompt)
            
            return {
                "query": query,
                "reasoning": reasoning,
                "facts": facts,
                "applicable_law": applicable_law
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def start_server(self, host: str = "localhost", port: int = 3000):
        """Start the MCP server."""
        try:
            logger.info(f"Starting Legal MCP Server on {host}:{port}")
            
            # Setup resources and tools
            self.setup_resources()
            self.setup_tools()
            
            # Start server
            if MCP_AVAILABLE:
                await self.server.serve(host=host, port=port)
            else:
                logger.warning("MCP not available, running in compatibility mode")
                # Run a simple HTTP server or other fallback
                await self._run_fallback_server(host, port)
                
        except Exception as e:
            logger.error(f"Error starting MCP server: {str(e)}")

    async def _run_fallback_server(self, host: str, port: int):
        """Run a fallback server when MCP is not available."""
        logger.info("Running fallback HTTP server for MCP functionality")
        
        # This would implement a simple HTTP API as fallback
        # For now, just log that we're running in fallback mode
        while True:
            await asyncio.sleep(60)
            logger.info("MCP fallback server running...")

def main():
    """Main entry point for the MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Legal Tech MCP Server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=3000, help="Server port")
    parser.add_argument("--name", default="legal-tech-mcp", help="Server name")
    parser.add_argument("--version", default="1.0.0", help="Server version")
    
    args = parser.parse_args()
    
    # Create and start server
    server = LegalMCPServer(args.name, args.version)
    
    try:
        asyncio.run(server.start_server(args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")

if __name__ == "__main__":
    main()
