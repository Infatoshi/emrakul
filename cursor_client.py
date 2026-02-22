#!/usr/bin/env python3
"""
Cursor API Client

Call Claude 4.5 Opus, GPT-5.2 Codex, and other models via Cursor API.
Uses your Cursor subscription credits.

Two modes:
1. Direct API (experimental) - requires exact protobuf encoding
2. CLI wrapper (stable) - wraps cursor-agent for reliable operation

The API uses Connect-RPC protocol (protobuf over HTTP/2).
JSON endpoints work for metadata but streaming chat requires binary protobuf.
"""

import json
import struct
import subprocess
import httpx
import uuid
from dataclasses import dataclass
from typing import Iterator, Optional
from pathlib import Path

# ===== Configuration =====

# JWT token from Cursor CLI (via NODE_DEBUG=http interception)
# Located in ~/.cursor/cli-config.json or via network capture
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb29nbGUtb2F1dGgyfHVzZXJfMDFKMlIyQzZHU01UN0JLR1pDOUtXSjJXUEYiLCJ0aW1lIjoiMTc2OTQ3NDA3OSIsInJhbmRvbW5lc3MiOiIyYjk1YjU3ZC05M2RiLTRiNzEiLCJleHAiOjE3NzQ2NTgwNzksImlzcyI6Imh0dHBzOi8vYXV0aGVudGljYXRpb24uY3Vyc29yLnNoIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBvZmZsaW5lX2FjY2VzcyIsImF1ZCI6Imh0dHBzOi8vY3Vyc29yLmNvbSIsInR5cGUiOiJzZXNzaW9uIn0.dpddYTTCIa2HUMKlhYO0fG8gTR6uRgOh3mli2BbPGvU"

BASE_URL = "https://api2.cursor.sh"

# Model IDs available via Cursor
MODELS = {
    "opus": "claude-4.5-opus-high",
    "opus-thinking": "claude-4.5-opus-high-thinking",
    "sonnet": "claude-4.5-sonnet",
    "sonnet-thinking": "claude-4.5-sonnet-thinking",
    "gpt-5.2": "gpt-5.2",
    "gpt-5.2-high": "gpt-5.2-high",
    "codex": "gpt-5.2-codex",
    "codex-high": "gpt-5.2-codex-high",
    "codex-fast": "gpt-5.2-codex-fast",
    "gemini-3-pro": "gemini-3-pro",
    "gemini-3-flash": "gemini-3-flash",
    "grok": "grok-code-fast-1",
}

# ===== Protobuf Encoding =====

def encode_varint(value: int) -> bytes:
    """Encode an integer as a varint."""
    result = []
    while value > 127:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value)
    return bytes(result)

def encode_string(field_num: int, value: str) -> bytes:
    """Encode a string field."""
    if not value:
        return b""
    encoded = value.encode("utf-8")
    # Wire type 2 (length-delimited) = (field_num << 3) | 2
    tag = encode_varint((field_num << 3) | 2)
    length = encode_varint(len(encoded))
    return tag + length + encoded

def encode_bool(field_num: int, value: bool) -> bytes:
    """Encode a boolean field."""
    if not value:
        return b""
    # Wire type 0 (varint) = (field_num << 3) | 0
    tag = encode_varint((field_num << 3) | 0)
    return tag + encode_varint(1 if value else 0)

def encode_message(field_num: int, data: bytes) -> bytes:
    """Encode a nested message field."""
    if not data:
        return b""
    tag = encode_varint((field_num << 3) | 2)
    length = encode_varint(len(data))
    return tag + length + data

def encode_repeated_message(field_num: int, messages: list[bytes]) -> bytes:
    """Encode repeated message fields."""
    result = b""
    for msg in messages:
        result += encode_message(field_num, msg)
    return result

# ===== Message Encoding =====

def encode_conversation_message(role: str, content: str) -> bytes:
    """
    Encode a conversation message.
    Based on the ConversationMessage type used in StreamUnifiedChatRequest.conversation
    """
    # Field numbers based on extraction (approximate - may need adjustment)
    # The actual message type is 'rt' in minified code
    result = b""
    result += encode_string(1, role)     # role field
    result += encode_string(2, content)  # content field
    return result

def encode_model_details(model_id: str) -> bytes:
    """
    Encode model details.
    Field 5 in StreamUnifiedChatRequest
    """
    return encode_string(1, model_id)

def encode_stream_unified_chat_request(
    messages: list[tuple[str, str]],
    model_id: str,
    conversation_id: Optional[str] = None,
    is_agentic: bool = False,
) -> bytes:
    """
    Encode a StreamUnifiedChatRequest message.

    Args:
        messages: List of (role, content) tuples
        model_id: Model ID to use
        conversation_id: Session ID (generated if not provided)
        is_agentic: Whether to use agentic mode with tools
    """
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    result = b""

    # Field 1: conversation (repeated message)
    for role, content in messages:
        msg = encode_conversation_message(role, content)
        result += encode_message(1, msg)

    # Field 5: model_details
    model_details = encode_model_details(model_id)
    result += encode_message(5, model_details)

    # Field 22: is_chat
    result += encode_bool(22, True)

    # Field 23: conversation_id
    result += encode_string(23, conversation_id)

    # Field 27: is_agentic
    if is_agentic:
        result += encode_bool(27, True)

    # Field 45: is_headless
    result += encode_bool(45, True)

    return result

# ===== Connect Protocol =====

def encode_connect_message(data: bytes) -> bytes:
    """Encode for Connect streaming protocol: [flags:1][length:4 BE][data]"""
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

# ===== API Client =====

@dataclass
class ChatResponse:
    """Response from chat API."""
    text: str
    usage_uuid: Optional[str] = None
    raw_response: Optional[bytes] = None

class CursorClient:
    """Direct Cursor API client."""

    def __init__(self, jwt_token: str = JWT_TOKEN):
        self.jwt_token = jwt_token
        self.client = httpx.Client(http2=True, timeout=300.0)

    def _headers(self, content_type: str = "application/proto") -> dict:
        return {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": content_type,
            "Accept": "application/proto",
            "Connect-Protocol-Version": "1",
            "User-Agent": "connect-es/1.6.1",
        }

    def get_models(self) -> list[dict]:
        """Get available models (uses JSON endpoint)."""
        r = self.client.post(
            f"{BASE_URL}/aiserver.v1.AiService/GetUsableModels",
            headers=self._headers("application/json"),
            json={},
        )
        r.raise_for_status()
        return r.json().get("models", [])

    def get_user(self) -> dict:
        """Get current user info."""
        r = self.client.post(
            f"{BASE_URL}/aiserver.v1.DashboardService/GetMe",
            headers=self._headers("application/json"),
            json={},
        )
        r.raise_for_status()
        return r.json()

    def chat(
        self,
        prompt: str,
        model: str = "gpt-5.2",
        system_prompt: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Send a chat message and get response.

        Args:
            prompt: User message
            model: Model alias or ID (see MODELS dict)
            system_prompt: Optional system prompt
            conversation_id: Optional session ID for continuity

        Returns:
            ChatResponse with text and metadata
        """
        # Resolve model alias
        model_id = MODELS.get(model, model)

        # Build message list
        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("user", prompt))

        # Encode request
        request_bytes = encode_stream_unified_chat_request(
            messages=messages,
            model_id=model_id,
            conversation_id=conversation_id,
        )

        # Wrap for Connect protocol
        body = encode_connect_message(request_bytes)

        # Send request
        r = self.client.post(
            f"{BASE_URL}/aiserver.v1.AiService/StreamChat",
            headers=self._headers("application/proto"),
            content=body,
        )

        if r.status_code != 200:
            # Try to decode error
            error_text = r.text or r.content.decode("utf-8", errors="replace")
            raise RuntimeError(f"API error {r.status_code}: {error_text}")

        # Decode streaming response
        text_parts = []
        for msg_bytes in decode_connect_stream(r.content):
            # Parse the StreamUnifiedChatResponse
            # Field 1 is 'text' (string)
            text = self._extract_string_field(msg_bytes, 1)
            if text:
                text_parts.append(text)

        return ChatResponse(
            text="".join(text_parts),
            raw_response=r.content,
        )

    def _extract_string_field(self, data: bytes, field_num: int) -> Optional[str]:
        """Extract a string field from protobuf bytes."""
        offset = 0
        while offset < len(data):
            try:
                # Read tag
                tag_byte = data[offset]
                wire_type = tag_byte & 0x07
                field = tag_byte >> 3
                offset += 1

                # Handle multi-byte tag
                if tag_byte & 0x80:
                    # Skip complex varint tags for now
                    while offset < len(data) and data[offset] & 0x80:
                        offset += 1
                    offset += 1
                    continue

                if wire_type == 2:  # Length-delimited
                    # Read length
                    length = data[offset]
                    offset += 1
                    if length & 0x80:
                        # Multi-byte length
                        length = length & 0x7F
                        shift = 7
                        while offset < len(data) and data[offset-1] & 0x80:
                            length |= (data[offset] & 0x7F) << shift
                            offset += 1
                            shift += 7

                    if field == field_num:
                        return data[offset:offset+length].decode("utf-8", errors="replace")
                    offset += length
                elif wire_type == 0:  # Varint
                    while offset < len(data) and data[offset] & 0x80:
                        offset += 1
                    offset += 1
                elif wire_type == 1:  # 64-bit
                    offset += 8
                elif wire_type == 5:  # 32-bit
                    offset += 4
                else:
                    break
            except (IndexError, ValueError):
                break
        return None

    def chat_cli(
        self,
        prompt: str,
        model: str = "gpt-5.2",
        system_prompt: Optional[str] = None,
        timeout: int = 300,
        json_output: bool = False,
    ) -> ChatResponse:
        """
        Send a chat message via cursor-agent CLI (stable method).

        This uses the cursor-agent CLI which handles all the protobuf
        encoding correctly. It's more reliable than direct API calls.

        Args:
            prompt: User message
            model: Model alias or ID
            system_prompt: Optional system prompt (prepended to prompt)
            timeout: Timeout in seconds
            json_output: Return JSON metadata

        Returns:
            ChatResponse with text
        """
        model_id = MODELS.get(model, model)

        # Build prompt with system prompt if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Build command
        cmd = ["cursor-agent", "--print", "--model", model_id]
        if json_output:
            cmd.extend(["--output-format", "json"])
        cmd.append(full_prompt)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                raise RuntimeError(f"cursor-agent failed: {result.stderr}")

            if json_output:
                data = json.loads(result.stdout)
                # Extract text from JSON response
                text = ""
                for line in result.stdout.strip().split("\n"):
                    try:
                        msg = json.loads(line)
                        if msg.get("type") == "assistant":
                            content = msg.get("message", {}).get("content", [])
                            for c in content:
                                if c.get("type") == "text":
                                    text += c.get("text", "")
                    except json.JSONDecodeError:
                        continue
                return ChatResponse(text=text.strip())
            else:
                return ChatResponse(text=result.stdout.strip())

        except FileNotFoundError:
            raise RuntimeError("cursor-agent not found. Install Cursor CLI first.")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Request timed out after {timeout}s")

# ===== CLI Interface =====

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Cursor API Client - Call models via Cursor credits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cursor_client.py "Explain Python decorators" --model opus
  cursor_client.py "Write a hello world" --model codex
  cursor_client.py --list-models
  cursor_client.py --user

Available model aliases:
  opus, opus-thinking, sonnet, sonnet-thinking
  gpt-5.2, gpt-5.2-high, codex, codex-high, codex-fast
  gemini-3-pro, gemini-3-flash, grok
"""
    )
    parser.add_argument("prompt", nargs="?", help="Chat prompt")
    parser.add_argument("--model", "-m", default="gpt-5.2", help="Model to use (default: gpt-5.2)")
    parser.add_argument("--system", "-s", help="System prompt")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--user", action="store_true", help="Show user info")
    parser.add_argument("--direct", action="store_true", help="Use direct API (experimental)")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")

    args = parser.parse_args()

    client = CursorClient()

    if args.list_models:
        print("Available models:")
        for m in client.get_models():
            aliases = m.get("aliases", [])
            alias_str = f" ({', '.join(aliases)})" if aliases else ""
            print(f"  {m['modelId']}: {m['displayName']}{alias_str}")
        return

    if args.user:
        user = client.get_user()
        print(f"User: {user.get('firstName')} {user.get('lastName')}")
        print(f"Email: {user.get('email')}")
        return

    if not args.prompt:
        parser.print_help()
        return

    try:
        if args.direct:
            # Experimental direct API (may not work)
            response = client.chat(
                prompt=args.prompt,
                model=args.model,
                system_prompt=args.system,
            )
        else:
            # Stable CLI wrapper
            response = client.chat_cli(
                prompt=args.prompt,
                model=args.model,
                system_prompt=args.system,
                timeout=args.timeout,
            )
        print(response.text)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
