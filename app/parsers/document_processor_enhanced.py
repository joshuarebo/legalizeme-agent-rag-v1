"""
Enhanced Document Processor for Phase 2
Handles PDF, HTML, and text documents with legal-specific processing
"""
import os
import asyncio
import hashlib
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import re
from dataclasses import dataclass

# Try to import the actual dependencies
try:
    import pymupdf as fitz
    from unstructured.partition.auto import partition
    from unstructured.partition.pdf import partition_pdf
    from unstructured.partition.html import partition_html
    from unstructured.chunking.title import chunk_by_title
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    fitz = None
    partition = None
    partition_pdf = None 
    partition_html = None
    chunk_by_title = None
    UNSTRUCTURED_AVAILABLE = False

from bs4 import BeautifulSoup
from app.utils.logger import get_logger
from app.utils.llm_factory import get_enhanced_llm, create_legal_prompt

logger = get_logger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata."""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    document_id: str
    start_char: int
    end_char: int

@dataclass
class ProcessedDocument:
    """Represents a fully processed legal document."""
    id: str
    title: str
    content: str
    chunks: List[DocumentChunk]
    metadata: Dict[str, Any]
    citations: List[Dict[str, Any]]
    entities: Dict[str, List[str]]
    processing_date: str

class EnhancedDocumentProcessor:
    """
    Enhanced document processor for legal documents.
    
    Features:
    - Multi-format support (PDF, HTML, text)
    - Legal metadata extraction
    - Citation parsing
    - Intelligent chunking
    - Entity extraction
    """
    
    def __init__(self):
        """Initialize the enhanced document processor."""
        self.temp_dir = os.getenv("TEMP_PDFS_DIR", "./data/temp_pdfs")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Processing configuration
        self.chunk_size = int(os.getenv("DOC_CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("DOC_CHUNK_OVERLAP", "200"))
        
        # Initialize LLM for content analysis
        self.llm = get_enhanced_llm("huggingface", "legal_analysis")
        
        # Legal document patterns
        self.legal_patterns = {
            "case_citation": [
                r'([A-Z][a-zA-Z\s&]+)\s+v\.?\s+([A-Z][a-zA-Z\s&]+)\s+\[(\d{4})\]\s*([A-Z]+)\s*(\d+)',
                r'([A-Z][a-zA-Z\s&]+)\s+(?:vs?\.?\s+|versus\s+)([A-Z][a-zA-Z\s&]+)\s+\((\d{4})\)'
            ],
            "statutory_citation": [
                r'(?:Section|Article)\s+(\d+[A-Za-z]?)\s+of\s+(?:the\s+)?([\w\s]+(?:Act|Constitution))',
                r'([\w\s]+Act)\s*,?\s*(?:Chapter\s+)?(\d+)\s*(?:of\s+)?(\d{4})'
            ],
            "court_name": [
                r'(?:High Court of Kenya|Court of Appeal|Supreme Court of Kenya)',
                r'(?:Environment and Land Court|Employment and Labour Relations Court)'
            ],
            "judge_name": [
                r'(?:Hon\.?\s+)?(?:Justice|Judge)\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.)',
                r'(?:Hon\.?\s+)?(?:Chief Justice|Deputy Chief Justice)\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.)'
            ]
        }

    async def process_document(self, file_path: str, document_type: str = "auto") -> Optional[ProcessedDocument]:
        """
        Process a document with enhanced legal analysis.
        
        Args:
            file_path: Path to the document file
            document_type: Type of document processing to apply
            
        Returns:
            ProcessedDocument or None if processing failed
        """
        try:
            logger.info(f"Processing document: {file_path}")
            
            # Determine file type and extract content
            if file_path.lower().endswith('.pdf'):
                content, raw_metadata = await self._process_pdf(file_path)
            elif file_path.lower().endswith(('.html', '.htm')):
                content, raw_metadata = await self._process_html(file_path)
            elif file_path.lower().endswith('.txt'):
                content, raw_metadata = await self._process_text(file_path)
            else:
                logger.error(f"Unsupported file type: {file_path}")
                return None
            
            if not content:
                logger.error(f"No content extracted from {file_path}")
                return None
            
            # Generate document ID
            doc_id = self._generate_document_id(file_path, content)
            
            # Extract enhanced metadata
            metadata = await self._extract_enhanced_metadata(content, raw_metadata, document_type)
            
            # Extract citations
            citations = await self._extract_citations(content)
            
            # Extract legal entities
            entities = await self._extract_legal_entities(content)
            
            # Create intelligent chunks
            chunks = await self._create_intelligent_chunks(content, doc_id, metadata)
            
            # Create processed document
            processed_doc = ProcessedDocument(
                id=doc_id,
                title=metadata.get("title", os.path.basename(file_path)),
                content=content,
                chunks=chunks,
                metadata=metadata,
                citations=citations,
                entities=entities,
                processing_date=datetime.now().isoformat()
            )
            
            logger.info(f"Successfully processed document {doc_id} with {len(chunks)} chunks")
            return processed_doc
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return None

    async def _process_pdf(self, file_path: str) -> tuple[str, Dict]:
        """Process PDF document."""
        content = ""
        metadata = {}
        
        try:
            # Try unstructured.io first
            if UNSTRUCTURED_AVAILABLE and partition_pdf:
                logger.debug("Using unstructured.io for PDF processing")
                elements = partition_pdf(file_path)
                content = "\n".join([str(element) for element in elements])
                
                # Extract metadata from elements
                for element in elements:
                    if hasattr(element, 'metadata') and element.metadata:
                        metadata.update(element.metadata.to_dict())
            
            # Fallback to PyMuPDF
            elif fitz:
                logger.debug("Using PyMuPDF for PDF processing")
                doc = fitz.open(file_path)
                
                # Extract metadata
                metadata = doc.metadata or {}
                
                # Extract text
                text_blocks = []
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text_blocks.append(page.get_text())
                
                content = "\n".join(text_blocks)
                doc.close()
            
            else:
                logger.warning("No PDF processing library available")
                return "", {}
                
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            
        return content, metadata

    async def _process_html(self, file_path: str) -> tuple[str, Dict]:
        """Process HTML document."""
        content = ""
        metadata = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Try unstructured.io first
            if UNSTRUCTURED_AVAILABLE and partition_html:
                logger.debug("Using unstructured.io for HTML processing")
                elements = partition_html(text=html_content)
                content = "\n".join([str(element) for element in elements])
            
            # Fallback to BeautifulSoup
            else:
                logger.debug("Using BeautifulSoup for HTML processing")
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract metadata
                title_tag = soup.find('title')
                metadata['title'] = title_tag.get_text() if title_tag else ""
                
                # Extract main content
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                content = soup.get_text()
                
        except Exception as e:
            logger.error(f"Error processing HTML {file_path}: {str(e)}")
            
        return content, metadata

    async def _process_text(self, file_path: str) -> tuple[str, Dict]:
        """Process text document."""
        content = ""
        metadata = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic metadata
            metadata = {
                'title': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path)
            }
                
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            
        return content, metadata

    async def _extract_enhanced_metadata(self, content: str, raw_metadata: Dict, document_type: str) -> Dict:
        """Extract enhanced legal metadata from document content."""
        metadata = {**raw_metadata}
        
        try:
            # Use LLM for metadata extraction
            if self.llm:
                prompt = create_legal_prompt("document_summarization", document=content[:2000])
                
                try:
                    summary_response = await self.llm.invoke(prompt)
                    metadata['ai_summary'] = summary_response
                except Exception as e:
                    logger.error(f"Error generating AI summary: {str(e)}")
            
            # Extract document type
            metadata['document_type'] = self._classify_document_type(content, document_type)
            
            # Extract dates
            date_patterns = [
                r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})\b',
                r'\b(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b',
                r'\b(\d{1,2}\s+\w+\s+\d{4})\b'
            ]
            
            for pattern in date_patterns:
                dates = re.findall(pattern, content)
                if dates:
                    metadata['extracted_dates'] = dates[:5]  # Keep first 5 dates
                    break
            
            # Extract court information
            for pattern in self.legal_patterns['court_name']:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    metadata['court'] = matches[0]
                    break
            
            # Extract judge information
            for pattern in self.legal_patterns['judge_name']:
                matches = re.findall(pattern, content)
                if matches:
                    metadata['judge'] = matches[0]
                    break
            
            # Extract case number or reference
            case_patterns = [
                r'(?:Case|Petition|Appeal|Application)\s+No\.?\s*(\d+(?:\/\d+)?)',
                r'(\w+\s+\d+\s+of\s+\d{4})'
            ]
            
            for pattern in case_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    metadata['case_number'] = matches[0]
                    break
            
        except Exception as e:
            logger.error(f"Error extracting enhanced metadata: {str(e)}")
        
        return metadata

    async def _extract_citations(self, content: str) -> List[Dict]:
        """Extract legal citations from content."""
        citations = []
        
        try:
            # Extract case citations
            for pattern in self.legal_patterns['case_citation']:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    citation = {
                        'type': 'case_law',
                        'raw_text': ' '.join(match) if isinstance(match, tuple) else match,
                        'components': match if isinstance(match, tuple) else [match]
                    }
                    citations.append(citation)
            
            # Extract statutory citations
            for pattern in self.legal_patterns['statutory_citation']:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    citation = {
                        'type': 'statutory',
                        'raw_text': ' '.join(match) if isinstance(match, tuple) else match,
                        'components': match if isinstance(match, tuple) else [match]
                    }
                    citations.append(citation)
            
        except Exception as e:
            logger.error(f"Error extracting citations: {str(e)}")
        
        return citations

    async def _extract_legal_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract legal entities from content."""
        entities = {
            'courts': [],
            'judges': [],
            'legal_concepts': [],
            'organizations': []
        }
        
        try:
            # Extract courts
            for pattern in self.legal_patterns['court_name']:
                matches = re.findall(pattern, content, re.IGNORECASE)
                entities['courts'].extend(matches)
            
            # Extract judges
            for pattern in self.legal_patterns['judge_name']:
                matches = re.findall(pattern, content)
                entities['judges'].extend([match.strip() for match in matches])
            
            # Extract legal concepts
            legal_concepts = [
                'constitutional law', 'administrative law', 'criminal law', 'civil procedure',
                'human rights', 'judicial review', 'due process', 'natural justice',
                'burden of proof', 'standard of proof', 'precedent', 'stare decisis'
            ]
            
            for concept in legal_concepts:
                if concept.lower() in content.lower():
                    entities['legal_concepts'].append(concept)
            
        except Exception as e:
            logger.error(f"Error extracting legal entities: {str(e)}")
        
        return entities

    async def _create_intelligent_chunks(self, content: str, doc_id: str, metadata: Dict) -> List[DocumentChunk]:
        """Create intelligent chunks based on document structure."""
        chunks = []
        
        try:
            # Try unstructured.io chunking first
            if UNSTRUCTURED_AVAILABLE and chunk_by_title:
                try:
                    # This would need the original elements, so skip for now
                    pass
                except Exception:
                    pass
            
            # Fallback to custom chunking
            chunks = self._create_semantic_chunks(content, doc_id, metadata)
            
        except Exception as e:
            logger.error(f"Error creating intelligent chunks: {str(e)}")
            # Final fallback to simple chunking
            chunks = self._create_simple_chunks(content, doc_id, metadata)
        
        return chunks

    def _create_semantic_chunks(self, content: str, doc_id: str, metadata: Dict) -> List[DocumentChunk]:
        """Create semantic chunks based on legal document structure."""
        chunks = []
        
        # Split by common legal document sections
        section_patterns = [
            r'\n\s*(?:FACTS?|BACKGROUND)\s*\n',
            r'\n\s*(?:ISSUES?)\s*\n',
            r'\n\s*(?:ANALYSIS|DISCUSSION)\s*\n',
            r'\n\s*(?:HELD|HOLDING)\s*\n',
            r'\n\s*(?:CONCLUSION|RULING)\s*\n',
            r'\n\s*(?:ORDER|ORDERS)\s*\n'
        ]
        
        # Try to split by sections
        sections = [content]
        for pattern in section_patterns:
            new_sections = []
            for section in sections:
                parts = re.split(pattern, section, flags=re.IGNORECASE)
                new_sections.extend(parts)
            sections = [s.strip() for s in new_sections if s.strip()]
        
        # Create chunks from sections
        chunk_id = 0
        current_pos = 0
        
        for section in sections:
            if len(section) <= self.chunk_size:
                # Section fits in one chunk
                chunk = DocumentChunk(
                    content=section,
                    metadata={**metadata, 'section_type': 'semantic'},
                    chunk_id=f"{doc_id}_chunk_{chunk_id}",
                    document_id=doc_id,
                    start_char=current_pos,
                    end_char=current_pos + len(section)
                )
                chunks.append(chunk)
                chunk_id += 1
                current_pos += len(section)
            else:
                # Split large section into smaller chunks
                section_chunks = self._split_section(section, doc_id, chunk_id, current_pos, metadata)
                chunks.extend(section_chunks)
                chunk_id += len(section_chunks)
                current_pos += len(section)
        
        return chunks

    def _create_simple_chunks(self, content: str, doc_id: str, metadata: Dict) -> List[DocumentChunk]:
        """Create simple overlapping chunks."""
        chunks = []
        
        start = 0
        chunk_id = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                sentence_end = content.find('. ', end)
                if sentence_end != -1 and sentence_end < end + 100:
                    end = sentence_end + 1
            
            chunk_content = content[start:end].strip()
            
            if chunk_content:
                chunk = DocumentChunk(
                    content=chunk_content,
                    metadata={**metadata, 'section_type': 'simple'},
                    chunk_id=f"{doc_id}_chunk_{chunk_id}",
                    document_id=doc_id,
                    start_char=start,
                    end_char=end
                )
                chunks.append(chunk)
                chunk_id += 1
            
            start = max(start + self.chunk_size - self.chunk_overlap, end)
        
        return chunks

    def _split_section(self, section: str, doc_id: str, start_chunk_id: int, start_pos: int, metadata: Dict) -> List[DocumentChunk]:
        """Split a large section into smaller chunks."""
        chunks = []
        
        start = 0
        chunk_id = start_chunk_id
        
        while start < len(section):
            end = start + self.chunk_size
            
            if end < len(section):
                # Try to break at paragraph or sentence
                para_break = section.rfind('\n\n', start, end)
                if para_break > start:
                    end = para_break
                else:
                    sent_break = section.rfind('. ', start, end)
                    if sent_break > start:
                        end = sent_break + 1
            
            chunk_content = section[start:end].strip()
            
            if chunk_content:
                chunk = DocumentChunk(
                    content=chunk_content,
                    metadata={**metadata, 'section_type': 'split_section'},
                    chunk_id=f"{doc_id}_chunk_{chunk_id}",
                    document_id=doc_id,
                    start_char=start_pos + start,
                    end_char=start_pos + end
                )
                chunks.append(chunk)
                chunk_id += 1
            
            start = max(start + self.chunk_size - self.chunk_overlap, end)
        
        return chunks

    def _classify_document_type(self, content: str, document_type: str) -> str:
        """Classify the document type based on content."""
        if document_type != "auto":
            return document_type
        
        content_lower = content.lower()
        
        # Check for judgment indicators
        if any(word in content_lower for word in ['judgment', 'ruling', 'held', 'court']):
            if any(word in content_lower for word in ['criminal', 'accused', 'prosecution']):
                return 'criminal_judgment'
            elif any(word in content_lower for word in ['civil', 'plaintiff', 'defendant']):
                return 'civil_judgment'
            else:
                return 'judgment'
        
        # Check for legislation indicators
        elif any(word in content_lower for word in ['act', 'bill', 'statute', 'regulation']):
            return 'legislation'
        
        # Check for constitutional indicators
        elif any(word in content_lower for word in ['constitution', 'constitutional', 'bill of rights']):
            return 'constitutional'
        
        else:
            return 'legal_document'

    def _generate_document_id(self, file_path: str, content: str) -> str:
        """Generate unique document ID."""
        combined = f"{file_path}_{len(content)}_{content[:100]}"
        return hashlib.md5(combined.encode()).hexdigest()
