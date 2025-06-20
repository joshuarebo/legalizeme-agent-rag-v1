"""
Web Parser - For parsing web pages and URLs
"""
import os
from typing import Dict, Any, List, Optional
import asyncio
import httpx
from bs4 import BeautifulSoup
import tempfile

# Try to import real dependencies first, fall back to stubs if not available
USING_UNSTRUCTURED = False
try:
    from unstructured.partition.html import partition as partition_html
    USING_UNSTRUCTURED = True
except (ImportError, ModuleNotFoundError):
    from app.utils.stubs.unstructured.partition.html import partition as partition_html
    USING_UNSTRUCTURED = False

from app.utils.logger import get_logger

logger = get_logger(__name__)

class WebParser:
    """
    Parser for web pages and URLs.
    """
    
    def __init__(self):
        """Initialize the web parser."""
        self.temp_dir = os.getenv("PDF_TEMP_DIR", "./data/temp_pdfs")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        if not USING_UNSTRUCTURED:
            logger.warning("Using stub implementation for HTML parsing")
        else:
            logger.info("Using real HTML parsing libraries")
        
        # Kenya Law specific selectors (would be customized for their site structure)
        self.kenya_law_selectors = {
            "judgment": {
                "title": "h1.title",
                "content": "div.judgment-content",
                "date": "div.meta-data span.date",
                "citation": "div.meta-data span.citation"
            },
            "legislation": {
                "title": "h1.title",
                "content": "div.legislation-content",
                "date": "div.meta-data span.date",
                "citation": "div.meta-data span.citation"
            }
        }
    
    async def parse_url(self, url: str) -> Dict[str, Any]:
        """
        Parse a URL and extract its content.
        
        Args:
            url: The URL to parse
            
        Returns:
            Dict with the parsed content and metadata
        """
        try:
            # Download the page
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
            
            # Parse the HTML
            html_content = response.text
            parsed_content = await self.parse_html(html_content, url)
            
            # Add the URL as source
            if isinstance(parsed_content, dict):
                parsed_content["meta"] = parsed_content.get("meta", {})
                parsed_content["meta"]["source"] = url
            
            return parsed_content
        
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {str(e)}")
            return {
                "content": f"Error parsing URL: {str(e)}",
                "meta": {
                    "source": url,
                    "error": str(e)
                }
            }
    
    async def parse_html(self, html_content: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse HTML content and extract text and metadata.
        
        Args:
            html_content: Raw HTML content
            url: Optional source URL
            
        Returns:
            Dict with the parsed content and metadata
        """
        if not html_content:
            return {"content": "", "meta": {"source": url if url else "unknown"}}
        
        # Try different parsing strategies
        try:
            # First try with custom parsing for Kenya Law
            if url and "kenyalaw.org" in url:
                parsed_data = await self._parse_kenya_law(html_content, url)
                if parsed_data.get("content"):
                    return parsed_data
            
            # Then try with unstructured.io
            unstructured_text = await self._parse_with_unstructured(html_content)
            if unstructured_text:
                return {
                    "content": unstructured_text,
                    "meta": {
                        "source": url if url else "unknown",
                        "parser": "unstructured.io"
                    }
                }
            
            # Finally fall back to BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Extract title
            title = soup.title.text.strip() if soup.title else ""
            
            # Extract main content (basic implementation)
            # In a production system, this would be more sophisticated
            content_elements = []
            
            # Try to find main content containers
            main_elements = soup.select("main, article, .content, .main, #content, #main")
            if main_elements:
                for element in main_elements:
                    content_elements.append(element.get_text(strip=True, separator="\n"))
            else:
                # If no main content containers, take the body text
                content_elements.append(soup.body.get_text(strip=True, separator="\n") if soup.body else "")
            
            content = "\n\n".join([e for e in content_elements if e])
            
            return {
                "content": content,
                "meta": {
                    "title": title,
                    "source": url if url else "unknown",
                    "parser": "BeautifulSoup"
                }
            }
        
        except Exception as e:
            logger.error(f"Error parsing HTML: {str(e)}")
            return {
                "content": f"Error parsing HTML: {str(e)}",
                "meta": {
                    "source": url if url else "unknown",
                    "error": str(e)
                }
            }
    
    async def _parse_with_unstructured(self, html_content: str) -> str:
        """Parse HTML with unstructured.io."""
        if not USING_UNSTRUCTURED:
            logger.warning("Unstructured.io is not available, using stub implementation")
            return f"[Stub] Parsed HTML content ({len(html_content)} characters)"
            
        # Create a temporary file for the HTML
        with tempfile.NamedTemporaryFile(suffix=".html", dir=self.temp_dir, delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(html_content.encode("utf-8"))
        
        try:
            # Try to parse with unstructured.io
            try:
                # Parse with unstructured.io
                unstructured_elements = await asyncio.to_thread(
                    partition_html, filename=temp_path, strategy="fast"
                )
                
                # Extract text from elements
                texts = []
                for element in unstructured_elements:
                    if hasattr(element, "text"):
                        texts.append(element.text)
                    else:
                        texts.append(str(element))
                
                return "\n\n".join(texts)
            
            except Exception as e:
                logger.error(f"Error parsing with unstructured.io: {str(e)}")
                return ""
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    async def _parse_kenya_law(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Parse Kenya Law HTML content with custom selectors.
        
        Args:
            html_content: Raw HTML content
            url: Source URL
            
        Returns:
            Dict with the parsed content and metadata
        """
        soup = BeautifulSoup(html_content, "html.parser")
        
        content_type = None
        selectors = None
        
        # Determine the type of content based on URL
        if "judgment" in url:
            content_type = "judgment"
            selectors = self.kenya_law_selectors["judgment"]
        elif "legislation" in url:
            content_type = "legislation"
            selectors = self.kenya_law_selectors["legislation"]
        else:
            # Unknown content type, use judgment as default
            content_type = "unknown"
            selectors = self.kenya_law_selectors["judgment"]
        
        # Extract data using the appropriate selectors
        title = soup.select_one(selectors["title"])
        title_text = title.get_text(strip=True) if title else ""
        
        content = soup.select_one(selectors["content"])
        content_text = content.get_text(strip=True, separator="\n\n") if content else ""
        
        date = soup.select_one(selectors["date"])
        date_text = date.get_text(strip=True) if date else ""
        
        citation = soup.select_one(selectors["citation"])
        citation_text = citation.get_text(strip=True) if citation else ""
        
        # Return structured data
        return {
            "content": content_text,
            "meta": {
                "title": title_text,
                "date": date_text,
                "citation": citation_text,
                "source": url,
                "type": content_type,
                "parser": "custom_kenya_law"
            }
        }
