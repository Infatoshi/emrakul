#!/usr/bin/env python3
"""
Test the agent.v1.AgentService API with custom system prompt.

Flow:
1. BidiAppend - sends AgentRunRequest data
2. RunSSE/RunPoll - streams responses
"""

import httpx
import struct
import uuid
import json

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


def encode_int64(field_num: int, value: int) -> bytes:
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


def build_bidi_request_id(request_id: str) -> bytes:
    """Build BidiRequestId message."""
    return encode_string(1, request_id)


def build_bidi_append_request(data: str, request_id: str, seqno: int = 0) -> bytes:
    """
    Build BidiAppendRequest:
    - Field 1: data (string)
    - Field 2: request_id (BidiRequestId message)
    - Field 3: append_seqno (int64)
    """
    req = b""
    req += encode_string(1, data)
    req += encode_message(2, build_bidi_request_id(request_id))
    req += encode_int64(3, seqno)
    return req


def build_agent_run_request(user_message: str, model_id: str, custom_system_prompt: str = None) -> dict:
    """Build AgentRunRequest as a JSON-like structure for encoding as the 'data' field."""
    # The data field in BidiAppend is JSON-encoded AgentRunRequest
    # Looking at the structure, it seems like the agent service might accept JSON
    request = {
        "conversationState": {
            "rootPromptMessagesJson": [
                json.dumps({"role": "user", "content": user_message})
            ],
            "turns": []
        },
        "modelDetails": {
            "modelId": model_id
        },
        "requestedModel": {
            "modelId": model_id
        }
    }
    if custom_system_prompt:
        request["customSystemPrompt"] = custom_system_prompt
    return request


headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/connect+proto",
    "Connect-Protocol-Version": "1",
}

client = httpx.Client(http2=True, timeout=30.0)

# Generate a request ID
request_id = str(uuid.uuid4())

print(f"Request ID: {request_id}")

# Try the simplest approach first: just call RunSSE with an AgentRunRequest
# Maybe it doesn't need the BidiAppend step for simple requests

# Build a simple AgentRunRequest
print("\n=== Testing agent.v1.AgentService/RunSSE directly ===")

# Build AgentRunRequest as protobuf
# Field 8: custom_system_prompt (string)
# Field 9: requested_model (RequestedModel with field 1=model_id)

def build_requested_model(model_id: str) -> bytes:
    return encode_string(1, model_id)

def build_conversation_state(user_message: str) -> bytes:
    """Build minimal ConversationState."""
    # Field 1: root_prompt_messages_json (repeated string)
    msg_json = json.dumps({"role": "user", "content": user_message})
    return encode_string(1, msg_json)

def build_model_details(model_id: str) -> bytes:
    """Build ModelDetails."""
    return encode_string(1, model_id)

def build_agent_run_request_proto(
    user_message: str,
    model_id: str,
    custom_system_prompt: str = None
) -> bytes:
    """Build AgentRunRequest as protobuf."""
    req = b""
    # Field 1: conversation_state
    req += encode_message(1, build_conversation_state(user_message))
    # Field 3: model_details
    req += encode_message(3, build_model_details(model_id))
    # Field 8: custom_system_prompt
    if custom_system_prompt:
        req += encode_string(8, custom_system_prompt)
    # Field 9: requested_model
    req += encode_message(9, build_requested_model(model_id))
    return req


# Test with AgentRunRequest directly
req = build_agent_run_request_proto(
    "Hello, say hi back in exactly 3 words",
    "gpt-5.2",
    "You are a helpful assistant. Always respond with exactly 3 words."
)
body = encode_connect_message(req)

print(f"Request hex: {body.hex()[:200]}...")

r = client.post(f"{BASE_URL}/agent.v1.AgentService/RunSSE", headers=headers, content=body)
print(f"Status: {r.status_code}")
print(f"Response: {r.content[:1000]}")

# Try RunPoll
print("\n\n=== Testing agent.v1.AgentService/RunPoll ===")

def build_bidi_poll_request(request_id: str, start_request: bool = True) -> bytes:
    """Build BidiPollRequest."""
    req = b""
    req += encode_message(1, build_bidi_request_id(request_id))
    req += encode_bool(2, start_request)
    return req

req = build_bidi_poll_request(request_id, True)
body = encode_connect_message(req)

r = client.post(f"{BASE_URL}/agent.v1.AgentService/RunPoll", headers=headers, content=body)
print(f"Status: {r.status_code}")
print(f"Response: {r.content[:500]}")

# Try BidiAppend first
print("\n\n=== Testing aiserver.v1.BidiService/BidiAppend ===")

agent_req = build_agent_run_request_proto(
    "Hello, say hi back in exactly 3 words",
    "gpt-5.2",
    "You are a helpful assistant. Always respond with exactly 3 words."
)

# BidiAppend wants JSON-encoded data in the data field
# Or maybe it wants base64-encoded protobuf?
import base64
agent_req_b64 = base64.b64encode(agent_req).decode()

bidi_append = build_bidi_append_request(
    data=agent_req_b64,
    request_id=request_id,
    seqno=0
)
body = encode_connect_message(bidi_append)

r = client.post(f"{BASE_URL}/aiserver.v1.BidiService/BidiAppend", headers=headers, content=body)
print(f"Status: {r.status_code}")
print(f"Response: {r.content[:500]}")
