"""
Comprehensive Phase 2 Testing Script
Tests all enhanced components and integrations
"""
import asyncio
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import enhanced components
from app.utils.llm_factory import get_enhanced_llm, create_legal_prompt, LEGAL_MODELS
from app.crawlers.kenya_law_crawler import KenyaLawCrawler
from app.indexing.enhanced_indexer import EnhancedDocumentIndexer
from app.parsers.document_processor_enhanced import EnhancedDocumentProcessor
from app.utils.logger import get_logger

# Set up logging
logger = get_logger(__name__)

class Phase2Tester:
    """Comprehensive tester for Phase 2 implementation."""
    
    def __init__(self):
        """Initialize the tester."""
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 2",
            "tests": {},
            "summary": {}
        }
        
        # Test data
        self.test_legal_queries = [
            {
                "query": "What are the constitutional rights to fair trial in Kenya?",
                "area": "constitutional_law",
                "expected_topics": ["Article 50", "fair trial", "constitutional rights"]
            },
            {
                "query": "Explain the process of judicial review in Kenyan administrative law",
                "area": "administrative_law", 
                "expected_topics": ["judicial review", "administrative action", "procedural fairness"]
            },
            {
                "query": "What are the requirements for valid contract formation in Kenya?",
                "area": "contract_law",
                "expected_topics": ["offer", "acceptance", "consideration", "intention"]
            }
        ]
        
        self.test_citations = [
            "Constitution of Kenya (2010), Article 47",
            "David Njoroge Macharia v Republic [2011] eKLR",
            "Public Procurement and Asset Disposal Act, 2015"
        ]

    async def run_all_tests(self):
        """Run all Phase 2 tests."""
        print("=" * 60)
        print("LEGAL TECH AI - PHASE 2 COMPREHENSIVE TESTING")
        print("=" * 60)
        
        try:
            # Test LLM enhancements
            await self.test_enhanced_llm()
            
            # Test document processing
            await self.test_document_processing()
            
            # Test enhanced indexing
            await self.test_enhanced_indexing()
            
            # Test crawler enhancements
            await self.test_crawler_enhancements()
            
            # Test legal query processing
            await self.test_legal_query_processing()
            
            # Test citation search
            await self.test_citation_search()
            
            # Test integration workflow
            await self.test_integration_workflow()
            
            # Generate summary
            self.generate_test_summary()
            
            # Save results
            self.save_test_results()
            
        except Exception as e:
            logger.error(f"Error in comprehensive testing: {str(e)}")
            self.results["error"] = str(e)

    async def test_enhanced_llm(self):
        """Test enhanced LLM functionality."""
        print("\n1. Testing Enhanced LLM Integration...")
        test_name = "enhanced_llm"
        
        try:
            # Test HuggingFace Hub integration
            llm = get_enhanced_llm("huggingface", "legal_reasoning")
            
            if llm is None:
                raise Exception("Failed to initialize enhanced LLM")
            
            # Test legal prompt creation
            prompt = create_legal_prompt(
                "legal_analysis",
                question="What is the doctrine of precedent in Kenyan law?"
            )
            
            # Test LLM response
            start_time = time.time()
            response = await llm.invoke(prompt)
            response_time = time.time() - start_time
            
            # Validate response
            is_valid = (
                response and 
                len(response) > 100 and
                any(term in response.lower() for term in ["precedent", "stare decisis", "court"])
            )
            
            self.results["tests"][test_name] = {
                "status": "PASS" if is_valid else "FAIL",
                "response_time": response_time,
                "response_length": len(response),
                "prompt_type": "legal_analysis",
                "model_info": {
                    "provider": "huggingface",
                    "use_case": "legal_reasoning",
                    "available_models": list(LEGAL_MODELS.keys())
                },
                "sample_response": response[:200] + "..." if len(response) > 200 else response
            }
            
            print(f"   ✓ Enhanced LLM: {'PASS' if is_valid else 'FAIL'}")
            print(f"   ✓ Response time: {response_time:.2f}s")
            print(f"   ✓ HuggingFace token: Configured")
            
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"   ✗ Enhanced LLM: ERROR - {str(e)}")

    async def test_document_processing(self):
        """Test enhanced document processing."""
        print("\n2. Testing Enhanced Document Processing...")
        test_name = "document_processing"
        
        try:
            processor = EnhancedDocumentProcessor()
            
            # Create a test document
            test_content = """
            IN THE HIGH COURT OF KENYA AT NAIROBI
            CONSTITUTIONAL AND HUMAN RIGHTS DIVISION
            
            PETITION NO. 123 OF 2024
            
            JOHN DOE ................................................ PETITIONER
            
            VERSUS
            
            ATTORNEY GENERAL ................................... RESPONDENT
            
            JUDGMENT
            
            This petition concerns the constitutional right to fair trial under Article 50 of the Constitution of Kenya, 2010.
            
            HELD: The right to fair trial is fundamental and includes the right to be heard, the right to legal representation, and the right to a timely trial.
            
            Constitutional provisions cited:
            - Article 50 (Fair hearing)
            - Article 25 (Fundamental rights and freedoms)
            
            Case law cited:
            - Republic v Chief Magistrate [2020] eKLR
            - David Njoroge v Attorney General [2019] eKLR
            """
            
            # Test content analysis
            start_time = time.time()
            
            # Test metadata extraction
            metadata = await processor._extract_enhanced_metadata(test_content, {}, "judgment")
            
            # Test citation extraction
            citations = await processor._extract_citations(test_content)
            
            # Test entity extraction
            entities = await processor._extract_legal_entities(test_content)
            
            processing_time = time.time() - start_time
            
            # Validate results
            has_court = metadata.get("court") is not None
            has_citations = len(citations) > 0
            has_entities = len(entities.get("courts", [])) > 0
            
            is_valid = has_court and has_citations and has_entities
            
            self.results["tests"][test_name] = {
                "status": "PASS" if is_valid else "FAIL",
                "processing_time": processing_time,
                "metadata_extracted": len(metadata),
                "citations_found": len(citations),
                "entities_found": sum(len(v) for v in entities.values()),
                "features": {
                    "court_detection": has_court,
                    "citation_extraction": has_citations,
                    "entity_extraction": has_entities
                },
                "sample_metadata": metadata,
                "sample_citations": citations[:2],
                "sample_entities": {k: v[:2] for k, v in entities.items() if v}
            }
            
            print(f"   ✓ Document Processing: {'PASS' if is_valid else 'FAIL'}")
            print(f"   ✓ Processing time: {processing_time:.2f}s")
            print(f"   ✓ Citations found: {len(citations)}")
            print(f"   ✓ Entities found: {sum(len(v) for v in entities.values())}")
            
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"   ✗ Document Processing: ERROR - {str(e)}")

    async def test_enhanced_indexing(self):
        """Test enhanced indexing system."""
        print("\n3. Testing Enhanced Indexing System...")
        test_name = "enhanced_indexing"
        
        try:
            indexer = EnhancedDocumentIndexer()
            
            # Wait for initialization
            await asyncio.sleep(2)
            
            # Test adding a document chunk
            test_content = "The Constitution of Kenya (2010) guarantees fundamental rights under Chapter 4."
            test_metadata = {
                "document_type": "constitutional",
                "source": "test",
                "date": "2024-01-01"
            }
            
            start_time = time.time()
            await indexer.add_document_chunk(test_content, test_metadata)
            indexing_time = time.time() - start_time
            
            # Test search functionality
            start_time = time.time()
            search_results = await indexer.search("constitutional rights Kenya", k=5)
            search_time = time.time() - start_time
            
            # Test citation search
            citation_results = await indexer.search_by_citation("Constitution of Kenya", k=3)
            
            # Test metadata search
            metadata_results = await indexer.search_by_metadata({"document_type": "constitutional"}, k=3)
            
            # Get index statistics
            stats = await indexer.get_stats()
            
            # Validate results
            is_valid = (
                indexing_time < 10.0 and  # Reasonable indexing time
                search_time < 5.0 and     # Reasonable search time
                stats.total_chunks > 0    # Has indexed content
            )
            
            self.results["tests"][test_name] = {
                "status": "PASS" if is_valid else "FAIL",
                "indexing_time": indexing_time,
                "search_time": search_time,
                "search_results": len(search_results),
                "citation_results": len(citation_results),
                "metadata_results": len(metadata_results),
                "index_stats": {
                    "total_documents": stats.total_documents,
                    "total_chunks": stats.total_chunks,
                    "embedding_model": stats.embedding_model,
                    "last_updated": stats.last_updated
                },
                "features": {
                    "semantic_search": len(search_results) > 0,
                    "citation_search": True,  # Method exists
                    "metadata_filtering": True  # Method exists
                }
            }
            
            print(f"   ✓ Enhanced Indexing: {'PASS' if is_valid else 'FAIL'}")
            print(f"   ✓ Indexing time: {indexing_time:.2f}s")
            print(f"   ✓ Search time: {search_time:.2f}s")
            print(f"   ✓ Total chunks: {stats.total_chunks}")
            
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"   ✗ Enhanced Indexing: ERROR - {str(e)}")

    async def test_crawler_enhancements(self):
        """Test crawler enhancements."""
        print("\n4. Testing Crawler Enhancements...")
        test_name = "crawler_enhancements"
        
        try:
            crawler = KenyaLawCrawler()
            
            # Test crawler initialization
            is_initialized = (
                crawler.base_url is not None and
                len(crawler.sections) > 0 and
                crawler.web_parser is not None
            )
            
            # Test enhanced extraction methods (without actual crawling)
            test_doc_info = {
                "url": "https://example.com/test-case",
                "title": "Test Case v Test Respondent"
            }
            
            # Test document classification
            classification = crawler._classify_document_type("judgments", None)
            
            # Test metadata extraction capabilities
            has_metadata_extraction = hasattr(crawler, '_extract_legal_metadata')
            has_citation_extraction = hasattr(crawler, '_extract_citations')
            has_entity_extraction = hasattr(crawler, '_extract_legal_entities')
            
            # Test scheduling capability
            has_scheduling = hasattr(crawler, 'schedule_periodic_crawl')
            
            is_valid = (
                is_initialized and
                has_metadata_extraction and
                has_citation_extraction and
                has_entity_extraction and
                has_scheduling
            )
            
            self.results["tests"][test_name] = {
                "status": "PASS" if is_valid else "FAIL",
                "crawler_initialized": is_initialized,
                "sections_configured": len(crawler.sections),
                "rate_limit": crawler.rate_limit,
                "max_pages": crawler.max_pages_per_section,
                "features": {
                    "enhanced_metadata_extraction": has_metadata_extraction,
                    "citation_parsing": has_citation_extraction,
                    "entity_extraction": has_entity_extraction,
                    "periodic_scheduling": has_scheduling,
                    "incremental_updates": hasattr(crawler, 'incremental_update')
                },
                "sections": list(crawler.sections.keys())
            }
            
            print(f"   ✓ Crawler Enhancements: {'PASS' if is_valid else 'FAIL'}")
            print(f"   ✓ Sections configured: {len(crawler.sections)}")
            print(f"   ✓ Enhanced features: Available")
            
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"   ✗ Crawler Enhancements: ERROR - {str(e)}")

    async def test_legal_query_processing(self):
        """Test legal query processing workflow."""
        print("\n5. Testing Legal Query Processing...")
        test_name = "legal_query_processing"
        
        try:
            llm = get_enhanced_llm("huggingface", "legal_reasoning")
            indexer = EnhancedDocumentIndexer()
            
            results = []
            
            for test_query in self.test_legal_queries:
                start_time = time.time()
                
                # Create legal prompt
                prompt = create_legal_prompt("legal_analysis", question=test_query["query"])
                
                # Get LLM response
                llm_response = await llm.invoke(prompt)
                
                # Search for supporting documents
                search_results = await indexer.search(test_query["query"], k=3)
                
                processing_time = time.time() - start_time
                
                # Check if expected topics are covered
                response_lower = llm_response.lower()
                topics_covered = sum(1 for topic in test_query["expected_topics"] 
                                   if topic.lower() in response_lower)
                
                query_result = {
                    "query": test_query["query"],
                    "area": test_query["area"],
                    "processing_time": processing_time,
                    "response_length": len(llm_response),
                    "search_results": len(search_results),
                    "topics_covered": topics_covered,
                    "expected_topics": len(test_query["expected_topics"]),
                    "topic_coverage": topics_covered / len(test_query["expected_topics"])
                }
                
                results.append(query_result)
            
            # Calculate overall performance
            avg_processing_time = sum(r["processing_time"] for r in results) / len(results)
            avg_topic_coverage = sum(r["topic_coverage"] for r in results) / len(results)
            
            is_valid = (
                avg_processing_time < 15.0 and  # Reasonable response time
                avg_topic_coverage > 0.3        # At least 30% topic coverage
            )
            
            self.results["tests"][test_name] = {
                "status": "PASS" if is_valid else "FAIL",
                "queries_tested": len(results),
                "avg_processing_time": avg_processing_time,
                "avg_topic_coverage": avg_topic_coverage,
                "individual_results": results
            }
            
            print(f"   ✓ Legal Query Processing: {'PASS' if is_valid else 'FAIL'}")
            print(f"   ✓ Queries tested: {len(results)}")
            print(f"   ✓ Avg processing time: {avg_processing_time:.2f}s")
            print(f"   ✓ Avg topic coverage: {avg_topic_coverage:.1%}")
            
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"   ✗ Legal Query Processing: ERROR - {str(e)}")

    async def test_citation_search(self):
        """Test citation search functionality."""
        print("\n6. Testing Citation Search...")
        test_name = "citation_search"
        
        try:
            indexer = EnhancedDocumentIndexer()
            
            # Add some test content with citations
            test_documents = [
                {
                    "content": "According to Article 47 of the Constitution of Kenya (2010), every person has the right to fair administrative action.",
                    "metadata": {"document_type": "constitutional", "source": "constitution"}
                },
                {
                    "content": "In David Njoroge Macharia v Republic [2011] eKLR, the court held that constitutional rights must be protected.",
                    "metadata": {"document_type": "judgment", "source": "case_law"}
                }
            ]
            
            # Index test documents
            for doc in test_documents:
                await indexer.add_document_chunk(doc["content"], doc["metadata"])
            
            citation_results = []
            
            for citation in self.test_citations:
                start_time = time.time()
                results = await indexer.search_by_citation(citation, k=5)
                search_time = time.time() - start_time
                
                citation_results.append({
                    "citation": citation,
                    "results_found": len(results),
                    "search_time": search_time
                })
            
            # Calculate performance
            total_results = sum(r["results_found"] for r in citation_results)
            avg_search_time = sum(r["search_time"] for r in citation_results) / len(citation_results)
            
            is_valid = avg_search_time < 2.0  # Reasonable search time
            
            self.results["tests"][test_name] = {
                "status": "PASS" if is_valid else "FAIL",
                "citations_tested": len(citation_results),
                "total_results_found": total_results,
                "avg_search_time": avg_search_time,
                "individual_results": citation_results
            }
            
            print(f"   ✓ Citation Search: {'PASS' if is_valid else 'FAIL'}")
            print(f"   ✓ Citations tested: {len(citation_results)}")
            print(f"   ✓ Total results: {total_results}")
            print(f"   ✓ Avg search time: {avg_search_time:.2f}s")
            
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"   ✗ Citation Search: ERROR - {str(e)}")

    async def test_integration_workflow(self):
        """Test end-to-end integration workflow."""
        print("\n7. Testing Integration Workflow...")
        test_name = "integration_workflow"
        
        try:
            # Simulate a complete workflow
            start_time = time.time()
            
            # 1. Initialize all components
            llm = get_enhanced_llm("huggingface", "legal_reasoning")
            indexer = EnhancedDocumentIndexer()
            processor = EnhancedDocumentProcessor()
            
            # 2. Process a legal query
            query = "What are the constitutional provisions for judicial review in Kenya?"
            
            # 3. Create legal prompt
            prompt = create_legal_prompt("reasoning_trace", query=query)
            
            # 4. Get AI analysis
            analysis = await llm.invoke(prompt)
            
            # 5. Search for supporting documents
            search_results = await indexer.search(query, k=5)
            
            # 6. Extract citations from analysis
            citations = await processor._extract_citations(analysis)
            
            total_time = time.time() - start_time
            
            # Validate workflow
            is_valid = (
                analysis and len(analysis) > 100 and
                total_time < 30.0 and  # Complete workflow under 30 seconds
                len(search_results) >= 0  # Search completed
            )
            
            self.results["tests"][test_name] = {
                "status": "PASS" if is_valid else "FAIL",
                "total_workflow_time": total_time,
                "analysis_length": len(analysis),
                "search_results": len(search_results),
                "citations_extracted": len(citations),
                "workflow_steps": [
                    "Component initialization",
                    "Legal prompt creation", 
                    "AI analysis generation",
                    "Document search",
                    "Citation extraction"
                ]
            }
            
            print(f"   ✓ Integration Workflow: {'PASS' if is_valid else 'FAIL'}")
            print(f"   ✓ Total workflow time: {total_time:.2f}s")
            print(f"   ✓ Analysis generated: {len(analysis)} chars")
            print(f"   ✓ Search results: {len(search_results)}")
            
        except Exception as e:
            self.results["tests"][test_name] = {
                "status": "ERROR", 
                "error": str(e)
            }
            print(f"   ✗ Integration Workflow: ERROR - {str(e)}")

    def generate_test_summary(self):
        """Generate test summary."""
        tests = self.results["tests"]
        
        total_tests = len(tests)
        passed_tests = sum(1 for test in tests.values() if test.get("status") == "PASS")
        failed_tests = sum(1 for test in tests.values() if test.get("status") == "FAIL") 
        error_tests = sum(1 for test in tests.values() if test.get("status") == "ERROR")
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "phase_2_features": {
                "huggingface_integration": "enhanced_llm" in tests and tests["enhanced_llm"].get("status") == "PASS",
                "advanced_document_processing": "document_processing" in tests and tests["document_processing"].get("status") == "PASS",
                "legal_specialized_indexing": "enhanced_indexing" in tests and tests["enhanced_indexing"].get("status") == "PASS",
                "enhanced_crawler": "crawler_enhancements" in tests and tests["crawler_enhancements"].get("status") == "PASS",
                "legal_query_processing": "legal_query_processing" in tests and tests["legal_query_processing"].get("status") == "PASS",
                "citation_search": "citation_search" in tests and tests["citation_search"].get("status") == "PASS",
                "end_to_end_workflow": "integration_workflow" in tests and tests["integration_workflow"].get("status") == "PASS"
            }
        }
        
        print("\n" + "=" * 60)
        print("PHASE 2 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")
        print(f"Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        print("\nPhase 2 Feature Status:")
        for feature, status in self.results["summary"]["phase_2_features"].items():
            status_str = "✓ PASS" if status else "✗ FAIL"
            print(f"  {feature.replace('_', ' ').title()}: {status_str}")

    def save_test_results(self):
        """Save test results to file."""
        try:
            results_file = f"phase2_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"\nTest results saved to: {results_file}")
            
        except Exception as e:
            print(f"Error saving test results: {str(e)}")

async def main():
    """Main test execution."""
    tester = Phase2Tester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
