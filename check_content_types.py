#!/usr/bin/env python3
"""Test different content types for Cursor API."""

import httpx
import struct

# JWT Token
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKMlIyQzZHU01UN0JLR1pDOUtXSjJXUEYiLCJ0aW1lIjoiMTc2OTQ3NDA3OSIsInJhbmRvbW5lc3MiOiIyYjk1YjU3ZC05M2RiLTRiNzEiLCJleHAiOjE3NzQ2NTgwNzksImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSIsInR5cGUiOiJzZXNzaW9uIn0.dpddYTTCIa2HUMKlhYO0fG8gTR6uRgOh3mli2BbPGvU"

BASE_URL = "https://api2.cursor.sh"

# Test body (Connect protocol framing)
test_body = bytes.fromhex("00000000420a080a047465737410022a090a076770742d352e32b00101ba012463663536343936392d353736372d346438322d623561322d386639646533326532346566e80201")

content_types = [
    "application/proto",
    "application/connect+proto",
    "application/grpc",
    "application/grpc+proto",
    "application/x-protobuf",
    "application/octet-stream",
]

client = httpx.Client(http2=True, timeout=30.0)

for ct in content_types:
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": ct,
        "Accept": ct,
        "Connect-Protocol-Version": "1",
    }

    try:
        r = client.post(
            f"{BASE_URL}/aiserver.v1.AiService/StreamChat",
            headers=headers,
            content=test_body,
        )
        print(f"{ct}: {r.status_code}")
        if r.status_code != 415:
            print(f"  Response: {r.content[:200]}")
    except Exception as e:
        print(f"{ct}: Error - {e}")

# Also try with connect-web headers
print("\n--- Testing connect-web ---")
headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/connect+proto",
    "Connect-Protocol-Version": "1",
    "Connect-Content-Encoding": "identity",
    "Connect-Accept-Encoding": "identity",
}
r = client.post(
    f"{BASE_URL}/aiserver.v1.AiService/StreamChat",
    headers=headers,
    content=test_body,
)
print(f"connect+proto: {r.status_code}")
if r.status_code != 415:
    print(f"  Response: {r.content[:200]}")
