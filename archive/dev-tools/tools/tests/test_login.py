#!/usr/bin/env python3
"""
Test login API directly.
"""

import asyncio
import aiohttp
import json


async def test_login():
    """Test login with the user credentials"""
    
    login_data = {
        "email": "heyeqiu1210@gmail.com",
        "password": "password123"  # Try common passwords
    }
    
    url = "http://localhost:8000/api/auth/login"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=login_data) as response:
                print(f"Status Code: {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")
                
                if response.status == 200:
                    print("✅ Login successful!")
                else:
                    print("❌ Login failed")
                    
                    # Try different common passwords
                    common_passwords = ["123456", "admin", "test123", "heyeqiu1210"]
                    
                    for pwd in common_passwords:
                        print(f"\nTrying password: {pwd}")
                        login_data["password"] = pwd
                        
                        async with session.post(url, json=login_data) as retry_response:
                            print(f"Status: {retry_response.status}")
                            if retry_response.status == 200:
                                print(f"✅ Login successful with password: {pwd}")
                                retry_text = await retry_response.text()
                                print(f"Response: {retry_text}")
                                return
                            else:
                                retry_text = await retry_response.text()
                                print(f"Failed: {retry_text}")
                
        except Exception as e:
            print(f"Error testing login: {e}")


async def main():
    await test_login()


if __name__ == "__main__":
    asyncio.run(main())