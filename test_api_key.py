#!/usr/bin/env python3
"""
Test script to verify OpenRouter API key is working
Run this to diagnose the 401 authentication error
"""
import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

async def test_openrouter_key():
    """Test if the OpenRouter API key works"""
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    print("🔍 Testing OpenRouter API Key...")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    print(f"   API Key: {'***' + api_key[-8:] if api_key else 'NOT SET'}")
    print()
    
    if not api_key:
        print("❌ API key not found in environment")
        return False
        
    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        print("🚀 Sending test request...")
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say 'Hello' in German"}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✅ API key works! Response: {result}")
        return True
        
    except Exception as e:
        print(f"❌ API key test failed: {str(e)}")
        if "401" in str(e):
            print("   → This usually means:")
            print("     • API key is invalid or expired")
            print("     • Account doesn't exist or was suspended")
            print("     • Wrong API key format")
        elif "403" in str(e):
            print("   → This usually means:")
            print("     • Account has no credits/insufficient balance")
            print("     • API key doesn't have required permissions")
        elif "429" in str(e):
            print("   → This usually means:")
            print("     • Rate limit exceeded")
            print("     • Try again in a few moments")
        
        print()
        print("💡 Next steps:")
        print("   1. Check your OpenRouter dashboard: https://openrouter.ai/")
        print("   2. Verify your API key is correct")
        print("   3. Check your account balance/credits")
        print("   4. Make sure your account is in good standing")
        
        return False

if __name__ == "__main__":
    asyncio.run(test_openrouter_key())