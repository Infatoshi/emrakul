#!/usr/bin/env python3
"""
Direct Cursor API client with proper protobuf encoding.

Based on extracted proto definitions from cursor-agent bundle.
"""

import struct
import httpx
import uuid
from typing import Optional, Iterator
from dataclasses import dataclass

# ===== Configuration =====

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKMlIyQzZHU01UN0JLR1pDOUtXSjJXUEYiLCJ0aW1lIjoiMTc2OTQ3NDA3OSIsInJhbmRvbW5lc3MiOiIyYjk1YjU3ZC05M2RiLTRiNzEiLCJleHAiOjE3NzQ2NTgwNzksImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSIsInR5cGUiOiJzZXNzaW9uIn0.dpddYTTCIa2HUMKlhYO0fG8gTR6uRgOh3mli2BbPGvU"

BASE_URL = "https://api2.cursor.sh"

# ===== Protobuf Encoding =====

def encode_varint(value: int) -> bytes:
    """Encode unsigned integer as varint."""
    parts = []
    while value > 0x7f:
        parts.append((value & 0x7f) | 0x80)
        value >>= 7
    parts.append(value)
    return bytes(parts) if parts else b'\x00'

def encode_string(field_num: int, value: str) -> bytes:
    """Encode string field (wire type 2)."""
    if not value:
        return b""
    data = value.encode('utf-8')
    tag = encode_varint((field_num << 3) | 2)
    return tag + encode_varint(len(data)) + data

def encode_bytes(field_num: int, value: bytes) -> bytes:
    """Encode bytes field (wire type 2)."""
    if not value:
        return b""
    tag = encode_varint((field_num << 3) | 2)
    return tag + encode_varint(len(value)) + value

def encode_bool(field_num: int, value: bool) -> bytes:
    """Encode bool field (wire type 0)."""
    if not value:
        return b""
    tag = encode_varint((field_num << 3) | 0)
    return tag + b'\x01'

def encode_int32(field_num: int, value: int) -> bytes:
    """Encode int32 field (wire type 0)."""
    if value == 0:
        return b""
    tag = encode_varint((field_num << 3) | 0)
    return tag + encode_varint(value)

def encode_message(field_num: int, data: bytes) -> bytes:
    """Encode embedded message (wire type 2)."""
    if not data:
        return b""
    tag = encode_varint((field_num << 3) | 2)
    return tag + encode_varint(len(data)) + data

# ===== Message Type Enum =====

class MessageType:
    """aiserver.v1.PureMessage.MessageType enum values."""
    UNSPECIFIED = 0
    SYSTEM = 1
    USER = 2
    ASSISTANT = 3


def encode_enum(field_num: int, value: int) -> bytes:
    """Encode enum field (wire type 0)."""
    if value == 0:
        return b""
    tag = encode_varint((field_num << 3) | 0)
    return tag + encode_varint(value)


# ===== Message Encoding =====

def encode_conversation_message(text: str, msg_type: int) -> bytes:
    """
    Encode a ConversationMessage for the conversation field.

    Based on extracted proto (aiserver.v1.ConversationMessage):
    - Field 1: text (string)
    - Field 2: type (enum MessageType)
    """
    msg = b""
    msg += encode_string(1, text)
    msg += encode_enum(2, msg_type)
    return msg

def encode_model_details(model_id: str) -> bytes:
    """
    Encode ModelDetails message.

    Based on extracted proto - modelDetails field 5 in StreamUnifiedChatRequest
    """
    return encode_string(1, model_id)

def role_to_type(role: str) -> int:
    """Convert role string to MessageType enum value."""
    mapping = {
        "system": MessageType.SYSTEM,
        "user": MessageType.USER,
        "assistant": MessageType.ASSISTANT,
    }
    return mapping.get(role.lower(), MessageType.UNSPECIFIED)


def encode_stream_unified_chat_request(
    messages: list[tuple[str, str]],
    model_id: str,
    system_prompt: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> bytes:
    """
    Encode StreamUnifiedChatRequest.

    Key fields from extraction (aiserver.v1.StreamUnifiedChatRequest):
    - 1: conversation (repeated ConversationMessage)
    - 5: model_details (message)
    - 22: is_chat (bool)
    - 23: conversation_id (string)
    - 45: is_headless (bool)
    """
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    result = b""

    # Add system message if provided
    if system_prompt:
        msg = encode_conversation_message(system_prompt, MessageType.SYSTEM)
        result += encode_message(1, msg)

    # Add conversation messages
    for role, content in messages:
        msg_type = role_to_type(role)
        msg = encode_conversation_message(content, msg_type)
        result += encode_message(1, msg)

    # Model details (field 5)
    model_details = encode_model_details(model_id)
    result += encode_message(5, model_details)

    # is_chat (field 22)
    result += encode_bool(22, True)

    # conversation_id (field 23)
    result += encode_string(23, conversation_id)

    # is_headless (field 45)
    result += encode_bool(45, True)

    return result

# ===== Connect Protocol =====

def encode_connect_message(data: bytes) -> bytes:
    """Encode for Connect streaming: [flags:1][length:4 BE][data]"""
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

def extract_text_from_response(data: bytes) -> str:
    """Extract text field (field 1) from StreamUnifiedChatResponse."""
    texts = []
    offset = 0
    while offset < len(data):
        if offset >= len(data):
            break
        try:
            tag = data[offset]
            field_num = tag >> 3
            wire_type = tag & 0x07
            offset += 1

            if wire_type == 2:  # Length-delimited
                # Read length (varint)
                length = 0
                shift = 0
                while offset < len(data):
                    b = data[offset]
                    offset += 1
                    length |= (b & 0x7f) << shift
                    if not (b & 0x80):
                        break
                    shift += 7

                if field_num == 1:  # text field
                    texts.append(data[offset:offset+length].decode('utf-8', errors='replace'))
                offset += length
            elif wire_type == 0:  # Varint
                while offset < len(data) and data[offset] & 0x80:
                    offset += 1
                offset += 1
            else:
                break
        except:
            break
    return "".join(texts)

# ===== API Client =====

@dataclass
class ChatResponse:
    text: str
    raw: Optional[bytes] = None

class CursorDirectClient:
    """Direct Cursor API client with protobuf encoding."""

    def __init__(self, jwt_token: str = JWT_TOKEN):
        self.jwt_token = jwt_token
        self.client = httpx.Client(http2=True, timeout=300.0)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/proto",
            "Accept": "application/proto",
            "Connect-Protocol-Version": "1",
            "User-Agent": "cursor-direct/1.0",
        }

    def chat(
        self,
        prompt: str,
        model: str = "gpt-5.2",
        system_prompt: Optional[str] = None,
    ) -> ChatResponse:
        """Send chat request with custom system prompt."""

        # Encode request
        request_bytes = encode_stream_unified_chat_request(
            messages=[("user", prompt)],
            model_id=model,
            system_prompt=system_prompt,
        )

        # Wrap for Connect protocol
        body = encode_connect_message(request_bytes)

        print(f"Request size: {len(body)} bytes")
        print(f"Request hex (first 200): {body[:200].hex()}")

        # Send request
        r = self.client.post(
            f"{BASE_URL}/aiserver.v1.AiService/StreamChat",
            headers=self._headers(),
            content=body,
        )

        print(f"Response status: {r.status_code}")
        print(f"Response headers: {dict(r.headers)}")

        if r.status_code != 200:
            print(f"Error response: {r.content[:500]}")
            raise RuntimeError(f"API error {r.status_code}")

        # Decode response
        texts = []
        for msg in decode_connect_stream(r.content):
            text = extract_text_from_response(msg)
            if text:
                texts.append(text)

        return ChatResponse(text="".join(texts), raw=r.content)

def main():
    print("Testing direct Cursor API with protobuf encoding\n")

    client = CursorDirectClient()

    try:
        response = client.chat(
            prompt="Say hello in exactly 3 words.",
            model="gpt-5.2",
            system_prompt="You are a helpful assistant. Be concise.",
        )
        print(f"\nResponse: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

        # Debug: save the request for analysis
        request_bytes = encode_stream_unified_chat_request(
            messages=[("user", "test")],
            model_id="gpt-5.2",
        )
        body = encode_connect_message(request_bytes)

        with open("/tmp/cursor_test_request.bin", "wb") as f:
            f.write(body)
        print(f"\nSaved test request to /tmp/cursor_test_request.bin")
        print(f"Hex: {body.hex()}")

if __name__ == "__main__":
    main()
