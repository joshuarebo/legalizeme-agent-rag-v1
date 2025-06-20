"""
Enhanced Test Script for Counsel Legal AI Backend

This script tests the core functionality of the system:
1. Vector database and retrieval
2. LLM integration and response generation
3. Document parsing

Usage:
    python enhanced_test_fixed.py
"""
import os
import asyncio
import sys
import logging
from dotenv import load_dotenv

# Add the root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# First try to restore any previously patched files
from app.utils.patch_imports import restore_files, is_package_installed

# Check which packages are available and restore them
packages_to_restore = {}
package_mapping = {
    "langgraph": "app.utils.stubs.langgraph",
    "haystack": "app.utils.stubs.haystack",
    "unstructured": "app.utils.stubs.unstructured", 
    "fitz": "app.utils.stubs.fitz",
    "smol_agent": "app.utils.stubs.smol_agent"
}

for package, stub in package_mapping.items():
    if is_package_installed(package):
        packages_to_restore[package] = stub

# Restore files with real imports
restore_files(packages_to_restore)

# Import our components
from app.rag.retriever import KenyaLawRetriever
from app.utils.llm_factory import get_llm, get_fake_llm
from app.parsers.document_parser import DocumentParser

# Terminal colors for better readability
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"

# Load environment variables
load_dotenv()

def print_section(title):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

async def test_retriever():
    """Test the retriever component."""
    print_section("Testing Retriever")
    retriever = KenyaLawRetriever()
    
    # Test query
    query = "What does the Constitution of Kenya say about land rights?"
    print(f"{Colors.YELLOW}Query: {query}{Colors.END}")
    
    print("Retrieving documents...")
    docs = await retriever.retrieve(query, k=3)
    
    print(f"{Colors.GREEN}Retrieved {len(docs)} documents{Colors.END}")
    
    # Display results
    for i, doc in enumerate(docs):
        print(f"{Colors.BOLD}Document {i+1}:{Colors.END}")
        # Truncate content for display
        content = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
        print(f"  Content: {content}")
        
        if hasattr(doc, "metadata") and doc.metadata:
            source = doc.metadata.get("source", "Unknown")
            print(f"  Source: {source}")
        
        if hasattr(doc, "score"):
            print(f"  Score: {doc.score:.4f}")
        
        print()
    
    return docs

async def test_llm():
    """Test the LLM component."""
    print_section("Testing LLM")
    
    print("Initializing LLM (this may take a moment)...")
    llm = get_llm()
    
    # Simple test prompt
    prompt = """
    You are a legal assistant specializing in Kenyan law.
    Query: What are the requirements for registering a business in Kenya?
    Answer the query with specific reference to Kenyan law.
    """
    
    print("Sending prompt to LLM...")
    response = await llm.ainvoke(prompt)
    
    print(f"{Colors.GREEN}LLM Response:{Colors.END}\n{response}")
    
    return response

async def test_document_parser():
    """Test the document parser component."""
    print_section("Testing Document Parser")
    
    parser = DocumentParser()
    
    # Test with a sample PDF
    pdf_path = os.path.join("data", "samples", "test_document.pdf")
    
    # Create sample PDF if it doesn't exist
    if not os.path.exists(pdf_path):
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.5\n%Sample PDF for testing\nHello World")
    
    print(f"Parsing {os.path.basename(pdf_path)}...")
    
    with open(pdf_path, "rb") as f:
        content = f.read()
    
    parsed_content = await parser.parse(content, "application/pdf")
    
    # Display a preview of the parsed content
    preview = parsed_content[:100] + "..." if len(parsed_content) > 100 else parsed_content
    print(f"{Colors.GREEN}Parsed Content Preview:{Colors.END}\n{preview}")
    
    print(f"Total parsed content length: {len(parsed_content)} characters")
    
    return parsed_content

async def run_tests():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'Counsel Legal AI Backend Test'.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'=' * 60}{Colors.END}\n")
    
    try:
        # Test retriever
        await test_retriever()
    except Exception as e:
        print(f"{Colors.RED}Error in retriever test: {str(e)}{Colors.END}")
    
    try:
        # Test LLM
        await test_llm()
    except Exception as e:
        print(f"{Colors.RED}Error in LLM test: {str(e)}{Colors.END}")
    
    try:
        # Test document parser
        await test_document_parser()
    except Exception as e:
        print(f"{Colors.RED}Error in document parser test: {str(e)}{Colors.END}")
    
    print(f"\n{Colors.GREEN}Test Complete{Colors.END}")

if __name__ == "__main__":
    asyncio.run(run_tests())
