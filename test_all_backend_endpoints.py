#!/usr/bin/env python3
"""
Test ALL backend endpoints with 'weis' to find which one returns it incorrectly
"""
import requests
import json
import time

def test_endpoint(method, url, data=None, headers=None):
    """Test an endpoint and return the result"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    base_url = "http://localhost:8000"
    
    print("Testing ALL backend endpoints with 'weis'")
    print("=" * 50)
    
    # Test 1: Direct word lookup
    print("TEST 1: GET /words/weis")
    result1 = test_endpoint("GET", f"{base_url}/words/weis")
    if "error" not in result1:
        if result1.get("found"):
            lemma = result1.get("lemma", result1.get("original", "unknown"))
            print(f"ISSUE: Returns found=True, lemma='{lemma}'")
            if lemma.lower() == "weis":
                print("PROBLEM: This endpoint is returning 'weis' as valid!")
        else:
            print("GOOD: Returns found=False")
    else:
        print(f"Error: {result1['error']}")
    print()
    
    # Test 2: Search words
    print("TEST 2: GET /words/search-words?q=weis")
    result2 = test_endpoint("GET", f"{base_url}/words/search-words?q=weis")
    if "error" not in result2:
        results = result2.get("results", [])
        if results:
            first_result = results[0].get("lemma", "unknown")
            print(f"First result: '{first_result}'")
            if first_result.lower() == "weis":
                print("PROBLEM: Search returns 'weis' as first result!")
            elif first_result.lower() == "ausweis":
                print("GOOD: Search returns 'Ausweis' as first result")
        else:
            print("No results returned")
    else:
        print(f"Error: {result2['error']}")
    print()
    
    # Test 3: Translate search 
    print("TEST 3: POST /words/translate-search")
    translate_data = {
        "input_text": "weis",
        "target_languages": ["de"]
    }
    result3 = test_endpoint("POST", f"{base_url}/words/translate-search", translate_data)
    if "error" not in result3:
        if result3.get("found"):
            lemma = result3.get("lemma", result3.get("word", "unknown"))
            print(f"Returns: found=True, lemma='{lemma}'")
            if lemma.lower() == "weis":
                print("PROBLEM: Translate search returns 'weis'!")
            elif lemma.lower() == "ausweis":
                print("GOOD: Translate search returns 'Ausweis'")
        else:
            print("Returns: found=False (good, should suggest corrections)")
    else:
        print(f"Error: {result3['error']}")
    print()
    
    # Test 4: Check what endpoints exist
    print("TEST 4: Available endpoints")
    docs_result = test_endpoint("GET", f"{base_url}/docs")
    if "error" not in docs_result:
        print("Docs endpoint accessible - check /docs for all available endpoints")
    print()
    
    print("SUMMARY:")
    print("Check which test shows 'weis' being returned as a valid German word")
    print("That endpoint is the problem that needs fixing")

if __name__ == "__main__":
    main()