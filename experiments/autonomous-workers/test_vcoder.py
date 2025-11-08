#!/usr/bin/env python3
"""Quick test of vcoder-120b model via LM Studio."""

from openai import OpenAI

# Connect to LM Studio
client = OpenAI(
    base_url="http://192.168.0.2:1234/v1",
    api_key="not-needed"
)

print("🚀 Testing vcoder-120b-1.0-qx86-hi-mlx")
print("=" * 60)

# List available models
print("\n📋 Available models:")
models = client.models.list()
for model in models.data:
    print(f"  ✓ {model.id}")

# Test completion
print("\n🧪 Testing completion...")
response = client.chat.completions.create(
    model="vcoder-120b-1.0-qx86-hi-mlx",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function to add two numbers. Be concise."}
    ],
    max_tokens=150,
    temperature=0.7
)

print(f"\n✅ Response from vcoder-120b:")
print("-" * 60)
print(response.choices[0].message.content)
print("-" * 60)

print(f"\n📊 Stats:")
print(f"  • Model: {response.model}")
print(f"  • Tokens used: {response.usage.total_tokens}")
print(f"  • Prompt tokens: {response.usage.prompt_tokens}")
print(f"  • Completion tokens: {response.usage.completion_tokens}")

print("\n✅ SUCCESS! vcoder-120b is working with AgencyOS!")
