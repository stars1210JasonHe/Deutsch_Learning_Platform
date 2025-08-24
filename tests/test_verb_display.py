#!/usr/bin/env python3
"""
Test verb conjugation display - check what data is returned by the API
"""
import sys
import os
import requests
import json

sys.path.append(os.getcwd())

def test_verb_api(word="fahren"):
    """Test a verb through the API to see what conjugation data is returned"""
    
    print(f"=== Testing verb '{word}' via API ===")
    
    # API endpoint
    url = "http://localhost:8000/api/translate/word"
    
    try:
        response = requests.post(url, json={"input": word}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Status: {response.status_code}")
            print(f"Found: {data.get('found', False)}")
            print(f"POS: {data.get('pos', 'unknown')}")
            
            # Check tables structure
            tables = data.get('tables')
            if tables:
                print(f"\nAvailable tenses ({len(tables)} total):")
                for tense, forms in tables.items():
                    if isinstance(forms, dict):
                        form_count = len([f for f in forms.values() if f])
                        try:
                            print(f"  {tense}: {form_count} forms")
                        except UnicodeEncodeError:
                            print(f"  [tense]: {form_count} forms")
                
                # Show first few forms for each tense
                print(f"\nSample conjugations:")
                for tense, forms in list(tables.items())[:3]:  # Show first 3 tenses
                    if isinstance(forms, dict):
                        try:
                            print(f"  {tense}:")
                        except UnicodeEncodeError:
                            print(f"  [tense]:")
                        
                        for person, form in list(forms.items())[:3]:  # Show first 3 forms
                            if form:
                                try:
                                    print(f"    {person}: {form}")
                                except UnicodeEncodeError:
                                    print(f"    {person}: [form]")
            else:
                print("No conjugation tables found")
            
            # Check if the expected frontend tenses are present
            expected_tenses = ['praesens', 'praeteritum', 'perfekt', 'plusquamperfekt', 'imperativ', 'futur_i', 'futur_ii', 'konjunktiv_i', 'konjunktiv_ii']
            
            if tables:
                print(f"\nFrontend compatibility check:")
                available_tenses = set(tables.keys())
                
                for expected in expected_tenses:
                    if expected in available_tenses:
                        try:
                            print(f"  ✓ {expected} - Available")
                        except UnicodeEncodeError:
                            print(f"  OK {expected} - Available")
                    else:
                        try:
                            print(f"  ✗ {expected} - Missing")
                        except UnicodeEncodeError:
                            print(f"  X {expected} - Missing")
                
                # Show any unexpected tenses
                unexpected = available_tenses - set(expected_tenses)
                if unexpected:
                    print(f"  Additional tenses: {list(unexpected)}")
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Is the backend running on port 8000?")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test a few different verbs
    test_verbs = ["fahren", "gehen", "sein", "haben"]
    
    for verb in test_verbs:
        test_verb_api(verb)
        print("\n" + "="*50 + "\n")