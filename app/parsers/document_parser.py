"""
Document Parser - For parsing PDFs and other document formats
"""
import os
import tempfile
from typing import Dict, Any, List, Optional
import asyncio
import io

# Try to import real dependencies first, fall back to stubs if not available
USING_PYMUPDF = False
USING_UNSTRUCTURED = False

try:
    import fitz  # PyMuPDF
    USING_PYMUPDF = True
except ImportError:
    from app.utils.stubs.fitz import fitz
    USING_PYMUPDF = False

try:
    # Try importing unstructured modules separately since some might be available while others are not
    try:
        from unstructured.partition.pdf import partition as partition_pdf
        USING_UNSTRUCTURED = True
    except (ImportError, ModuleNotFoundError):
        from app.utils.stubs.unstructured.partition.pdf import partition as partition_pdf
        USING_UNSTRUCTURED = False
    
    try:
        from unstructured.partition.html import partition as partition_html
    except (ImportError, ModuleNotFoundError):
        from app.utils.stubs.unstructured.partition.html import partition as partition_html
    
    try:
        from unstructured.partition.text import partition as partition_text
    except (ImportError, ModuleNotFoundError):
        from app.utils.stubs.unstructured.partition.text import partition as partition_text
except Exception as e:
    # Fall back to all stubs if there's any unexpected error
    from app.utils.stubs.unstructured.partition.pdf import partition as partition_pdf
    from app.utils.stubs.unstructured.partition.html import partition as partition_html
    from app.utils.stubs.unstructured.partition.text import partition as partition_text
    USING_UNSTRUCTURED = False

from app.utils.logger import get_logger

logger = get_logger(__name__)

class DocumentParser:
    """
    Parser for various document formats (PDF, HTML, text, etc.)
    using unstructured.io and PyMuPDF.
    """
    
    def __init__(self):
        """Initialize the document parser."""
        self.temp_dir = os.getenv("PDF_TEMP_DIR", "./data/temp_pdfs")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.max_file_size = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "10")) * 1024 * 1024  # Convert to bytes
        
        if not USING_PYMUPDF and not USING_UNSTRUCTURED:
            logger.warning("Using stub implementations for document parsing - no real parser libraries available")
        else:
            available_parsers = []
            if USING_PYMUPDF:
                available_parsers.append("PyMuPDF")
            if USING_UNSTRUCTURED:
                available_parsers.append("unstructured.io")
            logger.info(f"Using real document parsing libraries: {', '.join(available_parsers)}")
    
    async def parse(self, content: bytes, file_type: str) -> str:
        """
        Parse document content based on file type.
        
        Args:
            content: Raw binary content of the document
            file_type: MIME type of the document (e.g., "application/pdf")
            
        Returns:
            Extracted text content
        """
        if len(content) > self.max_file_size:
            raise ValueError(f"File too large ({len(content) / (1024 * 1024):.2f} MB). Maximum size is {self.max_file_size / (1024 * 1024)} MB")
        
        logger.info(f"Parsing document of type {file_type} ({len(content) / 1024:.2f} KB)")
        
        try:
            # Route to appropriate parser based on file type
            if "pdf" in file_type.lower():
                return await self._parse_pdf(content)
            elif "html" in file_type.lower():
                return await self._parse_html(content)
            elif "text" in file_type.lower() or "plain" in file_type.lower():
                return content.decode("utf-8", errors="replace")
            else:
                # Try to parse as text for unknown types
                try:
                    return content.decode("utf-8", errors="replace")
                except:
                    logger.warning(f"Could not decode unknown file type {file_type} as text")
                    return f"Unsupported file format: {file_type}"
        except Exception as e:
            logger.error(f"Error parsing document: {str(e)}")
            # Return a partial result if possible
            try:
                return content.decode("utf-8", errors="replace")
            except:
                return f"Error parsing document: {str(e)}"
    
    async def _parse_pdf(self, content: bytes) -> str:
        """
        Parse PDF content using a combination of unstructured.io and PyMuPDF.
        
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
            pymupdf_text = ""
            unstructured_text = ""
            
            # First try with PyMuPDF (fitz) if available
            if USING_PYMUPDF:
                try:
                    pymupdf_text = await self._parse_with_pymupdf(temp_path, content)
                    logger.info(f"PyMuPDF extracted {len(pymupdf_text)} characters")
                except Exception as e:
                    logger.error(f"Error in PyMuPDF parsing: {str(e)}")
            
            # Then try with unstructured if available
            if USING_UNSTRUCTURED:
                try:
                    unstructured_text = await self._parse_with_unstructured(temp_path)
                    logger.info(f"Unstructured extracted {len(unstructured_text)} characters")
                except Exception as e:
                    logger.error(f"Error in unstructured parsing: {str(e)}")
            
            # Choose the best result or use stub if neither worked
            if len(pymupdf_text) > 0 or len(unstructured_text) > 0:
                if len(unstructured_text) > len(pymupdf_text) * 0.5:  # If unstructured got at least 50% of PyMuPDF
                    logger.info("Using unstructured.io parsed content")
                    result = unstructured_text
                else:
                    logger.info("Using PyMuPDF parsed content")
                    result = pymupdf_text
            else:
                # Fallback to stub if neither parser worked
                logger.warning("Both parsers failed, using stub implementation")
                result = f"[Stub] PDF content with {len(content)} bytes"
            
            return result
        
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            return f"Error parsing PDF: {str(e)}"
        
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    async def _parse_with_pymupdf(self, file_path: str, content: bytes = None) -> str:
        """Parse PDF with PyMuPDF."""
        if not USING_PYMUPDF:
            logger.warning("PyMuPDF is not available, using stub implementation")
            return f"[Stub] Parsed content from {file_path}"
            
        try:
            # Try to open from file first
            if os.path.exists(file_path):
                doc = fitz.open(file_path)
            # If that fails or we have content, try from memory
            elif content:
                doc = fitz.open(stream=content, filetype="pdf")
            else:
                raise ValueError("Neither file path nor content provided")
            
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text("text") + "\n\n"
            
            doc.close()
            return text
        
        except Exception as e:
            logger.error(f"PyMuPDF parsing error: {str(e)}")
            raise
    
    async def _parse_with_unstructured(self, file_path: str) -> str:
        """Parse PDF with unstructured.io."""
        if not USING_UNSTRUCTURED:
            logger.warning("Unstructured.io is not available, using stub implementation")
            return f"[Stub] Parsed content from {file_path}"
            
        try:
            # Run in a separate thread to avoid blocking
            elements = await asyncio.to_thread(
                partition_pdf, 
                file_path=file_path, 
                strategy="fast"  # Use fast strategy to avoid unstructured_inference dependency
            )
            
            # Extract text from elements
            texts = []
            for element in elements:
                if hasattr(element, "text"):
                    texts.append(element.text)
                else:
                    texts.append(str(element))
            
            return "\n\n".join(texts)
        
        except Exception as e:
            logger.error(f"Unstructured parsing error: {str(e)}")
            raise
    
    async def _parse_html(self, content: bytes) -> str:
        """
        Parse HTML content using unstructured.io.
        
        Args:
            content: Raw HTML content
            
        Returns:
            Extracted text
        """
        try:
            # Create a temporary file for the HTML
            with tempfile.NamedTemporaryFile(suffix=".html", dir=self.temp_dir, delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(content)
            
            try:
                if USING_UNSTRUCTURED:
                    # Run in a separate thread to avoid blocking
                    elements = await asyncio.to_thread(
                        partition_html, 
                        filename=temp_path
                    )
                    
                    # Extract text from elements
                    texts = []
                    for element in elements:
                        if hasattr(element, "text"):
                            texts.append(element.text)
                        else:
                            texts.append(str(element))
                    
                    return "\n\n".join(texts)
                else:
                    logger.warning("Unstructured.io is not available, using stub implementation")
                    return f"[Stub] Parsed HTML content ({len(content)} bytes)"
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        except Exception as e:
            logger.error(f"Error parsing HTML: {str(e)}")
            
            # Fallback to basic decoding
            try:
                return content.decode("utf-8", errors="replace")
            except:
                return f"Error parsing HTML: {str(e)}"
