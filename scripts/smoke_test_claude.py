#!/usr/bin/env python3
"""
Simple smoke test for Claude 4 model via the router
As specified in the requirements: 
python -c "from agent.llm_router import route_model; print(route_model('Summarize this legal clause...', 'claude-4'))"
"""
import os
import sys
import asyncio

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def smoke_test_claude():
    """Run a simple smoke test for Claude 4"""
    try:
        from app.utils.llm_router import route_model
        
        print("🧪 Running Claude 4 smoke test...")
        print("-" * 40)
        
        # Test query as mentioned in requirements
        query = "Summarize this legal clause: 'The employment relationship may be terminated by either party giving thirty (30) days written notice to the other party, provided that such termination complies with the Employment Act of Kenya 2007 and any applicable collective bargaining agreements.'"
        
        print(f"Query: {query}")
        print("\nCalling Claude 4...")
        
        # Call Claude 4 via router
        response = await route_model(
            prompt=query,
            model_choice='claude-4',
            temperature=0.3,
            max_tokens=512
        )
        
        print(f"\n✅ Response received:")
        print("-" * 20)
        print(response)
        print("-" * 20)
        print(f"\nResponse length: {len(response)} characters")
        
        # Basic validation
        if len(response.strip()) > 50:
            print("✅ Smoke test PASSED - Response looks valid")
            return True
        else:
            print("❌ Smoke test FAILED - Response too short")
            return False
            
    except Exception as e:
        print(f"❌ Smoke test FAILED with error: {str(e)}")
        return False

async def smoke_test_hunyuan():
    """Run a simple smoke test for Hunyuan A13B"""
    try:
        from app.utils.llm_router import route_model
        
        print("\n🧪 Running Hunyuan A13B smoke test...")
        print("-" * 40)
        
        query = "What are the key employment rights in Kenya?"
        
        print(f"Query: {query}")
        print("\nCalling Hunyuan A13B...")
        
        # Call Hunyuan via router
        response = await route_model(
            prompt=query,
            model_choice='hunyuan-a13b',
            temperature=0.3,
            max_tokens=512
        )
        
        print(f"\n✅ Response received:")
        print("-" * 20)
        print(response)
        print("-" * 20)
        print(f"\nResponse length: {len(response)} characters")
        
        # Basic validation
        if len(response.strip()) > 50:
            print("✅ Smoke test PASSED - Response looks valid")
            return True
        else:
            print("❌ Smoke test FAILED - Response too short")
            return False
            
    except Exception as e:
        print(f"❌ Smoke test FAILED with error: {str(e)}")
        return False

async def smoke_test_flan():
    """Run a simple smoke test for FLAN-T5"""
    try:
        from app.utils.llm_router import route_model
        
        print("\n🧪 Running FLAN-T5 smoke test...")
        print("-" * 40)
        
        query = "What is the capital of Kenya?"
        
        print(f"Query: {query}")
        print("\nCalling FLAN-T5...")
        
        # Call FLAN-T5 via router
        response = await route_model(
            prompt=query,
            model_choice='flan-t5',
            temperature=0.3,
            max_tokens=128
        )
        
        print(f"\n✅ Response received:")
        print("-" * 20)
        print(response)
        print("-" * 20)
        print(f"\nResponse length: {len(response)} characters")
        
        # Basic validation
        if len(response.strip()) > 10:
            print("✅ Smoke test PASSED - Response looks valid")
            return True
        else:
            print("❌ Smoke test FAILED - Response too short")
            return False
            
    except Exception as e:
        print(f"❌ Smoke test FAILED with error: {str(e)}")
        return False

async def main():
    """Run all smoke tests"""
    print("🚀 Multi-LLM Smoke Test Suite")
    print("=" * 50)
    
    # Test individual models
    results = {}
    
    # Test Claude 4
    results['claude-4'] = await smoke_test_claude()
    
    # Test Hunyuan A13B
    results['hunyuan-a13b'] = await smoke_test_hunyuan()
    
    # Test FLAN-T5
    results['flan-t5'] = await smoke_test_flan()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SMOKE TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for model, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{model:15}: {status}")
    
    print(f"\nOverall: {passed}/{total} models passed smoke tests")
    
    if passed == total:
        print("🎉 All smoke tests passed!")
        sys.exit(0)
    else:
        print("⚠️ Some smoke tests failed")
        sys.exit(1)

if __name__ == "__main__":
    # Set up environment
    os.environ.setdefault("PYTHONPATH", ".")
    
    # Run smoke tests
    asyncio.run(main())