#!/usr/bin/env python3
"""
Debug frontend login by simulating the exact same request.
"""

import json
import sys

def simulate_frontend_request():
    """Simulate the exact request the frontend makes"""
    
    print("=== Debugging Frontend Login ===")
    print()
    
    # The exact data the frontend sends
    request_data = {
        "email": "heyeqiu1210@gmail.com",
        "password": "123456",
        "remember_me": False
    }
    
    print("Request Data:")
    print(json.dumps(request_data, indent=2))
    print()
    
    # Test with curl to match frontend exactly
    import subprocess
    
    curl_cmd = [
        'curl', '-X', 'POST',
        'http://localhost:8000/auth/login',
        '-H', 'Content-Type: application/json',
        '-H', 'Accept: application/json',
        '-d', json.dumps(request_data),
        '--silent',
        '--show-error'
    ]
    
    try:
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        
        print(f"Exit Code: {result.returncode}")
        print(f"Response: {result.stdout}")
        
        if result.stderr:
            print(f"Error: {result.stderr}")
            
        # Parse response
        if result.returncode == 0 and result.stdout:
            try:
                response_data = json.loads(result.stdout)
                print("\nParsed Response:")
                for key, value in response_data.items():
                    if key == 'access_token':
                        print(f"  {key}: {value[:50]}...")
                    elif key == 'refresh_token':
                        print(f"  {key}: {value[:50]}...")
                    else:
                        print(f"  {key}: {value}")
                        
                return True
            except json.JSONDecodeError:
                print("Failed to parse JSON response")
                return False
        else:
            print("Request failed")
            return False
            
    except Exception as e:
        print(f"Error running curl: {e}")
        return False


if __name__ == "__main__":
    simulate_frontend_request()