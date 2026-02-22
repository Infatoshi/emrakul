#!/usr/bin/env python3
"""
Test using your own API key through Cursor's agent service.

RequestedModel structure:
- model_id: string
- max_mode: bool
- api_key_credentials: {api_key, base_url}
"""

import httpx
import json
import os

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKMlIyQzZHU01UN0JLR1pDOUtXSjJXUEYiLCJ0aW1lIjoiMTc2OTQ3NDA3OSIsInJhbmRvbm5lc3MiOiIyYjk1YjU3ZC05M2RiLTRiNzEiLCJleHAiOjE3NzQ2NTgwNzksImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSIsInR5cGUiOiJzZXNzaW9uIn0.dpddYTTCIa2HUMKlhYO0fG8gTR6uRgOh3mli2BbPGvU"

BASE_URL = "https://api2.cursor.sh"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json",
    "Connect-Protocol-Version": "1",
    "x-ghost-mode": "false",
    "x-cursor-client-version": "cli-2026.01.28-fd13201",
    "x-cursor-client-type": "cli",
}

client = httpx.Client(http2=True, timeout=30.0)

# Check GetAllowedModelIntents to see what's allowed
print("=== Checking allowed model intents ===")
r = client.post(
    f"{BASE_URL}/agent.v1.AgentService/GetAllowedModelIntents",
    headers=headers,
    json={},
)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    try:
        data = r.json()
        print(f"Model intents: {data.get('modelIntents', [])}")
    except:
        print(f"Response: {r.text[:500]}")

# Check GetUsableModels with custom model IDs
print("\n\n=== Checking usable models with custom IDs ===")
r = client.post(
    f"{BASE_URL}/agent.v1.AgentService/GetUsableModels",
    headers=headers,
    json={"customModelIds": ["claude-3-opus-20240229", "claude-3-5-sonnet-20241022"]},
)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    try:
        data = r.json()
        for m in data.get('models', [])[:5]:
            print(f"  - {m.get('modelId')}: {m.get('displayName')}")
    except:
        print(f"Response: {r.text[:500]}")

# Check if there's a way to list custom models or API key models
print("\n\n=== Looking for custom/API key model support ===")

# Try to see if we can query model capabilities
endpoints = [
    "/aiserver.v1.AiService/GetUserInfo",
    "/aiserver.v1.DashboardService/GetUsage",
]

for endpoint in endpoints:
    print(f"\n--- Testing {endpoint} ---")
    try:
        r = client.post(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            json={},
            timeout=10.0
        )
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            try:
                print(f"Response: {json.dumps(r.json(), indent=2)[:500]}")
            except:
                print(f"Response: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
