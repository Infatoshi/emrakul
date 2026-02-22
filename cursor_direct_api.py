#!/usr/bin/env python3
"""Direct Cursor API client for calling models via credits."""

import json
import httpx
import struct
from typing import Iterator
from dataclasses import dataclass

# JWT token from cursor CLI (extracted via NODE_DEBUG=http)
# This token has ~60 day expiry based on the JWT claims
JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKMlIyQzZHU01UN0JLR1pDOUtXSjJXUEYiLCJ0aW1lIjoiMTc2OTQ3NDA3OSIsInJhbmRvbW5lc3MiOiIyYjk1YjU3ZC05M2RiLTRiNzEiLCJleHAiOjE3NzQ2NTgwNzksImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSIsInR5cGUiOiJzZXNzaW9uIn0.dpddYTTCIa2HUMKlhYO0fG8gTR6uRgOh3mli2BbPGvU"

BASE_URL = "https://api2.cursor.sh"

def get_headers(content_type: str = "application/json") -> dict:
    """Get standard headers for Cursor API."""
    return {
        "Authorization": f"Bearer {JWT}",
        "Content-Type": content_type,
        "Connect-Protocol-Version": "1",
        "User-Agent": "connect-es/1.6.1",
    }

def call_json_endpoint(service: str, method: str, payload: dict) -> dict:
    """Call a Cursor API endpoint that accepts JSON."""
    url = f"{BASE_URL}/{service}/{method}"
    r = httpx.post(url, headers=get_headers(), json=payload, timeout=30.0)
    r.raise_for_status()
    return r.json()

def get_user_info() -> dict:
    """Get current user info."""
    return call_json_endpoint("aiserver.v1.DashboardService", "GetMe", {})

def get_models() -> list[dict]:
    """Get list of available models."""
    result = call_json_endpoint("aiserver.v1.AiService", "GetUsableModels", {})
    return result.get("models", [])

@dataclass
class Model:
    """Cursor model info."""
    model_id: str
    display_name: str
    aliases: list[str]

def list_models() -> list[Model]:
    """List available models with human-readable format."""
    models = get_models()
    return [
        Model(
            model_id=m["modelId"],
            display_name=m["displayName"],
            aliases=m.get("aliases", [])
        )
        for m in models
    ]

# Connect-RPC streaming requires special framing:
# Each message is: [flags:1byte][length:4bytes big-endian][payload]
# flags: 0 = normal, 2 = end-stream trailer

def encode_connect_message(data: bytes) -> bytes:
    """Encode a message for Connect streaming protocol."""
    # flags (1 byte) + length (4 bytes big-endian) + data
    return struct.pack(">BI", 0, len(data)) + data

def decode_connect_stream(data: bytes) -> Iterator[bytes]:
    """Decode Connect streaming messages."""
    offset = 0
    while offset < len(data):
        if len(data) - offset < 5:
            break
        flags, length = struct.unpack(">BI", data[offset:offset+5])
        offset += 5
        if offset + length > len(data):
            break
        yield data[offset:offset+length]
        offset += length

def stream_chat_raw(model: str, messages: list[dict]) -> Iterator[str]:
    """
    Attempt to stream chat using Connect protocol.

    Note: This may not work without proper protobuf encoding.
    The Cursor API uses protobuf, not JSON, for streaming.
    """
    # The endpoint that returned 415 suggests we need application/proto
    # This is a placeholder - full implementation requires protobuf definitions

    # For now, the cursor-agent CLI is the reliable way to call models
    # We can wrap it instead of reverse-engineering the full proto schema

    raise NotImplementedError(
        "Direct streaming requires protobuf encoding. "
        "Use cursor-agent CLI wrapper instead."
    )

def chat_via_cli(model: str, prompt: str) -> str:
    """
    Call Cursor models via the cursor-agent CLI.

    This is the reliable method that uses our Cursor credits.
    """
    import subprocess

    result = subprocess.run(
        ["cursor-agent", "--print", "--model", model, prompt],
        capture_output=True,
        text=True,
        timeout=300
    )

    if result.returncode != 0:
        raise RuntimeError(f"cursor-agent failed: {result.stderr}")

    return result.stdout

def chat_via_cli_json(model: str, prompt: str) -> dict:
    """
    Call Cursor models via CLI with JSON output for structured parsing.
    """
    import subprocess

    result = subprocess.run(
        ["cursor-agent", "--print", "--output-format", "json", "--model", model, prompt],
        capture_output=True,
        text=True,
        timeout=300
    )

    if result.returncode != 0:
        raise RuntimeError(f"cursor-agent failed: {result.stderr}")

    return json.loads(result.stdout)

if __name__ == "__main__":
    print("=== Cursor Direct API Test ===\n")

    # Test user info
    user = get_user_info()
    print(f"User: {user.get('firstName')} {user.get('lastName')} ({user.get('email')})")
    print()

    # List models
    print("Available Models:")
    for m in list_models():
        aliases = f" (aliases: {', '.join(m.aliases)})" if m.aliases else ""
        print(f"  - {m.model_id}: {m.display_name}{aliases}")
    print()

    # Test CLI wrapper
    print("=== Testing CLI Wrapper ===")
    try:
        response = chat_via_cli("gpt-5.2", "Say hello in one word")
        print(f"GPT-5.2 response: {response.strip()}")
    except FileNotFoundError:
        print("cursor-agent not found in PATH. Install Cursor CLI first.")
    except Exception as e:
        print(f"CLI error: {e}")
