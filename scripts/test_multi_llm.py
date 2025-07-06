#!/usr/bin/env python3
"""
Multi-LLM Testing and Validation Script
Tests all models, measures latency, and validates functionality
"""
import os
import sys
import time
import asyncio
import json
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.llm_router import get_router, route_model
from app.utils.claude_model import ClaudeModel
from app.utils.hunyuan_model import HunyuanModel

class MultiLLMTester:
    """
    Comprehensive testing suite for the multi-LLM system
    """
    
    def __init__(self):
        """Initialize the tester"""
        self.router = get_router()
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "models_tested": [],
            "smoke_tests": {},
            "performance_tests": {},
            "error_tests": {},
            "summary": {}
        }
        
        # Test queries for different scenarios
        self.test_queries = {
            "simple": "What is the capital of Kenya?",
            "legal": "What are the employment rights under the Employment Act of Kenya?",
            "complex": "Analyze the constitutional provisions for land ownership in Kenya and their relationship to customary law.",
            "multilingual": "Explain the concept of 'ubuntu' in African legal systems.",
            "summarization": "Summarize the key provisions of the Children Act.",
            "edge_case": "What happens when " + "a" * 1000 + " very long query is submitted?"
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        print("🚀 Starting Multi-LLM Testing Suite")
        print("=" * 50)
        
        # Get available models
        available_models = self.router.get_supported_models()
        print(f"📋 Available models: {', '.join(available_models)}")
        
        # Run tests for each model
        for model in available_models:
            print(f"\n🧪 Testing model: {model}")
            print("-" * 30)
            
            try:
                # Smoke tests
                await self._run_smoke_tests(model)
                
                # Performance tests
                await self._run_performance_tests(model)
                
                # Error handling tests
                await self._run_error_tests(model)
                
                self.test_results["models_tested"].append(model)
                print(f"✅ {model} tests completed")
                
            except Exception as e:
                print(f"❌ {model} tests failed: {str(e)}")
                self.test_results["smoke_tests"][model] = {"error": str(e)}
        
        # Generate summary
        self._generate_summary()
        
        return self.test_results
    
    async def _run_smoke_tests(self, model: str) -> None:
        """Run basic smoke tests for a model"""
        smoke_results = {"passed": 0, "failed": 0, "tests": {}}
        
        for test_name, query in self.test_queries.items():
            try:
                print(f"  🔍 Running smoke test: {test_name}")
                
                start_time = time.time()
                response = await route_model(
                    prompt=query,
                    model_choice=model,
                    temperature=0.3,
                    max_tokens=512
                )
                end_time = time.time()
                
                # Validate response
                is_valid = self._validate_response(response, test_name)
                
                smoke_results["tests"][test_name] = {
                    "passed": is_valid,
                    "response_length": len(response),
                    "latency_ms": round((end_time - start_time) * 1000, 2),
                    "response_preview": response[:100] + "..." if len(response) > 100 else response
                }
                
                if is_valid:
                    smoke_results["passed"] += 1
                    print(f"    ✅ {test_name}: PASSED ({smoke_results['tests'][test_name]['latency_ms']}ms)")
                else:
                    smoke_results["failed"] += 1
                    print(f"    ❌ {test_name}: FAILED")
                
            except Exception as e:
                smoke_results["failed"] += 1
                smoke_results["tests"][test_name] = {
                    "passed": False,
                    "error": str(e)
                }
                print(f"    ❌ {test_name}: ERROR - {str(e)}")
        
        self.test_results["smoke_tests"][model] = smoke_results
    
    async def _run_performance_tests(self, model: str) -> None:
        """Run performance benchmarks for a model"""
        print(f"  ⚡ Running performance tests")
        
        performance_results = {
            "latency_stats": {},
            "throughput_test": {},
            "concurrent_test": {}
        }
        
        # Latency test - multiple runs of the same query
        latencies = []
        test_query = self.test_queries["legal"]
        
        for i in range(3):  # Run 3 times for basic statistics
            try:
                start_time = time.time()
                response = await route_model(
                    prompt=test_query,
                    model_choice=model,
                    temperature=0.3,
                    max_tokens=256
                )
                end_time = time.time()
                
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
                
            except Exception as e:
                print(f"    ⚠️ Latency test {i+1} failed: {str(e)}")
        
        if latencies:
            performance_results["latency_stats"] = {
                "mean_ms": round(statistics.mean(latencies), 2),
                "median_ms": round(statistics.median(latencies), 2),
                "min_ms": round(min(latencies), 2),
                "max_ms": round(max(latencies), 2),
                "std_dev_ms": round(statistics.stdev(latencies) if len(latencies) > 1 else 0, 2)
            }
            print(f"    📊 Average latency: {performance_results['latency_stats']['mean_ms']}ms")
        
        # Concurrent requests test (simplified - 2 concurrent requests)
        try:
            start_time = time.time()
            tasks = [
                route_model(
                    prompt=self.test_queries["simple"],
                    model_choice=model,
                    temperature=0.3,
                    max_tokens=128
                ),
                route_model(
                    prompt=self.test_queries["legal"],
                    model_choice=model,
                    temperature=0.3,
                    max_tokens=128
                )
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            successful_requests = sum(1 for r in results if not isinstance(r, Exception))
            total_time = (end_time - start_time) * 1000
            
            performance_results["concurrent_test"] = {
                "total_requests": len(tasks),
                "successful_requests": successful_requests,
                "total_time_ms": round(total_time, 2),
                "avg_time_per_request_ms": round(total_time / len(tasks), 2)
            }
            
            print(f"    🔄 Concurrent test: {successful_requests}/{len(tasks)} succeeded")
            
        except Exception as e:
            performance_results["concurrent_test"] = {"error": str(e)}
            print(f"    ❌ Concurrent test failed: {str(e)}")
        
        self.test_results["performance_tests"][model] = performance_results
    
    async def _run_error_tests(self, model: str) -> None:
        """Test error handling and edge cases"""
        print(f"  🛡️ Running error handling tests")
        
        error_results = {"tests": {}}
        
        # Test 1: Empty query
        try:
            response = await route_model(
                prompt="",
                model_choice=model,
                temperature=0.3,
                max_tokens=50
            )
            error_results["tests"]["empty_query"] = {
                "handled_gracefully": len(response) > 0,
                "response_length": len(response)
            }
        except Exception as e:
            error_results["tests"]["empty_query"] = {
                "handled_gracefully": True,
                "error": str(e)
            }
        
        # Test 2: Invalid parameters
        try:
            response = await route_model(
                prompt="Test query",
                model_choice=model,
                temperature=2.0,  # Invalid temperature
                max_tokens=50
            )
            error_results["tests"]["invalid_temperature"] = {
                "handled_gracefully": True,
                "response_length": len(response)
            }
        except Exception as e:
            error_results["tests"]["invalid_temperature"] = {
                "handled_gracefully": True,
                "error": str(e)
            }
        
        # Test 3: Very long query (edge case)
        try:
            long_query = "What is " + "very " * 200 + "long query?"
            response = await route_model(
                prompt=long_query,
                model_choice=model,
                temperature=0.3,
                max_tokens=50
            )
            error_results["tests"]["long_query"] = {
                "handled_gracefully": len(response) > 0,
                "response_length": len(response)
            }
        except Exception as e:
            error_results["tests"]["long_query"] = {
                "handled_gracefully": True,
                "error": str(e)
            }
        
        self.test_results["error_tests"][model] = error_results
    
    def _validate_response(self, response: str, test_type: str) -> bool:
        """Validate if a response is acceptable"""
        if not response or len(response.strip()) < 10:
            return False
        
        # Basic validation checks
        if test_type == "simple":
            # Should mention Nairobi for Kenya capital question
            return "nairobi" in response.lower()
        elif test_type == "legal":
            # Should contain legal terms
            legal_terms = ["employment", "act", "rights", "law", "legal"]
            return any(term in response.lower() for term in legal_terms)
        elif test_type == "complex":
            # Should be longer and contain relevant terms
            return len(response) > 100 and any(term in response.lower() for term in ["constitution", "land", "law"])
        
        # Default validation - just check it's a reasonable response
        return len(response.strip()) >= 20
    
    def _generate_summary(self) -> None:
        """Generate test summary statistics"""
        summary = {
            "total_models_tested": len(self.test_results["models_tested"]),
            "models_passed": 0,
            "models_failed": 0,
            "fastest_model": None,
            "most_reliable_model": None,
            "recommendations": []
        }
        
        model_scores = {}
        
        for model in self.test_results["models_tested"]:
            score = 0
            
            # Score based on smoke tests
            smoke_data = self.test_results["smoke_tests"].get(model, {})
            if "passed" in smoke_data and "failed" in smoke_data:
                total_tests = smoke_data["passed"] + smoke_data["failed"]
                if total_tests > 0:
                    pass_rate = smoke_data["passed"] / total_tests
                    score += pass_rate * 40  # 40% weight for functionality
                    
                    if pass_rate >= 0.8:
                        summary["models_passed"] += 1
                    else:
                        summary["models_failed"] += 1
            
            # Score based on performance
            perf_data = self.test_results["performance_tests"].get(model, {})
            if "latency_stats" in perf_data and "mean_ms" in perf_data["latency_stats"]:
                # Lower latency is better - score inversely
                latency = perf_data["latency_stats"]["mean_ms"]
                if latency < 2000:  # Less than 2 seconds
                    score += 30
                elif latency < 5000:  # Less than 5 seconds
                    score += 20
                elif latency < 10000:  # Less than 10 seconds
                    score += 10
            
            # Score based on error handling
            error_data = self.test_results["error_tests"].get(model, {})
            if "tests" in error_data:
                error_tests_passed = sum(
                    1 for test in error_data["tests"].values() 
                    if test.get("handled_gracefully", False)
                )
                total_error_tests = len(error_data["tests"])
                if total_error_tests > 0:
                    error_score = (error_tests_passed / total_error_tests) * 30
                    score += error_score
            
            model_scores[model] = score
        
        # Find best performing models
        if model_scores:
            best_model = max(model_scores.items(), key=lambda x: x[1])
            summary["most_reliable_model"] = {
                "model": best_model[0],
                "score": round(best_model[1], 2)
            }
            
            # Find fastest model
            fastest_latency = float('inf')
            fastest_model = None
            
            for model in self.test_results["models_tested"]:
                perf_data = self.test_results["performance_tests"].get(model, {})
                if "latency_stats" in perf_data and "mean_ms" in perf_data["latency_stats"]:
                    latency = perf_data["latency_stats"]["mean_ms"]
                    if latency < fastest_latency:
                        fastest_latency = latency
                        fastest_model = model
            
            if fastest_model:
                summary["fastest_model"] = {
                    "model": fastest_model,
                    "latency_ms": fastest_latency
                }
        
        # Generate recommendations
        recommendations = []
        
        if summary["fastest_model"]:
            recommendations.append(
                f"Use {summary['fastest_model']['model']} for low-latency requirements "
                f"({summary['fastest_model']['latency_ms']}ms average)"
            )
        
        if summary["most_reliable_model"]:
            recommendations.append(
                f"Use {summary['most_reliable_model']['model']} for production workloads "
                f"(reliability score: {summary['most_reliable_model']['score']}/100)"
            )
        
        # Model-specific recommendations
        for model in self.test_results["models_tested"]:
            smoke_data = self.test_results["smoke_tests"].get(model, {})
            if model == "claude-4" and smoke_data.get("passed", 0) > 0:
                recommendations.append("Claude-4 recommended for complex legal analysis and reasoning")
            elif model == "flan-t5" and smoke_data.get("passed", 0) > 0:
                recommendations.append("FLAN-T5 recommended for development and cost optimization")
            elif model == "hunyuan-a13b" and smoke_data.get("passed", 0) > 0:
                recommendations.append("Hunyuan-A13B recommended for multilingual legal queries")
        
        summary["recommendations"] = recommendations
        self.test_results["summary"] = summary
    
    def print_results(self) -> None:
        """Print formatted test results"""
        print("\n" + "=" * 60)
        print("📊 MULTI-LLM TEST RESULTS SUMMARY")
        print("=" * 60)
        
        summary = self.test_results["summary"]
        print(f"🎯 Models Tested: {summary['total_models_tested']}")
        print(f"✅ Models Passed: {summary['models_passed']}")
        print(f"❌ Models Failed: {summary['models_failed']}")
        
        if summary.get("fastest_model"):
            print(f"🚀 Fastest Model: {summary['fastest_model']['model']} "
                  f"({summary['fastest_model']['latency_ms']}ms)")
        
        if summary.get("most_reliable_model"):
            print(f"🛡️ Most Reliable: {summary['most_reliable_model']['model']} "
                  f"(score: {summary['most_reliable_model']['score']}/100)")
        
        if summary.get("recommendations"):
            print("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(summary["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        print("\n📋 DETAILED RESULTS BY MODEL:")
        print("-" * 60)
        
        for model in self.test_results["models_tested"]:
            print(f"\n🤖 {model.upper()}")
            
            # Smoke test results
            smoke_data = self.test_results["smoke_tests"].get(model, {})
            if "passed" in smoke_data:
                total = smoke_data["passed"] + smoke_data.get("failed", 0)
                print(f"  Smoke Tests: {smoke_data['passed']}/{total} passed")
            
            # Performance results
            perf_data = self.test_results["performance_tests"].get(model, {})
            if "latency_stats" in perf_data:
                latency = perf_data["latency_stats"]["mean_ms"]
                print(f"  Average Latency: {latency}ms")
            
            # Error handling
            error_data = self.test_results["error_tests"].get(model, {})
            if "tests" in error_data:
                error_tests = len(error_data["tests"])
                print(f"  Error Handling: {error_tests} tests completed")
    
    def save_results(self, filename: str = None) -> str:
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"multi_llm_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"💾 Results saved to: {filename}")
        return filename

async def main():
    """Main test execution function"""
    tester = MultiLLMTester()
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Print results
        tester.print_results()
        
        # Save results
        tester.save_results()
        
        # Exit with appropriate code
        if results["summary"]["models_failed"] == 0:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print(f"\n⚠️ {results['summary']['models_failed']} model(s) failed tests")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    # Set up environment
    os.environ.setdefault("PYTHONPATH", ".")
    
    # Run tests
    asyncio.run(main())