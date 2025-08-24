#!/usr/bin/env python3
"""
Test the enhanced OpenAI service for 9-tense verb generation
"""
import asyncio
import sys
import os
import json

sys.path.append(os.getcwd())

async def test_enhanced_openai():
    """Test the enhanced OpenAI service with new tense prompts"""
    
    print("=== Testing Enhanced OpenAI Service ===")
    
    try:
        from app.services.openai_service import OpenAIService
        
        openai_service = OpenAIService()
        
        # Test with a common German verb
        test_word = "spielen"
        print(f"Testing with word: {test_word}")
        
        result = await openai_service.analyze_word(test_word)
        
        print(f"\nOpenAI Response:")
        print(f"  Found: {result.get('found', False)}")
        print(f"  POS: {result.get('pos', 'unknown')}")
        
        tables = result.get('tables', {})
        if tables:
            print(f"  Tenses returned: {len(tables)}")
            print(f"  Available tenses:")
            for tense_name in tables.keys():
                person_count = len(tables[tense_name]) if isinstance(tables[tense_name], dict) else 0
                print(f"    - {tense_name}: {person_count} forms")
                
                # Show first few forms as examples
                if isinstance(tables[tense_name], dict) and person_count > 0:
                    sample_forms = list(tables[tense_name].items())[:2]
                    for person, form in sample_forms:
                        try:
                            print(f"      {person}: {form}")
                        except UnicodeEncodeError:
                            print(f"      {person}: [German form]")
            
            # Check if we got the advanced tenses
            core_tenses = ['praesens', 'praeteritum', 'perfekt', 'plusquamperfekt', 'imperativ']
            advanced_tenses = ['futur_i', 'futur_ii', 'konjunktiv_i', 'konjunktiv_ii']
            
            core_count = sum(1 for t in core_tenses if t in tables)
            advanced_count = sum(1 for t in advanced_tenses if t in tables)
            
            print(f"\n  Core tenses: {core_count}/5")
            print(f"  Advanced tenses: {advanced_count}/4")
            print(f"  Total: {core_count + advanced_count}/9")
            
            if core_count >= 5:
                print(f"  ✅ SUCCESS: Has all required core tenses!")
            else:
                print(f"  ❌ Missing core tenses")
                
            if advanced_count > 0:
                print(f"  ✅ BONUS: Has {advanced_count} advanced tenses!")
            else:
                print(f"  ℹ️  No advanced tenses (normal for basic analysis)")
                
        else:
            print("  No conjugation tables returned")
            
        # Print full result for debugging
        print(f"\nFull result (first 500 chars):")
        result_str = json.dumps(result, indent=2, ensure_ascii=False)[:500]
        try:
            print(result_str)
        except UnicodeEncodeError:
            print("[Result with German characters - showing structure only]")
            print(f"Keys: {list(result.keys())}")
            
    except Exception as e:
        print(f"Error testing OpenAI service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_openai())