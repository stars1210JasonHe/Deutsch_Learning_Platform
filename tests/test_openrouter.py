#!/usr/bin/env python3
"""Quick test script to verify OpenRouter connection"""

import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

async def test_openrouter():
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    print(f"Testing OpenRouter connection...")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print(f"API Key: {api_key[:20]}..." if api_key else "No API key found")
    
    if not api_key:
        print("ERROR: No OPENAI_API_KEY found in .env file")
        return
    
    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Test chat completion
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say 'Hello from OpenRouter!' in German"}
            ],
            max_tokens=50
        )
        
        print("SUCCESS: OpenRouter connection working!")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Usage: {response.usage}")
        
    except Exception as e:
        print(f"FAILED: OpenRouter connection failed: {e}")
        if "401" in str(e):
            print("TIP: Check your API key and credits at https://openrouter.ai/")
        elif "403" in str(e):
            print("TIP: Check your OpenRouter account permissions")

if __name__ == "__main__":
    asyncio.run(test_openrouter())