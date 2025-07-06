"""
Counsel Agent - Core LangGraph agent implementation
"""
import os
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from fastapi import UploadFile
from pydantic import HttpUrl, BaseModel
import httpx

# Try to import the real langgraph first; fall back to internal stub if unavailable
try:
    from langgraph.graph import StateGraph, END  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from app.utils.stubs.langgraph.graph import StateGraph, END

# Import our custom components
from app.rag.retriever import KenyaLawRetriever
from app.parsers.document_parser import DocumentParser
from app.parsers.web_parser import WebParser
from app.utils.llm_factory import get_llm, get_fallback_llm
from app.utils.prompts import SYSTEM_PROMPT, INSTRUCTION_TEMPLATE
from app.utils.logger import get_logger
from app.utils.llm_router import get_router

logger = get_logger(__name__)

class AgentState(BaseModel):
    """State object for the Counsel agent."""
    query: str
    urls: List[HttpUrl] = []
    file_contents: List[Dict[str, Any]] = []
    web_contents: List[Dict[str, Any]] = []
    retrieved_documents: List[Dict[str, Any]] = []
    context: str = ""
    response: Optional[str] = None
    reasoning_trace: Optional[str] = None
    citations: List[Dict[str, Any]] = []
    error: Optional[str] = None
    use_fallback: bool = False
    document_type: Optional[str] = None
    confidence_score: Optional[float] = None
    legal_issues: List[str] = []
    legal_rules: List[Dict[str, str]] = []
    legal_conclusion: Optional[str] = None
    # Model selection parameters
    model_choice: Optional[str] = "flan-t5"
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 2048
    system_prompt: Optional[str] = None
    

class CounselAgent:
    """
    Main agent class that orchestrates the entire workflow using LangGraph.
    """
    
    def __init__(self):
        """Initialize the agent components."""
        self.retriever = KenyaLawRetriever()
        self.doc_parser = DocumentParser()
        self.web_parser = WebParser()
        self.primary_llm = get_llm(os.getenv("PRIMARY_LLM_TYPE", "mixtral"))
        self.fallback_llm = get_fallback_llm()
        
        # Initialize the legal reasoner
        from app.rag.legal_reasoner import LegalReasoner
        self.legal_reasoner = LegalReasoner()
        
        # Build the LangGraph workflow
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with enhanced routing."""
        # Define the workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes to the graph
        workflow.add_node("query_handler", self._query_handler)
        workflow.add_node("document_parser", self._document_parser)
        workflow.add_node("web_parser", self._web_parser)
        workflow.add_node("retriever", self._retriever)
        workflow.add_node("context_builder", self._context_builder)
        workflow.add_node("legal_reasoning", self._legal_reasoning)  # Add legal reasoning node
        workflow.add_node("llm_executor", self._llm_executor)
        workflow.add_node("fallback_executor", self._fallback_executor)
        workflow.add_node("citation_formatter", self._citation_formatter)
        
        # Define the edges (flow) of the graph with conditional routing
        workflow.add_edge("query_handler", self._route_after_query_handler)
        
        # Add conditional edges after query handling
        workflow.add_conditional_edges(
            "query_handler",
            self._route_after_query_handler,
            {
                "document_parser": "document_parser",
                "web_parser": "web_parser",
                "retriever": "retriever"
            }
        )
        
        # Add regular edges
        workflow.add_edge("document_parser", "web_parser")
        workflow.add_edge("web_parser", "retriever")
        workflow.add_edge("retriever", "context_builder")
        workflow.add_edge("context_builder", "legal_reasoning")  # Add legal reasoning before LLM
        workflow.add_edge("legal_reasoning", "llm_executor")
        
        # Add conditional edges after LLM execution
        workflow.add_conditional_edges(
            "llm_executor",
            self._should_use_fallback,
            {
                True: "fallback_executor",
                False: "citation_formatter"
            }
        )
        
        workflow.add_edge("fallback_executor", "citation_formatter")
        workflow.add_edge("citation_formatter", END)
          # Set the entry point
        workflow.set_entry_point("query_handler")
        
        return workflow
    
    def _route_after_query_handler(self, state: AgentState) -> str:
        """Determine the next node after query handling based on state."""
        # If we have files, go to document parser
        if state.file_contents:
            return "document_parser"
        # If we have URLs but no files, go to web parser
        elif state.urls:
            return "web_parser"
        # Otherwise, go straight to retriever
        else:
            return "retriever"
    
    async def _query_handler(self, state: AgentState) -> AgentState:
        """Process the initial query and prepare the state."""
        logger.info(f"Processing query: {state.query}")
        return state
        
    async def _document_parser(self, state: AgentState) -> AgentState:
        """Parse any attached files."""
        if not state.file_contents:
            return state
        
        logger.info(f"Parsing {len(state.file_contents)} documents")
        parsed_documents = []
        
        for doc in state.file_contents:
            try:
                # Enhanced document parsing with direct implementations
                file_type = doc["file_type"]
                content = doc["content"]
                filename = doc["filename"]
                
                # Create a temporary file for processing
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                
                try:
                    parsed_content = ""
                    
                    # PDF handling
                    if "pdf" in file_type.lower():
                        try:
                            # Try using PyMuPDF if available
                            import fitz
                            pdf_doc = fitz.open(temp_path)
                            
                            # Extract text from each page
                            text_content = []
                            for page_num in range(len(pdf_doc)):
                                page = pdf_doc.load_page(page_num)
                                text_content.append(page.get_text())
                            
                            parsed_content = "\n\n".join(text_content)
                            logger.info(f"Parsed PDF {filename} with PyMuPDF")
                        except ImportError:
                            # Fallback to fallback parser
                            parsed_content = await self.doc_parser.parse(
                                content=content,
                                file_type=file_type
                            )
                            logger.info(f"Parsed PDF {filename} with fallback parser")
                    
                    # DOCX handling
                    elif "word" in file_type.lower() or "docx" in file_type.lower():
                        try:
                            # Try using python-docx if available
                            import docx
                            doc_file = docx.Document(temp_path)
                            
                            # Extract text from paragraphs
                            text_content = []
                            for para in doc_file.paragraphs:
                                text_content.append(para.text)
                            
                            parsed_content = "\n\n".join(text_content)
                            logger.info(f"Parsed DOCX {filename} with python-docx")
                        except ImportError:
                            # Fallback to fallback parser
                            parsed_content = await self.doc_parser.parse(
                                content=content,
                                file_type=file_type
                            )
                            logger.info(f"Parsed DOCX {filename} with fallback parser")
                    
                    # TXT and other text formats
                    else:
                        try:
                            # Try reading as text
                            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                                parsed_content = f.read()
                            logger.info(f"Parsed text file {filename}")
                        except Exception as text_error:
                            logger.error(f"Error reading text from {filename}: {str(text_error)}")
                            # Fallback to fallback parser
                            parsed_content = await self.doc_parser.parse(
                                content=content,
                                file_type=file_type
                            )
                            logger.info(f"Parsed {filename} with fallback parser")
                    
                    # Add to parsed documents
                    parsed_documents.append({
                        "filename": filename,
                        "content": parsed_content,
                        "source": f"Uploaded file: {filename}"
                    })
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        logger.warning(f"Error removing temp file: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Error parsing document {doc['filename']}: {str(e)}")
                # Try original parser as last resort
                try:
                    parsed_content = await self.doc_parser.parse(
                        content=doc["content"],
                        file_type=doc["file_type"]
                    )
                    parsed_documents.append({
                        "filename": doc["filename"],
                        "content": parsed_content,
                        "source": f"Uploaded file: {doc['filename']} (fallback parser)"
                    })
                    logger.info(f"Parsed {doc['filename']} with fallback parser")
                except Exception as e2:
                    logger.error(f"Fallback parser also failed: {str(e2)}")
        
        # Add parsed documents to state
        state.file_contents = parsed_documents
        return state
    
    async def _web_parser(self, state: AgentState) -> AgentState:
        """Parse any web URLs."""
        if not state.urls:
            return state
        
        logger.info(f"Parsing {len(state.urls)} URLs")
        parsed_websites = []
        
        # Convert URL objects to strings
        url_strings = [str(url) for url in state.urls]
        
        # Try to use enhanced web parsing if available
        try:
            # Check if httpx is available for web scraping
            import httpx
            
            # Process each URL
            for url in url_strings:
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url, follow_redirects=True)
                        response.raise_for_status()
                        
                        # Extract content using BeautifulSoup if available
                        try:
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Remove script and style elements
                            for script in soup(["script", "style"]):
                                script.extract()
                            
                            # Get text
                            text = soup.get_text()
                            
                            # Break into lines and remove leading and trailing space
                            lines = (line.strip() for line in text.splitlines())
                            # Break multi-headlines into a line each
                            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                            # Remove blank lines
                            text = '\n'.join(chunk for chunk in chunks if chunk)
                            
                            parsed_websites.append({
                                "url": url,
                                "content": text,
                                "source": f"Web page: {url}"
                            })
                            logger.info(f"Successfully parsed {url} with BeautifulSoup")
                        except ImportError:
                            # If BeautifulSoup is not available, use the raw HTML
                            parsed_websites.append({
                                "url": url,
                                "content": response.text,
                                "source": f"Web page: {url} (raw HTML)"
                            })
                            logger.info(f"Parsed {url} as raw HTML")
                except Exception as e:
                    logger.error(f"Error fetching URL {url}: {str(e)}")
        except ImportError:
            # Fall back to original implementation if httpx not available
            for url in state.urls:
                try:
                    parsed_content = await self.web_parser.parse(url=str(url))
                    parsed_websites.append({
                        "url": str(url),
                        "content": parsed_content,
                        "source": f"Web page: {url}"
                    })
                except Exception as e:
                    logger.error(f"Error parsing URL {url}: {str(e)}")
        
        # Add parsed websites to state
        state.web_contents = parsed_websites
        return state
    
    async def _retriever(self, state: AgentState) -> AgentState:
        """Retrieve relevant documents from Kenya Law."""
        logger.info(f"Retrieving documents for query: {state.query}")
        
        try:
            # Step 1: Query rewriting for better retrieval
            rewritten_query = await self._rewrite_query(state.query)
            logger.info(f"Rewritten query: {rewritten_query}")
            
            # Step 2: Retrieve documents using enhanced retrieval
            retrieved_docs = await self.retriever.retrieve(
                query=rewritten_query,
                top_k=8  # Retrieve more docs initially for filtering
            )
            
            # Step 3: Relevance filtering
            filtered_docs = await self._filter_by_relevance(retrieved_docs, state.query)
            
            # Step 4: Structure the results with metadata
            state.retrieved_documents = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "Kenya Law Database"),
                    "relevance_score": getattr(doc, "score", 0.0)
                }
                for doc in filtered_docs
            ]
            
            logger.info(f"Retrieved and filtered {len(state.retrieved_documents)} documents")
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            state.error = f"Document retrieval error: {str(e)}"
        
        return state
        
    async def _rewrite_query(self, original_query: str) -> str:
        """Rewrite the query to improve retrieval performance."""
        try:
            # Use a structured approach to query rewriting
            # This would ideally use an LLM call, but we'll implement a rule-based approach for now
            
            # Check if we need to expand legal terms
            legal_terms_to_expand = {
                "constitution": "constitution of kenya constitutional rights fundamental freedoms",
                "employment": "employment act labor relations employer employee rights",
                "land": "land act property rights ownership title deed",
                "children": "children act minors rights welfare guardianship",
                "contract": "contract law agreement consideration offer acceptance",
            }
            
            expanded_query = original_query
            
            # Add legal context terms
            for term, expansion in legal_terms_to_expand.items():
                if term.lower() in original_query.lower():
                    expanded_query += f" {expansion}"
            
            # Add Kenyan legal system context if not present
            if "kenya" not in expanded_query.lower() and "kenyan" not in expanded_query.lower():
                expanded_query += " kenya kenyan law legal system"
                
            return expanded_query
        except Exception as e:
            logger.error(f"Error rewriting query: {str(e)}")
            return original_query  # Fall back to original query
    
    async def _filter_by_relevance(self, docs, query: str) -> List:
        """Filter documents by relevance to query."""
        try:
            if not docs:
                return []
                
            # Simple relevance threshold filtering
            threshold = 0.5  # Minimum relevance score
            
            # Filter based on score if available
            if hasattr(docs[0], "score"):
                filtered_docs = [doc for doc in docs if getattr(doc, "score", 0.0) > threshold]
                # Sort by relevance score (descending)
                filtered_docs.sort(key=lambda x: getattr(x, "score", 0.0), reverse=True)
                # Take top 5 most relevant
                return filtered_docs[:5]
            
            # If no scores, use all documents but limit to top 5
            return docs[:5]
        except Exception as e:
            logger.error(f"Error filtering documents: {str(e)}")
            return docs[:5] if docs else []  # Return first 5 docs or empty list
    
    async def _context_builder(self, state: AgentState) -> AgentState:
        """Build the context for the LLM by combining all sources."""
        # Combine all sources of information
        all_sources = []
        
        # Add retrieved documents (highest priority)
        for doc in state.retrieved_documents:
            all_sources.append({
                "content": doc["content"],
                "source": doc["source"],
                "relevance": doc.get("relevance_score", 1.0),
                "type": "retrieved"
            })
        
        # Add parsed files (medium priority)
        for doc in state.file_contents:
            all_sources.append({
                "content": doc["content"],
                "source": doc["source"],
                "relevance": 0.9,  # User-provided files are assumed relevant
                "type": "file"
            })
        
        # Add parsed web pages (lower priority)
        for doc in state.web_contents:
            all_sources.append({
                "content": doc["content"],
                "source": doc["source"],
                "relevance": 0.8,  # Web content may be less relevant
                "type": "web"
            })
        
        # Sort sources by relevance
        all_sources.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Select the most relevant sources to stay within context limits
        # A rough estimate of token count based on characters
        total_chars = 0
        max_chars = 14000  # Approximately 3500 tokens for 7B-8B models
        selected_sources = []
        
        for source in all_sources:
            source_chars = len(source["content"])
            if total_chars + source_chars <= max_chars:
                selected_sources.append(source)
                total_chars += source_chars
            else:
                # If we can't fit the whole source, try to include a summary or excerpt
                excerpt_size = max(500, max_chars - total_chars)  # At least 500 chars
                if excerpt_size > 500:  # Only add if we can include a meaningful excerpt
                    source["content"] = source["content"][:excerpt_size] + "... [truncated]"
                    selected_sources.append(source)
                break
        
        # Build the context string with clear section headers
        context_parts = []
        
        # Add legal context first
        legal_docs = [s for s in selected_sources if s["type"] == "retrieved"]
        if legal_docs:
            context_parts.append("## LEGAL REFERENCES")
            for i, source in enumerate(legal_docs, 1):
                context_parts.append(f"### Source {i}: {source['source']}\n{source['content']}\n")
        
        # Add uploaded files
        file_docs = [s for s in selected_sources if s["type"] == "file"]
        if file_docs:
            context_parts.append("## UPLOADED DOCUMENTS")
            for i, source in enumerate(file_docs, 1):
                context_parts.append(f"### File {i}: {source['source']}\n{source['content']}\n")
        
        # Add web content
        web_docs = [s for s in selected_sources if s["type"] == "web"]
        if web_docs:
            context_parts.append("## WEB CONTENT")
            for i, source in enumerate(web_docs, 1):
                context_parts.append(f"### Web Source {i}: {source['source']}\n{source['content']}\n")
        
        state.context = "\n\n".join(context_parts)
        
        # If we're in draft mode, add the document type
        if state.document_type:            state.context += f"\n\n## DOCUMENT TO DRAFT\nType: {state.document_type}\n\n"
        
        logger.info(f"Built context with {len(selected_sources)}/{len(all_sources)} sources (approximately {total_chars} chars)")
        return state
    
    async def _legal_reasoning(self, state: AgentState) -> AgentState:
        """Perform legal reasoning on the context."""
        try:
            if not state.context:
                logger.warning("No context available for legal reasoning")
                return state
                
            analysis = await self.legal_reasoner.analyze(state.query, state.context)
            
            # Extract legal issues
            state.legal_issues = analysis.get("issues", [])
            
            # Extract legal rules
            state.legal_rules = [{"rule": rule} for rule in analysis.get("rules", [])]
            
            # Extract legal conclusion
            state.legal_conclusion = analysis.get("conclusion", "")
            
            # Extract confidence score
            state.confidence_score = analysis.get("confidence", 0.0)
            
            # Extract citations
            state.citations = analysis.get("citations", [])
            
            logger.info(f"Legal reasoning extracted {len(state.legal_issues)} issues and {len(state.legal_rules)} rules")
            
            return state
        except Exception as e:
            logger.error(f"Error in legal reasoning: {str(e)}")
            return state
    async def _llm_executor(self, state: AgentState) -> AgentState:
        """Execute the selected LLM to generate a response with structured reasoning."""
        logger.info(f"Executing {state.model_choice} LLM with structured reasoning")
        
        try:
            # Get the router
            router = get_router()
            
            # Prepare a more structured prompt for legal reasoning
            system_prompt = state.system_prompt or SYSTEM_PROMPT
            
            # Add structured reasoning instructions
            reasoning_instructions = """
            You are tasked with providing a thorough legal analysis. Approach this task with the following structure:

            1. ISSUE IDENTIFICATION: Identify the legal issues presented.
            2. RULE ANALYSIS: Identify relevant legal principles, statutes, or precedents.
            3. APPLICATION: Apply the rules to the specific facts of this query.
            4. CONCLUSION: Provide a clear legal conclusion based on your analysis.
            5. CITATIONS: Include specific citations to legal authorities used.

            Your response should be structured with these sections:
            - Legal Analysis (main response)
            - REASONING TRACE (detailed step-by-step reasoning)
            - CITATIONS (formatted references to legal authorities)
            """
            
            # Prepare the prompt
            prompt = f"Query: {state.query}\n\nContext:\n{state.context}"
            full_system_prompt = f"{system_prompt}\n\n{reasoning_instructions}"
            
            # Call the LLM via router
            response = await router.route_model(
                prompt=prompt,
                model_choice=state.model_choice,
                temperature=state.temperature,
                max_tokens=state.max_tokens,
                system_prompt=full_system_prompt
            )
            
            # Extract reasoning trace and citations if possible
            response_text, reasoning, citations = self._extract_response_components(response)
            
            state.response = response_text
            state.reasoning_trace = reasoning
            
            # Parse citations if they exist
            if citations:
                state.citations = self._parse_citations(citations)
            else:
                # Try to extract citations from the main response and reasoning trace
                state.citations = self._extract_implicit_citations(response_text, reasoning)
            
            # Add confidence scoring
            state.confidence_score = self._calculate_confidence(response_text, reasoning, state.citations)
            
            logger.info(f"{state.model_choice} LLM executed successfully with structured reasoning")
        except Exception as e:
            logger.error(f"Error executing {state.model_choice} LLM: {str(e)}")
            state.error = f"LLM execution error: {str(e)}"
            state.use_fallback = True
        
        return state
    
    def _extract_implicit_citations(self, response: str, reasoning: str = None) -> List[Dict[str, Any]]:
        """Extract citations that might be embedded in the text rather than explicitly marked."""
        import re
        combined_text = f"{response}\n{reasoning if reasoning else ''}"
        
        citations = []
        
        # Pattern for Kenya Law citations
        kenya_law_patterns = [
            r'\[(\d{4})\]\s+(\w+)',  # [2022] eKLR
            r'(\w+)\s+v\s+(\w+)',    # Party v Party
            r'(\w+\s+Act)',          # Employment Act
            r'(\w+\s+No\.\s+\d+\s+of\s+\d{4})',  # Act No. X of YYYY
            r'Constitution of Kenya, (Article \d+)',  # Constitution articles
            r'Section (\d+) of the (\w+\s+Act)',  # Sections of Acts
        ]
        
        for pattern in kenya_law_patterns:
            matches = re.findall(pattern, combined_text)
            for match in matches:
                # Convert match tuple or string to a standard format
                if isinstance(match, tuple):
                    citation_text = " ".join(match)
                else:
                    citation_text = match
                    
                # Create a citation entry with a default URL if none exists
                citations.append({
                    "text": citation_text,
                    "url": f"https://new.kenyalaw.org/search?q={citation_text.replace(' ', '+')}"
                })
        
        # Remove duplicates
        unique_citations = []
        seen_texts = set()
        for citation in citations:
            if citation["text"] not in seen_texts:
                unique_citations.append(citation)
                seen_texts.add(citation["text"])
                
        return unique_citations
    
    def _calculate_confidence(self, response: str, reasoning: str = None, citations: List[Dict] = None) -> float:
        """Calculate a confidence score based on response quality indicators."""
        score = 0.5  # Start with a neutral score
        
        # Factor 1: Presence of reasoning trace
        if reasoning and len(reasoning) > 100:
            score += 0.1
            # Additional points for structured reasoning patterns
            if "issue" in reasoning.lower() and "rule" in reasoning.lower() and "conclusion" in reasoning.lower():
                score += 0.1
                
        # Factor 2: Citation quality
        if citations:
            score += min(0.1, len(citations) * 0.02)  # Up to 0.1 for citations
            
        # Factor 3: Response comprehensiveness
        if len(response) > 500:
            score += 0.05
            
        # Factor 4: Legal terminology usage
        legal_terms = ["statute", "legislation", "precedent", "ruling", "judgment", "provision", "section", "article"]
        legal_term_count = sum(1 for term in legal_terms if term in response.lower())
        score += min(0.1, legal_term_count * 0.01)
        
        # Factor 5: Hesitation markers (negative)
        uncertainty_terms = ["uncertain", "unclear", "possibly", "might", "maybe", "not sure", "could be"]
        uncertainty_count = sum(1 for term in uncertainty_terms if term in response.lower())
        score -= min(0.1, uncertainty_count * 0.02)
        
        # Ensure score is within 0-1 range
        return max(0.1, min(0.99, score))
    
    async def _fallback_executor(self, state: AgentState) -> AgentState:
        """Execute the fallback LLM when the primary one fails."""
        logger.info("Executing fallback LLM with simplified structure")
        
        try:
            # Simplified prompt for fallback LLM
            simplified_prompt = f"""
            You are a legal assistant specializing in Kenyan law. Answer the following query using the provided context.
            Include legal references when possible.
            
            Query: {state.query}
            
            Context:
            {state.context}
            
            Provide your answer in a clear and structured format.
            """
            
            # Call the fallback LLM
            response = await self.fallback_llm.invoke(simplified_prompt)
            
            # Extract components with a more lenient approach
            response_text, reasoning, citations = self._extract_response_components(response)
            
            state.response = response_text
            state.reasoning_trace = reasoning
            
            # Parse citations if they exist
            if citations:
                state.citations = self._parse_citations(citations)
            else:
                # Try to extract implicit citations with lower confidence
                state.citations = self._extract_implicit_citations(response_text)
            
            # Set a fixed, lower confidence score for fallback responses
            state.confidence_score = 0.5
            
            logger.info("Fallback LLM executed successfully")
        except Exception as e:
            logger.error(f"Error executing fallback LLM: {str(e)}")
            state.error = f"Fallback LLM execution error: {str(e)}"
            # Return a minimal response to avoid complete failure
            state.response = "I apologize, but I encountered an error while processing your request. " + \
                            "Please try again or rephrase your query."
            state.confidence_score = 0.1
        
        return state
    
    async def _citation_formatter(self, state: AgentState) -> AgentState:
        """Format the citations in the response and add confidence information."""
        if not state.response:
            return state
        
        # If we have proper citations, format them
        if state.citations:
            # Group citations by type
            case_citations = []
            statute_citations = []
            other_citations = []
            
            for citation in state.citations:
                text = citation['text'].lower()
                if 'v' in text or 'ekr' in text or '[20' in text:  # Case patterns
                    case_citations.append(citation)
                elif 'act' in text or 'section' in text or 'article' in text:  # Statute patterns
                    statute_citations.append(citation)
                else:
                    other_citations.append(citation)
            
            # Format citations by group
            citations_text = "## Citations\n\n"
            
            if case_citations:
                citations_text += "### Cases\n"
                for i, citation in enumerate(case_citations, 1):
                    citations_text += f"{i}. [{citation['text']}]({citation['url']})\n"
                citations_text += "\n"
                
            if statute_citations:
                citations_text += "### Statutes and Regulations\n"
                for i, citation in enumerate(statute_citations, 1):
                    citations_text += f"{i}. [{citation['text']}]({citation['url']})\n"
                citations_text += "\n"
                
            if other_citations:
                citations_text += "### Other References\n"
                for i, citation in enumerate(other_citations, 1):
                    citations_text += f"{i}. [{citation['text']}]({citation['url']})\n"
            
            # Add the citations to the response
            state.response = f"{state.response}\n\n{citations_text}"
        
        # If we have a reasoning trace, add it
        if state.reasoning_trace:
            state.response = f"{state.response}\n\n## Reasoning Process\n\n{state.reasoning_trace}"
        
        # Add confidence score if available
        if hasattr(state, 'confidence_score') and state.confidence_score is not None:
            confidence_percentage = int(state.confidence_score * 100)
            confidence_text = f"\n\n*Response confidence: {confidence_percentage}%*"
            state.response += confidence_text
        
        logger.info("Response formatted with citations, reasoning trace, and confidence score")
        return state
    
    def _should_use_fallback(self, state: AgentState) -> bool:
        """Determine if we should use the fallback LLM."""
        # Use fallback if explicitly set or if there was an error
        if state.use_fallback or state.error is not None:
            return True
            
        # Also use fallback if the response is empty or too short
        if not state.response or len(state.response) < 50:
            logger.warning("Response too short, using fallback")
            return True
            
        # Use fallback if confidence is too low (if available)
        if hasattr(state, 'confidence_score') and state.confidence_score is not None:
            if state.confidence_score < 0.3:
                logger.warning(f"Low confidence score ({state.confidence_score}), using fallback")
                return True
                
        return False
    
    def _extract_response_components(self, response: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Extract the main response, reasoning trace, and citations from the LLM output."""
        # Default values
        main_response = response
        reasoning_trace = None
        citations = None
        
        # Extract reasoning trace if present
        if "REASONING TRACE:" in response:
            parts = response.split("REASONING TRACE:", 1)
            main_response = parts[0].strip()
            reasoning_part = parts[1].strip()
            
            # Check if there are citations after the reasoning trace
            if "CITATIONS:" in reasoning_part:
                reasoning_citations = reasoning_part.split("CITATIONS:", 1)
                reasoning_trace = reasoning_citations[0].strip()
                citations = reasoning_citations[1].strip()
            else:
                reasoning_trace = reasoning_part
        
        # If no reasoning trace section but citations exist
        elif "CITATIONS:" in response:
            parts = response.split("CITATIONS:", 1)
            main_response = parts[0].strip()
            citations = parts[1].strip()
        
        return main_response, reasoning_trace, citations
    
    def _parse_citations(self, citations_text: str) -> List[Dict[str, Any]]:
        """Parse citations text into structured format."""
        citation_list = []
        
        # Simple parsing - looking for markdown links
        import re
        
        # Find all markdown links [text](url)
        matches = re.findall(r'\[(.*?)\]\((.*?)\)', citations_text)
        
        for text, url in matches:
            citation_list.append({
                "text": text,
                "url": url
            })
        
        # If no markdown links found, try to parse line by line
        if not citation_list:
            lines = citations_text.split("\n")
            for line in lines:
                line = line.strip()
                if line and "http" in line:
                    # Try to extract a URL
                    url_match = re.search(r'(https?://[^\s]+)', line)
                    if url_match:
                        url = url_match.group(1)
                        # Use the rest of the line as text, or the URL if nothing else
                        text = line.replace(url, "").strip() or url
                        citation_list.append({
                            "text": text,
                            "url": url
                        })        
        return citation_list
        
    async def run_query(self, query: str, files: List[UploadFile] = None, urls: List[HttpUrl] = None):
        """Run a query through the agent."""
        # Process files if provided
        file_contents = []
        if files:
            for file in files:
                content = await file.read()
                file_contents.append({
                    "filename": file.filename,
                    "content": content,
                    "file_type": file.content_type
                })
        
        # Create the initial state
        state = AgentState(
            query=query,
            urls=urls or [],
            file_contents=file_contents
        )
          # Execute the graph
        try:
            # Try the new API style
            result = await self.graph.ainvoke(state)
        except AttributeError:
            try:
                # Try the older API style
                result = await self.graph.arun(state)
            except AttributeError:
                # Fallback to synchronous API
                result = self.graph.invoke(state)
        
        # Return the final response
        return {
            "response": result.response,
            "error": result.error
        }
    
    async def run_summarize(self, query: str, files: List[UploadFile] = None, urls: List[HttpUrl] = None):
        """Run a summarization through the agent."""
        # Process files if provided
        file_contents = []
        if files:
            for file in files:
                content = await file.read()
                file_contents.append({
                    "filename": file.filename,
                    "content": content,
                    "file_type": file.content_type
                })
        
        # Add summarization directive to the query
        if not query:
            query = "Please summarize the content of these documents."
        else:
            query = f"Please summarize the content of these documents, focusing on: {query}"
        
        # Create the initial state
        state = AgentState(
            query=query,
            urls=urls or [],
            file_contents=file_contents
        )
        
        # Execute the graph
        result = await self.graph.ainvoke(state)
        
        # Return the final response
        return {
            "response": result.response,
            "error": result.error
        }
    
    async def run_draft(self, document_type: str, context: str, files: List[UploadFile] = None, urls: List[HttpUrl] = None):
        """Run a document drafting through the agent."""
        # Process files if provided
        file_contents = []
        if files:
            for file in files:
                content = await file.read()
                file_contents.append({
                    "filename": file.filename,
                    "content": content,
                    "file_type": file.content_type
                })
        
        # Create the drafting query
        query = f"Draft a {document_type} with the following context: {context}"
        
        # Create the initial state
        state = AgentState(
            query=query,
            urls=urls or [],
            file_contents=file_contents,
            document_type=document_type,
        )
        
        # Execute the graph
        result = await self.graph.ainvoke(state)
        
        # Return the final response
        return {
            "response": result.response,
            "error": result.error
        }
