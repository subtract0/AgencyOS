#!/usr/bin/env python3
"""Test LM Studio connectivity with vcoder-120b model."""

import os
from openai import OpenAI

# LM Studio Configuration
# Note: LM Studio typically runs on port 1234 for the API server
# Port 41343 seems to be the UI/web interface
LM_STUDIO_PORTS = [1234, 41343, 8080]

def test_lm_studio_connection():
    """Test connection to LM Studio on various ports."""
    
    print("🔍 Testing LM Studio Connection")
    print("=" * 50)
    
    for port in LM_STUDIO_PORTS:
        print(f"\n📡 Testing port {port}...")
        
        try:
            # Create OpenAI client pointing to LM Studio
            client = OpenAI(
                base_url=f"http://localhost:{port}/v1",
                api_key="lm-studio"  # LM Studio doesn't need real auth
            )
            
            # List models
            models = client.models.list()
            print(f"✅ Connected to port {port}!")
            print(f"   Available models: {len(models.data)}")
            
            for model in models.data:
                print(f"   - {model.id}")
            
            # Try a simple completion
            if models.data:
                model_name = models.data[0].id
                print(f"\n🧪 Testing completion with model: {model_name}")
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Say 'Hello from vcoder-120b!' in one line."}
                    ],
                    max_tokens=50
                )
                
                print(f"✅ Response: {response.choices[0].message.content}")
                print(f"\n🎯 Success! LM Studio is working on port {port}")
                print(f"   Model ID to use: {model_name}")
                print(f"\n📝 Update your .env with:")
                print(f"   OPENAI_API_BASE=http://localhost:{port}/v1")
                print(f"   AGENCY_MODEL=openai/{model_name}")
                return port, model_name
                
        except Exception as e:
            print(f"❌ Port {port} failed: {str(e)[:100]}")
    
    print("\n⚠️  Could not connect to LM Studio on any port")
    print("   Make sure LM Studio is running with 'Local Server' enabled")
    print("   Check LM Studio → Developer → Start Server")
    return None, None

if __name__ == "__main__":
    port, model = test_lm_studio_connection()
    
    if port:
        print("\n" + "=" * 50)
        print("✅ Configuration Ready!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ Configuration Failed")
        print("=" * 50)
