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
            "judgments": "div.judgment-content",
            "legislation": "div.legislation-content",
            "constitution": "div.constitution-content",
            "default": "body"  # Fallback selector
        }
    
    async def parse(self, url: str) -> str:
        """
        Parse a web page by URL.
        
        Args:
            url: URL of the web page to parse
            
        Returns:
            Extracted text content
        """
        logger.info(f"Parsing web page: {url}")
        
        try:
            # Fetch the web page
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "").lower()
                
                # Check if it's a PDF
                if "application/pdf" in content_type:
                    return await self._parse_pdf_url(response.content)
                    
                # Otherwise, assume it's HTML
                html_content = response.text
                
                # Use different parsing approach based on the domain
                if "kenyalaw.org" in url:
                    return await self._parse_kenya_law(html_content, url)
                else:
                    # Use generic HTML parsing
                    return await self._parse_generic_html(html_content)
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {str(e)}")
            return f"Error parsing URL {url}: {str(e)}"
    
    async def _parse_kenya_law(self, html_content: str, url: str) -> str:
        """
        Special parser for Kenya Law website.
        
        Args:
            html_content: HTML content of the page
            url: URL of the page (to determine content type)
            
        Returns:
            Extracted text with appropriate formatting
        """
        logger.info("Using Kenya Law-specific parser")
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Determine the content type from the URL
        content_type = "default"
        if "/judgments/" in url:
            content_type = "judgments"
        elif "/legislation/" in url:
            content_type = "legislation"
        elif "/constitution/" in url or "constitution" in url:
            content_type = "constitution"
        
        # Get the appropriate selector
        selector = self.kenya_law_selectors.get(content_type, self.kenya_law_selectors["default"])
        
        # Extract the main content
        main_content = soup.select_one(selector)
        
        if main_content:
            # Process the content based on type
            if content_type == "judgments":
                # Extract the judgment details
                title_elem = soup.select_one("h1.judgment-title") or soup.select_one("title")
                title = title_elem.text.strip() if title_elem else "Unknown Judgment"
                
                # Extract the case number, date, court, etc.
                meta_elems = soup.select("div.judgment-meta p")
                meta_text = "\n".join([elem.text.strip() for elem in meta_elems]) if meta_elems else ""
                
                # Combine all parts
                return f"Title: {title}\n\nMetadata:\n{meta_text}\n\nContent:\n{main_content.text.strip()}"
                
            elif content_type == "legislation" or content_type == "constitution":
                # Extract legislation details
                title_elem = soup.select_one("h1.legislation-title") or soup.select_one("title")
                title = title_elem.text.strip() if title_elem else "Unknown Legislation"
                
                # Process sections and articles
                sections = []
                for section in main_content.select("div.section") or main_content.select("div.article"):
                    section_num = section.select_one("span.section-number") or section.select_one("span.article-number")
                    section_title = section.select_one("span.section-title") or section.select_one("span.article-title")
                    section_content = section.select_one("div.section-content") or section.select_one("div.article-content")
                    
                    section_text = ""
                    if section_num:
                        section_text += section_num.text.strip() + " "
                    if section_title:
                        section_text += section_title.text.strip() + "\n"
                    if section_content:
                        section_text += section_content.text.strip() + "\n\n"
                    
                    sections.append(section_text)
                
                # Combine all parts
                sections_text = "\n".join(sections) if sections else main_content.text.strip()
                return f"Title: {title}\n\nContent:\n{sections_text}"
            
            else:
                # Generic content
                return main_content.text.strip()
        else:
            # Fallback to generic HTML parsing
            return await self._parse_generic_html(html_content)
    
    async def _parse_generic_html(self, html_content: str) -> str:
        """
        Parse generic HTML content.
        
        Args:
            html_content: HTML content
            
        Returns:
            Extracted text
        """
        # Create a temporary file for the HTML
        with tempfile.NamedTemporaryFile(suffix=".html", dir=self.temp_dir, delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(html_content.encode("utf-8"))
        
        try:            # Try to parse with unstructured.io first
            if USING_UNSTRUCTURED:
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
                    
                    unstructured_text = "\n\n".join(texts)
                    
                    # If we got enough content, return it
                    if len(unstructured_text.strip()) >= 100:
                        logger.info("Successfully parsed HTML with unstructured.io")
                        return unstructured_text
                    
                    # Otherwise fall back to BeautifulSoup
                    logger.info("unstructured.io returned limited content, falling back to BeautifulSoup")
                except Exception as e:
                    logger.error(f"Error parsing HTML with unstructured.io: {str(e)}")
            
            # Fall back to BeautifulSoup
            logger.info("Using BeautifulSoup for HTML parsing")
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text(separator="\n")
            
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = "\n".join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {str(e)}")
            
            # Return a minimal result
            try:
                soup = BeautifulSoup(html_content, "html.parser")
                return soup.get_text()
            except:
                return f"Error parsing HTML: {str(e)}"
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    async def _parse_pdf_url(self, content: bytes) -> str:
        """
        Parse PDF content from a URL.
        
        Args:
            content: Raw PDF content
            
        Returns:
            Extracted text
        """
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", dir=self.temp_dir, delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(content)
        
        try:
            # Use the DocumentParser to parse the PDF
            from app.parsers.document_parser import DocumentParser
            document_parser = DocumentParser()
            return await document_parser._parse_pdf(content)
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
