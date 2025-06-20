"""
Enhanced Test Script for Counsel Legal AI Backend

This script tests the core functionality of the system:
1. Vector database and retrieval
2. LLM integration and response generation
3. Document parsing

Usage:
    python enhanced_test.py
"""
import os
import asyncio
import sys
from dotenv import load_dotenv

# Add the root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    
    # Retrieve documents
    print("Retrieving documents...")
    docs = await retriever.retrieve(query=query, top_k=3)
    
    # Print results
    print(f"{Colors.GREEN}Retrieved {len(docs)} documents{Colors.END}")
    for i, doc in enumerate(docs):
        print(f"\n{Colors.BOLD}Document {i+1}:{Colors.END}")
        print(f"  Content: {doc['content'][:150]}...")
        print(f"  Source: {doc['meta'].get('source', 'Unknown')}")
        print(f"  Score: {doc['score']:.4f}")

async def test_llm():
    """Test the LLM component."""
    print_section("Testing LLM")
    
    # Initialize LLM with caching
    print("Initializing LLM (this may take a moment)...")
    llm = get_llm(llm_type="mixtral")  # Try with mixtral first
    
    # If llm is None, try with fallback
    if llm is None:
        print(f"{Colors.YELLOW}Primary LLM failed to initialize, using fallback...{Colors.END}")
        llm = get_fake_llm()
    
    # Test prompt
    prompt = """
    You are a legal assistant specializing in Kenyan law.
    
    Query: What are the requirements for registering a business in Kenya?
    
    Answer the query with specific reference to Kenyan law.
    """
    
    print(f"{Colors.YELLOW}Sending prompt to LLM...{Colors.END}")
    
    # Get response
    response = await llm.invoke(prompt=prompt)
    
    # Print response
    print(f"\n{Colors.GREEN}LLM Response:{Colors.END}")
    print(response)

async def test_document_parser():
    """Test the document parser component."""
    print_section("Testing Document Parser")
    parser = DocumentParser()
    
    # Test with a sample PDF
    pdf_path = "test_document.pdf"
    if os.path.exists(pdf_path):
        print(f"{Colors.YELLOW}Parsing {pdf_path}...{Colors.END}")
        with open(pdf_path, "rb") as f:
            content = f.read()
        
        # Parse the document
        parsed_content = await parser.parse(content=content, file_type="application/pdf")
        
        # Print a preview
        print(f"\n{Colors.GREEN}Parsed Content Preview:{Colors.END}")
        print(parsed_content[:500] + "...")
        print(f"\n{Colors.GREEN}Total parsed content length: {len(parsed_content)} characters{Colors.END}")
    else:
        print(f"{Colors.RED}Warning: Test file {pdf_path} not found. Skipping document parser test.{Colors.END}")

async def run_tests():
    """Run all tests."""
    print_section("Counsel Legal AI Backend Test")
    
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
