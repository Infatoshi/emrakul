#!/usr/bin/env python3
"""
Test with the correct GetChatRequest message type.

GetChatRequest (aiserver.v1.GetChatRequest) fields:
- 2: conversation (repeated ConversationMessage)
- 7: model_details (ModelDetails)
- 9: request_id (string)
- 15: conversation_id (string)

ConversationMessage (aiserver.v1.ConversationMessage) fields:
- 1: text (string)
- 2: type (enum: 0=UNSPECIFIED, 1=SYSTEM, 2=USER, 3=ASSISTANT)
"""

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


def encode_message(field_num: int, data: bytes) -> bytes:
    if not data:
        return b""
    tag = encode_varint((field_num << 3) | 2)
    return tag + encode_varint(len(data)) + data


def encode_connect_message(data: bytes) -> bytes:
    return struct.pack(">BI", 0, len(data)) + data


def build_getchat_request(text: str, model: str = "gpt-5.2") -> bytes:
    """Build GetChatRequest message."""
    # ConversationMessage: field 1=text, field 2=type (2=USER)
    conv_msg = encode_string(1, text) + encode_enum(2, 2)

    # ModelDetails: field 1=model_id
    model_details = encode_string(1, model)

    # GetChatRequest
    req = b""
    req += encode_message(2, conv_msg)  # conversation (field 2)
    req += encode_message(7, model_details)  # model_details (field 7)
    req += encode_string(9, str(uuid.uuid4()))  # request_id (field 9)
    req += encode_string(15, str(uuid.uuid4()))  # conversation_id (field 15)

    return req


headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/connect+proto",
    "Connect-Protocol-Version": "1",
}

client = httpx.Client(http2=True, timeout=30.0)

# Test GetChatRequest
print("=== Testing GetChatRequest ===")
req = build_getchat_request("Hello, say hi back in exactly 3 words")
body = encode_connect_message(req)

print(f"Request hex: {body.hex()}")

r = client.post(f"{BASE_URL}/aiserver.v1.AiService/StreamChat", headers=headers, content=body)
print(f"Status: {r.status_code}")
print(f"Response: {r.content[:1000]}")

# Also try the CheckLongFilesFit endpoint (since it uses the same input type)
print("\n\n=== Testing CheckLongFilesFit ===")
r = client.post(f"{BASE_URL}/aiserver.v1.AiService/CheckLongFilesFit", headers=headers, content=body)
print(f"Status: {r.status_code}")
print(f"Response: {r.content[:500]}")
