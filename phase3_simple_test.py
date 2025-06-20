"""
Phase 3 Simple Test - Test components individually
"""
import os
import asyncio
from dotenv import load_dotenv
from app.rag.retriever import KenyaLawRetriever
from app.rag.legal_reasoner import LegalReasoner
from app.utils.logger import get_logger

# Load environment variables
load_dotenv()

# Configure logging
logger = get_logger("phase3_test")

async def test_retrieval():
    """Test the enhanced retrieval capabilities."""
    logger.info("Testing enhanced retrieval")
    
    retriever = KenyaLawRetriever()
    
    # Test query expansion
    test_query = "What are the legal requirements for child adoption in Kenya?"
    logger.info(f"Original query: {test_query}")
    
    # Get expanded queries
    expanded = await retriever._expand_query(test_query)
    logger.info(f"Expanded queries: {expanded}")
    
    # Test full retrieval
    results = await retriever.retrieve(test_query, top_k=3)
    
    logger.info(f"Retrieved {len(results)} documents")
    for i, doc in enumerate(results):
        logger.info(f"Document {i+1} score: {getattr(doc, 'score', 'N/A')}")
        logger.info(f"Document {i+1} content (excerpt): {doc.page_content[:200]}...")
    
    return len(results) > 0

async def test_legal_reasoning():
    """Test the legal reasoning components."""
    logger.info("Testing legal reasoning")
    
    reasoner = LegalReasoner()
    
    test_query = "What are my rights if my employer terminates me without notice?"
    test_context = """
    The Employment Act of Kenya establishes the fundamental principles of employment in Kenya. 
    It provides for minimum terms and conditions of employment, and regulates the relationship between employers and employees.
    
    Section 35 of the Employment Act states that an employer must provide notice before termination or payment in lieu of notice.
    The notice period depends on the payment interval, with one month's notice for monthly paid employees.
    
    In the case of Macharia v. East African Breweries Ltd [2018] eKLR, the court held that termination without notice or payment in lieu 
    constitutes wrongful dismissal and entitles the employee to damages.
    
    Section 45 of the Employment Act further provides that termination must be for a valid reason related to the employee's conduct, 
    capacity, or operational requirements of the employer.
    """
    
    # Perform analysis
    result = await reasoner.analyze(test_query, test_context)
    
    logger.info(f"Legal issues identified: {result.get('issues', [])}")
    logger.info(f"Legal rules applied: {result.get('rules', [])}")
    logger.info(f"Confidence score: {result.get('confidence', 0)}")
    logger.info(f"Citations found: {result.get('citations', [])}")
    logger.info(f"Analysis excerpt: {result.get('analysis', '')[:200]}...")
    logger.info(f"Conclusion: {result.get('conclusion', '')[:200]}...")
    
    return len(result.get('issues', [])) > 0 and result.get('analysis', '') != ''

async def main():
    """Run all tests."""
    logger.info("Starting Phase 3 simple test")
    
    # Test retrieval
    retrieval_success = await test_retrieval()
    logger.info(f"Retrieval test {'passed' if retrieval_success else 'failed'}")
    
    # Test legal reasoning
    reasoning_success = await test_legal_reasoning()
    logger.info(f"Legal reasoning test {'passed' if reasoning_success else 'failed'}")
    
    # Overall result
    overall_success = retrieval_success and reasoning_success
    logger.info(f"Phase 3 simple test {'PASSED' if overall_success else 'FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main())
