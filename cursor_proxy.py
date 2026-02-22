#!/usr/bin/env python3
"""
Cursor-to-Anthropic API Proxy

Makes Cursor API look like Anthropic API so you can use Cursor credits
with any Anthropic-compatible client (like Claude Code).

Usage:
    uv run python cursor_proxy.py

Then set:
    export ANTHROPIC_BASE_URL=http://localhost:8082
    export ANTHROPIC_API_KEY=dummy
"""

import json
import subprocess
import uuid
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn

app = FastAPI(title="Cursor-to-Anthropic Proxy")

# Model mapping: Anthropic model -> Cursor model
MODEL_MAP = {
    # Claude models
    "claude-opus-4-5-20251101": "claude-4.5-opus-high-thinking",
    "claude-sonnet-4-5-20251101": "claude-4.5-sonnet-thinking",
    "claude-3-5-sonnet-20241022": "claude-4.5-sonnet",
    "claude-3-opus-20240229": "claude-4.5-opus-high",
    # Aliases
    "opus": "claude-4.5-opus-high-thinking",
    "sonnet": "claude-4.5-sonnet-thinking",
}

def get_cursor_model(anthropic_model: str) -> str:
    """Map Anthropic model ID to Cursor model ID."""
    return MODEL_MAP.get(anthropic_model, "claude-4.5-opus-high-thinking")

def call_cursor(model: str, messages: list, system: str = None) -> str:
    """Call Cursor via CLI and return response."""
    # Build prompt from messages
    prompt_parts = []
    if system:
        prompt_parts.append(f"System: {system}\n")

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        # Handle content array format
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            content = "\n".join(text_parts)

        if role == "user":
            prompt_parts.append(f"Human: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")

    prompt = "\n\n".join(prompt_parts)

    # Call cursor-agent
    cursor_model = get_cursor_model(model)
    result = subprocess.run(
        ["cursor-agent", "--print", "--model", cursor_model, prompt],
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        raise RuntimeError(f"cursor-agent failed: {result.stderr}")

    return result.stdout.strip()

def format_anthropic_response(text: str, model: str) -> dict:
    """Format response in Anthropic API format."""
    return {
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "model": model,
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": 0,  # Cursor doesn't expose this
            "output_tokens": 0,
        },
    }

def format_anthropic_stream_event(event_type: str, data: dict) -> str:
    """Format a streaming event in Anthropic format."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

@app.post("/v1/messages")
async def create_message(request: Request):
    """Handle Anthropic /v1/messages endpoint."""
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    model = body.get("model", "claude-opus-4-5-20251101")
    messages = body.get("messages", [])
    system = body.get("system", "")
    stream = body.get("stream", False)

    # Handle system as list
    if isinstance(system, list):
        system = "\n".join(
            block.get("text", "") for block in system
            if isinstance(block, dict) and block.get("type") == "text"
        )

    if stream:
        return StreamingResponse(
            stream_response(model, messages, system),
            media_type="text/event-stream",
        )
    else:
        # Non-streaming
        text = call_cursor(model, messages, system)
        return JSONResponse(format_anthropic_response(text, model))

async def stream_response(model: str, messages: list, system: str):
    """Stream response in Anthropic format."""
    msg_id = f"msg_{uuid.uuid4().hex[:24]}"

    # message_start
    yield format_anthropic_stream_event("message_start", {
        "type": "message_start",
        "message": {
            "id": msg_id,
            "type": "message",
            "role": "assistant",
            "content": [],
            "model": model,
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }
    })

    # content_block_start
    yield format_anthropic_stream_event("content_block_start", {
        "type": "content_block_start",
        "index": 0,
        "content_block": {"type": "text", "text": ""},
    })

    # Get response from Cursor (not truly streaming, but we can chunk it)
    try:
        text = call_cursor(model, messages, system)

        # Stream text in chunks
        chunk_size = 20
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            yield format_anthropic_stream_event("content_block_delta", {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": chunk},
            })
    except Exception as e:
        yield format_anthropic_stream_event("error", {
            "type": "error",
            "error": {"type": "api_error", "message": str(e)},
        })
        return

    # content_block_stop
    yield format_anthropic_stream_event("content_block_stop", {
        "type": "content_block_stop",
        "index": 0,
    })

    # message_delta
    yield format_anthropic_stream_event("message_delta", {
        "type": "message_delta",
        "delta": {"stop_reason": "end_turn", "stop_sequence": None},
        "usage": {"output_tokens": len(text) // 4},
    })

    # message_stop
    yield format_anthropic_stream_event("message_stop", {
        "type": "message_stop",
    })

@app.get("/v1/models")
async def list_models():
    """List available models."""
    return {
        "data": [
            {"id": "claude-opus-4-5-20251101", "object": "model"},
            {"id": "claude-sonnet-4-5-20251101", "object": "model"},
        ]
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    print("Starting Cursor-to-Anthropic Proxy on http://localhost:8082")
    print("\nTo use with Claude Code:")
    print("  export ANTHROPIC_BASE_URL=http://localhost:8082")
    print("  export ANTHROPIC_API_KEY=dummy")
    print("\nModel mapping:")
    for k, v in MODEL_MAP.items():
        print(f"  {k} -> {v}")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8082)
