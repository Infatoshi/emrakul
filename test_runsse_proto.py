#!/usr/bin/env python3
"""
Test agent.v1.AgentService/RunSSE with proto encoding and streaming.
"""

import httpx
import struct
import uuid
import json

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKMlIyQzZHU01UN0JLR1pDOUtXSjJXUEYiLCJ0aW1lIjoiMTc2OTQ3NDA3OSIsInJhbmRvbm5lc3MiOiIyYjk1YjU3ZC05M2RiLTRiNzEiLCJleHAiOjE3NzQ2NTgwNzksImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSIsInR5cGUiOiJzZXNzaW9uIn0.dpddYTTCIa2HUMKlhYO0fG8gTR6uRgOh3mli2BbPGvU"

BASE_URL = "https://api2.cursor.sh"


def encode_varint(value: int) -> bytes:
    parts = []
    while value > 0x7f:
        parts.append((value & 0x7f) | 0x80)
        value >>= 7
    parts.append(value)
    return bytes(parts) if parts else b'\x00'


def encode_string(field_num: int, value: str) -> bytes:
    if not value:
        return b""
    data = value.encode('utf-8')
    tag = encode_varint((field_num << 3) | 2)
    return tag + encode_varint(len(data)) + data


def encode_message(field_num: int, data: bytes) -> bytes:
    if not data:
        return b""
    tag = encode_varint((field_num << 3) | 2)
    return tag + encode_varint(len(data)) + data


def encode_connect_message(data: bytes) -> bytes:
    """Connect protocol framing."""
    return struct.pack(">BI", 0, len(data)) + data


def build_bidi_request_id(request_id: str) -> bytes:
    """aiserver.v1.BidiRequestId"""
    return encode_string(1, request_id)


def build_conversation_state(user_message: str) -> bytes:
    """agent.v1.ConversationState - minimal."""
    # Field 1: root_prompt_messages_json (repeated string)
    msg_json = json.dumps({"role": "user", "content": user_message})
    return encode_string(1, msg_json)


def build_model_details(model_id: str) -> bytes:
    """agent.v1.ModelDetails"""
    return encode_string(1, model_id)


def build_requested_model(model_id: str) -> bytes:
    """agent.v1.RequestedModel"""
    return encode_string(1, model_id)


def build_agent_run_request(
    user_message: str,
    model_id: str,
    custom_system_prompt: str = None
) -> bytes:
    """Build agent.v1.AgentRunRequest."""
    req = b""
    # Field 1: conversation_state
    req += encode_message(1, build_conversation_state(user_message))
    # Field 3: model_details
    req += encode_message(3, build_model_details(model_id))
    # Field 8: custom_system_prompt (optional)
    if custom_system_prompt:
        req += encode_string(8, custom_system_prompt)
    # Field 9: requested_model (optional)
    req += encode_message(9, build_requested_model(model_id))
    return req


headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/connect+proto",
    "Connect-Protocol-Version": "1",
}

client = httpx.Client(http2=True, timeout=120.0)

# Build request
req = build_agent_run_request(
    "Say hello in exactly 3 words",
    "gpt-5.2",
    "You are a helpful assistant. Always respond with exactly 3 words."
)
body = encode_connect_message(req)

print(f"Request size: {len(body)} bytes")
print(f"Request hex (first 200): {body[:200].hex()}")

print("\n=== Testing agent.v1.AgentService/RunSSE with streaming ===")

with client.stream(
    "POST",
    f"{BASE_URL}/agent.v1.AgentService/RunSSE",
    headers=headers,
    content=body,
    timeout=120.0
) as response:
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")

    if response.status_code == 200:
        print("\nStreaming response:")
        full_response = b""
        for chunk in response.iter_bytes():
            full_response += chunk
            print(f"Chunk ({len(chunk)} bytes): {chunk[:100]}")

        print(f"\nTotal response: {len(full_response)} bytes")
        print(f"Hex: {full_response[:500].hex()}")

        # Try to decode Connect frames
        print("\n=== Decoding Connect frames ===")
        offset = 0
        while offset < len(full_response):
            if len(full_response) - offset < 5:
                break
            flags, length = struct.unpack(">BI", full_response[offset:offset+5])
            offset += 5
            if offset + length > len(full_response):
                break
            frame_data = full_response[offset:offset+length]
            offset += length

            print(f"\nFrame: flags={flags}, length={length}")
            print(f"  Data (first 200): {frame_data[:200]}")

            # If flags & 2, it's a trailer (JSON error)
            if flags & 2:
                try:
                    print(f"  Trailer JSON: {frame_data.decode('utf-8')}")
                except:
                    pass
    else:
        print(f"Error: {response.read()}")
