#!/usr/bin/env python3
"""Test with StreamUnifiedChatRequestWithTools wrapper."""

import httpx
import struct
import uuid

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKMlIyQzZHU01UN0JLR1pDOUtXSjJXUEYiLCJ0aW1lIjoiMTc2OTQ3NDA3OSIsInJhbmRvbW5lc3MiOiIyYjk1YjU3ZC05M2RiLTRiNzEiLCJleHAiOjE3NzQ2NTgwNzksImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSIsInR5cGUiOiJzZXNzaW9uIn0.dpddYTTCIa2HUMKlhYO0fG8gTR6uRgOh3mli2BbPGvU"

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


def encode_enum(field_num: int, value: int) -> bytes:
    if value == 0:
        return b""
    tag = encode_varint((field_num << 3) | 0)
    return tag + encode_varint(value)


def encode_bool(field_num: int, value: bool) -> bytes:
    if not value:
        return b""
    tag = encode_varint((field_num << 3) | 0)
    return tag + b'\x01'


def encode_message(field_num: int, data: bytes) -> bytes:
    if not data:
        return b""
    tag = encode_varint((field_num << 3) | 2)
    return tag + encode_varint(len(data)) + data


def encode_connect_message(data: bytes) -> bytes:
    return struct.pack(">BI", 0, len(data)) + data


# Build StreamUnifiedChatRequest
def build_request(text: str, model: str = "gpt-5.2") -> bytes:
    # ConversationMessage: field 1=text, field 2=type (2=USER)
    conv_msg = encode_string(1, text) + encode_enum(2, 2)

    # ModelDetails: field 1=model_id
    model_details = encode_string(1, model)

    # StreamUnifiedChatRequest
    req = b""
    req += encode_message(1, conv_msg)  # conversation
    req += encode_message(5, model_details)  # model_details
    req += encode_bool(22, True)  # is_chat
    req += encode_string(23, str(uuid.uuid4()))  # conversation_id
    req += encode_bool(45, True)  # is_headless

    return req


# Test without wrapper first
print("=== Testing direct StreamUnifiedChatRequest ===")
req = build_request("Hello, say hi back")
body = encode_connect_message(req)

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/connect+proto",
    "Connect-Protocol-Version": "1",
}

client = httpx.Client(http2=True, timeout=30.0)
r = client.post(f"{BASE_URL}/aiserver.v1.AiService/StreamChat", headers=headers, content=body)
print(f"Status: {r.status_code}")
print(f"Response: {r.content[:500]}")

# Test with wrapper (StreamUnifiedChatRequestWithTools)
print("\n\n=== Testing with StreamUnifiedChatRequestWithTools wrapper ===")
req = build_request("Hello, say hi back")
wrapped = encode_message(1, req)  # Wrap in field 1 (stream_unified_chat_request)
body = encode_connect_message(wrapped)

r = client.post(f"{BASE_URL}/aiserver.v1.AiService/StreamChat", headers=headers, content=body)
print(f"Status: {r.status_code}")
print(f"Response: {r.content[:500]}")

# Test StreamChatToolformer endpoint
print("\n\n=== Testing StreamChatToolformer endpoint ===")
req = build_request("Hello, say hi back")
body = encode_connect_message(req)

r = client.post(f"{BASE_URL}/aiserver.v1.AiService/StreamChatToolformer", headers=headers, content=body)
print(f"Status: {r.status_code}")
print(f"Response: {r.content[:500]}")
