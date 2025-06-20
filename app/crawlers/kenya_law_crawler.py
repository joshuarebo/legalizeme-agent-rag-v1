"""
Kenya Law Crawler - For regularly crawling and indexing Kenya Law website
"""
import os
import asyncio
import httpx
import json
import time
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
from app.utils.logger import get_logger
from app.parsers.web_parser import WebParser
from app.parsers.document_parser import DocumentParser
from app.rag.retriever import KenyaLawRetriever

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

class KenyaLawCrawler:
    """
    Crawler for Kenya Law website to keep the vector database up to date.
    
    This enhanced crawler handles:
    - Robust rate limiting and retry logic
    - Detailed metadata extraction
    - Scheduled crawling with state persistence
    - Different document types (judgments, legislation, etc.)
    """
    def __init__(self):
        """Initialize the crawler with configuration."""
        # Base URLs for different sections
        self.base_url = os.getenv("KENYA_LAW_BASE_URL", "https://new.kenyalaw.org")
        self.sections = {
            "judgments": "/judgments/",
            "legislation": "/legislation/",
            "constitution": "/akn/ke/act/2010/constitution/eng@2010-09-03",
            "gazettes": "/gazettes/",
            "bills": "/bills/"
        }
        
        # Storage locations
        self.data_dir = os.getenv("CRAWL_DATA_DIR", "./data/kenya_law")
        self.raw_data_dir = os.path.join(self.data_dir, "raw")
        self.processed_data_dir = os.path.join(self.data_dir, "processed")
        
        # Ensure directories exist
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.processed_data_dir, exist_ok=True)
        
        # Crawl configuration
        self.rate_limit = float(os.getenv("CRAWL_RATE_LIMIT", "1.0"))  # requests per second
        
        # Handle potential comment in environment variable
        max_pages_env = os.getenv("CRAWLER_MAX_PAGES", "50")
        try:
            self.max_pages_per_section = int(max_pages_env.split('#')[0].strip())
        except (ValueError, AttributeError):
            logger.warning(f"Invalid CRAWLER_MAX_PAGES value: {max_pages_env}, using default of 50")
            self.max_pages_per_section = 50
            
        self.max_retries = int(os.getenv("CRAWL_MAX_RETRIES", "3"))
        self.user_agent = os.getenv("CRAWL_USER_AGENT", "CounselLegalAI/1.0")
        
        # Initialize parsers and retriever
        self.web_parser = WebParser()
        self.document_parser = DocumentParser()
        self.retriever = KenyaLawRetriever()
        
        # Crawl state
        self.visited_urls = set()
        self.documents_crawled = 0
        self.last_request_time = 0
        
        # Track last crawl time
        self.last_crawl_time = {}
        for section in self.sections:
            self.last_crawl_time[section] = None
            
        # Track what we've already processed
        self.crawl_state_file = os.path.join(self.data_dir, "crawl_state.json")
        self.load_state()
    
    async def crawl_all_sections(self):
        """Crawl all sections of Kenya Law website."""
        logger.info("Starting full crawl of Kenya Law website")
        
        try:
            for section, path in self.sections.items():
                logger.info(f"Crawling section: {section}")
                await self.crawl_section(section, path)
        
        except Exception as e:
            logger.error(f"Error during full crawl: {str(e)}")
        
        logger.info("Completed full crawl of Kenya Law website")
    
    async def crawl_section(self, section: str, path: str):
        """
        Crawl a specific section of the Kenya Law website.
        
        Args:
            section: The section name
            path: The URL path for the section
        """
        try:
            section_url = f"{self.base_url}{path}"
            
            # Get the index page for the section
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(section_url)
                response.raise_for_status()
                
                # Parse the HTML to find links to documents
                soup = BeautifulSoup(response.text, "html.parser")
                
                # The selectors would need to be customized for the actual Kenya Law website structure
                if section == "judgments":
                    links = soup.select("a.judgment-link") or soup.select("a[href*='/judgments/']")
                elif section == "legislation":
                    links = soup.select("a.legislation-link") or soup.select("a[href*='/legislation/']")
                elif section == "constitution":
                    # For constitution, we directly process the main page
                    await self._process_document(section_url, "constitution")
                    return
                elif section == "gazettes":
                    links = soup.select("a.gazette-link") or soup.select("a[href*='/gazettes/']")
                elif section == "bills":
                    links = soup.select("a.bill-link") or soup.select("a[href*='/bills/']")
                else:
                    links = []
                
                # If we can't find links with specific selectors, try a more general approach
                if not links:
                    # Try to find all links that point to this section
                    links = soup.select(f"a[href*='{path}']")
                
                # Process document links (limited by max_pages_per_section)
                count = 0
                for link in links:
                    if count >= self.max_pages_per_section:
                        break
                    
                    href = link.get("href")
                    if href:
                        # Make sure we have the full URL
                        if href.startswith("/"):
                            document_url = f"{self.base_url}{href}"
                        elif href.startswith("http"):
                            document_url = href
                        else:
                            document_url = f"{self.base_url}/{href}"
                        
                        # Process the document
                        await self._process_document(document_url, section)
                        count += 1
                        
                        # Small delay to avoid overloading the server
                        await asyncio.sleep(1)
            
            # Update last crawl time for this section
            self.last_crawl_time[section] = datetime.now()
            logger.info(f"Completed crawl of section {section}, processed {count} documents")
            
        except Exception as e:
            logger.error(f"Error crawling section {section}: {str(e)}")
    
    async def _process_document(self, url: str, document_type: str):
        """
        Process a single document from Kenya Law.
        
        Args:
            url: The URL of the document
            document_type: The type of document (judgments, legislation, etc.)
        """
        try:
            logger.info(f"Processing document: {url}")
            
            # Parse the document using our web parser
            content = await self.web_parser.parse(url)
            
            if not content or len(content) < 100:
                logger.warning(f"Insufficient content extracted from {url}, skipping")
                return
            
            # Extract document title
            title = self._extract_title(content, url)
            
            # Create document metadata
            metadata = {
                "source": url,
                "title": title,
                "type": document_type,
                "date_crawled": datetime.now().isoformat(),
                "date_published": self._extract_date(content, url)
            }
            
            # Index the document in our vector store
            from langchain.schema import Document
            
            doc = Document(
                page_content=content,
                metadata=metadata
            )
            
            # Add to document store and update embeddings
            docs = [doc]
            self.retriever.document_store.write_documents(docs)
            self.retriever.document_store.update_embeddings(self.retriever.retriever)
            
            logger.info(f"Successfully indexed document: {title}")
            
        except Exception as e:
            logger.error(f"Error processing document {url}: {str(e)}")
    
    def _extract_title(self, content: str, url: str) -> str:
        """
        Extract the title from document content.
        
        Args:
            content: The document content
            url: The document URL
            
        Returns:
            Extracted title or a fallback based on URL
        """
        # Try to find a title pattern in the content
        title_match = re.search(r'Title:\s*(.*?)(?:\n|$)', content)
        if title_match:
            return title_match.group(1).strip()
        
        # Try first line as title
        lines = content.strip().split("\n")
        if lines and len(lines[0]) < 200:  # Reasonable title length
            return lines[0].strip()
        
        # Fallback to URL-based title
        path_parts = url.rstrip('/').split('/')
        last_part = path_parts[-1]
        
        # Clean up the URL part
        last_part = last_part.replace('-', ' ').replace('_', ' ')
        
        return last_part.title()
    
    def _extract_date(self, content: str, url: str) -> Optional[str]:
        """
        Extract the publication date from document content.
        
        Args:
            content: The document content
            url: The document URL
            
        Returns:
            Extracted date or None
        """
        # Try to find date patterns in the content
        date_patterns = [
            r'Date:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Published on:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}(?:st|nd|rd|th)? [A-Za-z]+ \d{4})'  # e.g., "1st January 2022"
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, content)
            if date_match:
                return date_match.group(1).strip()
        
        # Try to extract date from URL
        url_date_match = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', url)
        if url_date_match:
            year, month, day = url_date_match.groups()
            return f"{day}/{month}/{year}"
        
        # Fallback to current date
        return datetime.now().strftime("%d/%m/%Y")
    
    async def crawl_recent_updates(self):
        """
        Crawl only recent updates from Kenya Law website.
        More efficient for regular updates.
        """
        logger.info("Starting crawl for recent updates")
        
        try:
            # Prioritize judgments and legislation for recent updates
            priority_sections = ["judgments", "legislation", "gazettes"]
            
            for section in priority_sections:
                path = self.sections[section]
                section_url = f"{self.base_url}{path}"
                
                # Modify URL for recent updates if applicable
                if section == "judgments":
                    section_url = f"{self.base_url}/judgments/recent"
                elif section == "legislation":
                    section_url = f"{self.base_url}/legislation/recent"
                
                # Crawl with reduced page limit for efficiency
                temp_max_pages = self.max_pages_per_section
                self.max_pages_per_section = 2  # Only get the most recent pages
                await self.crawl_section(section, path)
                self.max_pages_per_section = temp_max_pages
        
        except Exception as e:
            logger.error(f"Error during recent updates crawl: {str(e)}")
        
        logger.info("Completed crawl for recent updates")
    
    def get_crawl_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the last crawl.
        
        Returns:
            Dictionary with crawl statistics
        """
        stats = {
            "sections": {},
            "total_documents": self.retriever.document_store.get_document_count()
        }
        
        for section, last_time in self.last_crawl_time.items():
            stats["sections"][section] = {
                "last_crawled": last_time.isoformat() if last_time else None
            }
        
        return stats
    
    def load_state(self):
        """Load the crawl state from disk."""
        try:
            if os.path.exists(self.crawl_state_file):
                with open(self.crawl_state_file, 'r') as f:
                    state = json.load(f)
                self.visited_urls = set(state.get("visited_urls", []))
                self.documents_crawled = state.get("documents_crawled", 0)
                
                # Load last crawl times for each section
                last_crawl_times = state.get("last_crawl_time", {})
                for section in self.sections:
                    self.last_crawl_time[section] = last_crawl_times.get(section)
                    
                logger.info(f"Loaded crawl state: {len(self.visited_urls)} URLs, {self.documents_crawled} documents")
            else:
                logger.info("No previous crawl state found")
        except Exception as e:
            logger.error(f"Error loading crawl state: {str(e)}")
    
    def save_state(self):
        """Save the crawl state to disk."""
        try:
            state = {
                "visited_urls": list(self.visited_urls),
                "documents_crawled": self.documents_crawled,
                "last_crawl_time": self.last_crawl_time,
                "last_updated": datetime.now().isoformat()
            }
            with open(self.crawl_state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"Saved crawl state: {len(self.visited_urls)} URLs, {self.documents_crawled} documents")
        except Exception as e:
            logger.error(f"Error saving crawl state: {str(e)}")
            
    async def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
          # If we've made a request too recently, sleep
        if time_since_last_request < (1.0 / self.rate_limit):
            sleep_time = (1.0 / self.rate_limit) - time_since_last_request
            await asyncio.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _classify_document_type(self, section: str, soup: BeautifulSoup) -> str:
        """
        Classify the type of legal document.
        
        Args:
            section: Legal section name
            soup: BeautifulSoup object
            
        Returns:
            Document type classification
        """
        if soup is None:
            logger.warning("Cannot classify document: BeautifulSoup object is None")
            return f"{section}_document"  # Default classification
            
        try:
            text = soup.get_text().lower()
            
            if section == "judgments":
                if any(word in text for word in ["criminal", "accused", "prosecution"]):
                    return "criminal_judgment"
                elif any(word in text for word in ["civil", "plaintiff", "defendant"]):
                    return "civil_judgment"
                elif any(word in text for word in ["constitutional", "petition", "bill of rights"]):
                    return "constitutional_judgment"
                else:
                    return "judgment"
            elif section == "legislation":
                if "act" in text:
                    return "act"
                elif "bill" in text:
                    return "bill"
                elif "regulation" in text:
                    return "regulation"
                else:
                    return "legislation"
            elif section == "constitution":
                return "constitutional_provision"
            else:
                return f"{section}_document"
        except Exception as e:
            logger.error(f"Error classifying document: {str(e)}")
            return f"{section}_document"

    def _classify_citation_type(self, citation_match) -> str:
        """
        Classify the type of legal citation.
        
        Args:
            citation_match: Regex match object or tuple
            
        Returns:
            Citation type classification
        """
        if isinstance(citation_match, tuple):
            text = " ".join(str(part) for part in citation_match).lower()
        else:
            text = str(citation_match).lower()
        
        if any(word in text for word in ["act", "chapter"]):
            return "statutory"
        elif any(word in text for word in ["article", "constitution"]):
            return "constitutional"
        elif "v" in text or "vs" in text or "versus" in text:
            return "case_law"
        else:
            return "unknown"

    def _generate_document_id(self, url: str) -> str:
        """
        Generate a unique document ID from URL.
        
        Args:
            url: Document URL
            
        Returns:
            Unique document ID
        """
        return hashlib.md5(url.encode()).hexdigest()

    async def _store_processed_document(self, document: Dict, section: str):
        """
        Store processed document to filesystem.
        
        Args:
            document: Processed document data
            section: Legal section name
        """
        try:
            # Create section directory
            section_dir = os.path.join(self.processed_data_dir, section)
            os.makedirs(section_dir, exist_ok=True)
            
            # Save document
            filename = f"{document['id']}.json"
            filepath = os.path.join(section_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(document, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Stored processed document: {filepath}")
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")

    async def _index_document(self, document: Dict):
        """
        Index document in vector database.
        
        Args:
            document: Processed document data
        """
        try:
            # Create chunks for indexing
            chunks = self._create_document_chunks(document)
            
            # Index each chunk
            for chunk in chunks:
                await self.retriever.add_document(
                    content=chunk["content"],
                    metadata={
                        **chunk["metadata"],
                        "document_id": document["id"],
                        "source_url": document["url"],
                        "section": document["section"],
                        "extraction_date": document["extraction_date"]
                    }
                )
            
            logger.debug(f"Indexed {len(chunks)} chunks for document {document['id']}")
            
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")

    def _create_document_chunks(self, document: Dict, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """
        Create chunks from document for vector indexing.
        
        Args:
            document: Document data
            chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks
            
        Returns:
            List of document chunks
        """
        chunks = []
        content = document["content"]
        
        if not content:
            return chunks
        
        # Split content into chunks
        start = 0
        chunk_id = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence end within the next 100 characters
                sentence_end = content.find('. ', end)
                if sentence_end != -1 and sentence_end < end + 100:
                    end = sentence_end + 1
            
            chunk_content = content[start:end].strip()
            
            if chunk_content:
                chunk = {
                    "content": chunk_content,
                    "metadata": {
                        "chunk_id": chunk_id,
                        "start_char": start,
                        "end_char": end,
                        "title": document["title"],
                        "document_type": document["metadata"].get("document_type"),
                        "court": document["metadata"].get("court"),
                        "date_published": document["metadata"].get("date_published"),
                        "citations": document.get("citations", []),
                        "entities": document.get("entities", {})
                    }
                }
                chunks.append(chunk)
                chunk_id += 1
            
            # Move start position with overlap
            start = max(start + chunk_size - overlap, end)
        
        return chunks

    async def schedule_periodic_crawl(self, interval_hours: int = 24):
        """
        Schedule periodic crawling of Kenya Law website.
        
        Args:
            interval_hours: Hours between crawl cycles
        """
        logger.info(f"Scheduling periodic crawl every {interval_hours} hours")
        
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            
            scheduler = AsyncIOScheduler()
            
            # Schedule full crawl
            scheduler.add_job(
                self.crawl_all_sections,
                trigger=IntervalTrigger(hours=interval_hours),
                id='periodic_crawl',
                replace_existing=True
            )
            
            # Schedule incremental updates more frequently
            scheduler.add_job(
                self.incremental_update,
                trigger=IntervalTrigger(hours=interval_hours // 4),
                id='incremental_update',
                replace_existing=True
            )
            
            scheduler.start()
            logger.info("Periodic crawl scheduler started successfully")
            
        except ImportError:
            logger.warning("APScheduler not available, periodic crawling disabled")
        except Exception as e:
            logger.error(f"Error setting up periodic crawl: {str(e)}")

    async def incremental_update(self):
        """
        Perform incremental update of recent documents.
        """
        logger.info("Starting incremental update")
        
        try:
            # Focus on recent documents from each section
            for section in self.sections:
                await self.crawl_with_enhanced_extraction(section, max_documents=10)
            
            logger.info("Incremental update completed")
            
        except Exception as e:
            logger.error(f"Error in incremental update: {str(e)}")
