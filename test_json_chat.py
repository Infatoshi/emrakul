#!/usr/bin/env python3
"""Test JSON encoding for StreamChat."""

import httpx

JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKMlIyQzZHU01UN0JLR1pDOUtXSjJXUEYiLCJ0aW1lIjoiMTc2OTQ3NDA3OSIsInJhbmRvbW5lc3MiOiIyYjk1YjU3ZC05M2RiLTRiNzEiLCJleHAiOjE3NzQ2NTgwNzksImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSIsInR5cGUiOiJzZXNzaW9uIn0.dpddYTTCIa2HUMKlhYO0fG8gTR6uRgOh3mli2BbPGvU"

BASE = "https://api2.cursor.sh"

# Try various JSON payload formats
payloads = [
    # Format 1: camelCase
    {
        "conversation": [{"role": "user", "content": "say hello"}],
        "modelDetails": {"modelId": "gpt-5.2"},
        "isChat": True,
        "conversationId": "test-123",
        "isHeadless": True,
    },
    # Format 2: snake_case
    {
        "conversation": [{"role": "user", "content": "say hello"}],
        "model_details": {"model_id": "gpt-5.2"},
        "is_chat": True,
        "conversation_id": "test-123",
        "is_headless": True,
    },
    # Format 3: Simplified
    {
        "conversation": [{"role": "user", "content": "say hello"}],
    },
]

headers = {
    "Authorization": f"Bearer {JWT}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Connect-Protocol-Version": "1",
}

client = httpx.Client(http2=True, timeout=30.0)

for i, payload in enumerate(payloads):
    print(f"\n=== Trying format {i+1} ===")
    print(f"Payload: {payload}")

    try:
        r = client.post(f"{BASE}/aiserver.v1.AiService/StreamChat", headers=headers, json=payload)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500] if r.text else r.content[:500]}")
    except Exception as e:
        print(f"Error: {e}")
