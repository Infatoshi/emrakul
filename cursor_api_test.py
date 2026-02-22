#!/usr/bin/env python3
"""Test direct Cursor API access."""

import json
import httpx

JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKMlIyQzZHU01UN0JLR1pDOUtXSjJXUEYiLCJ0aW1lIjoiMTc2OTQ3NDA3OSIsInJhbmRvbW5lc3MiOiIyYjk1YjU3ZC05M2RiLTRiNzEiLCJleHAiOjE3NzQ2NTgwNzksImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSIsInR5cGUiOiJzZXNzaW9uIn0.dpddYTTCIa2HUMKlhYO0fG8gTR6uRgOh3mli2BbPGvU"

BASE_URL = "https://api2.cursor.sh"

HEADERS = {
    "Authorization": f"Bearer {JWT}",
    "Content-Type": "application/json",
    "Connect-Protocol-Version": "1",
    "User-Agent": "connect-es/1.6.1",
}

def get_me():
    """Test GetMe endpoint."""
    r = httpx.post(f"{BASE_URL}/aiserver.v1.DashboardService/GetMe", headers=HEADERS, json={})
    print("GetMe:", r.json())
    return r.json()

def get_models():
    """Test GetUsableModels endpoint."""
    r = httpx.post(f"{BASE_URL}/aiserver.v1.AiService/GetUsableModels", headers=HEADERS, json={})
    models = r.json().get("models", [])
    print(f"Found {len(models)} models:")
    for m in models:
        print(f"  - {m['modelId']} ({m['displayName']})")
    return models

def stream_chat(model: str, message: str):
    """Test streaming chat endpoint."""
    # Try various endpoint patterns
    endpoints = [
        "aiserver.v1.AiService/StreamUnifiedChat",
        "aiserver.v1.AiService/StreamChat",
        "aiserver.v1.ChatService/StreamChat",
        "aiserver.v1.AgentService/StreamChatToolformer",
    ]

    payload = {
        "model": model,
        "modelId": model,
        "messages": [{"role": "user", "content": message}],
        "prompt": message,
        "stream": True,
    }

    for endpoint in endpoints:
        print(f"\nTrying {endpoint}...")
        try:
            r = httpx.post(
                f"{BASE_URL}/{endpoint}",
                headers=HEADERS,
                json=payload,
                timeout=30.0
            )
            print(f"  Status: {r.status_code}")
            print(f"  Response: {r.text[:500] if r.text else '(empty)'}")
            if r.status_code == 200:
                return r.text
        except Exception as e:
            print(f"  Error: {e}")

    return None

if __name__ == "__main__":
    print("=== Testing Cursor API ===\n")

    # Test basic endpoints
    get_me()
    print()
    get_models()

    # Try chat
    print("\n=== Testing Chat ===")
    stream_chat("gpt-5.2", "say hello")
