#!/usr/bin/env python3
"""
Test Cursor API with JSON encoding (Connect-RPC supports both proto and JSON).
"""

import httpx
import json
import uuid

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKMlIyQzZHU01UN0JLR1pDOUtXSjJXUEYiLCJ0aW1lIjoiMTc2OTQ3NDA3OSIsInJhbmRvbW5lc3MiOiIyYjk1YjU3ZC05M2RiLTRiNzEiLCJleHAiOjE3NzQ2NTgwNzksImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSIsInR5cGUiOiJzZXNzaW9uIn0.dpddYTTCIa2HUMKlhYO0fG8gTR6uRgOh3mli2BbPGvU"

BASE_URL = "https://api2.cursor.sh"

client = httpx.Client(http2=True, timeout=120.0)

# Test JSON encoding
print("=== Testing JSON encoding ===")

headers_json = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Connect-Protocol-Version": "1",
}

# Test GetUsableModels (should work with JSON)
print("\n=== GetUsableModels (Unary, JSON) ===")
r = client.post(
    f"{BASE_URL}/agent.v1.AgentService/GetUsableModels",
    headers=headers_json,
    json={"customModelIds": []}
)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    try:
        print(f"Response: {json.dumps(r.json(), indent=2)[:1000]}")
    except:
        print(f"Response: {r.text[:500]}")
else:
    print(f"Response: {r.text[:500]}")

# Test GetDefaultModelForCli
print("\n\n=== GetDefaultModelForCli (Unary, JSON) ===")
r = client.post(
    f"{BASE_URL}/agent.v1.AgentService/GetDefaultModelForCli",
    headers=headers_json,
    json={}
)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    try:
        print(f"Response: {json.dumps(r.json(), indent=2)}")
    except:
        print(f"Response: {r.text[:500]}")
else:
    print(f"Response: {r.text[:500]}")

# Test RunSSE with JSON (streaming)
print("\n\n=== RunSSE (Streaming, JSON) ===")

# Build AgentRunRequest as JSON
agent_request = {
    "conversationState": {
        "rootPromptMessagesJson": [
            json.dumps({"role": "user", "content": "Say hello in exactly 3 words"})
        ]
    },
    "requestedModel": {
        "modelId": "gpt-5.2"
    },
    "modelDetails": {
        "modelId": "gpt-5.2"
    },
    "customSystemPrompt": "You are a helpful assistant. Always respond with exactly 3 words."
}

# For streaming, use stream=True
print("Sending request...")
with client.stream(
    "POST",
    f"{BASE_URL}/agent.v1.AgentService/RunSSE",
    headers=headers_json,
    json=agent_request,
    timeout=60.0
) as response:
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print("\nStreaming response:")
    for i, chunk in enumerate(response.iter_bytes()):
        print(f"Chunk {i}: {chunk[:200]}")
        if i > 10:
            print("(truncated)")
            break
