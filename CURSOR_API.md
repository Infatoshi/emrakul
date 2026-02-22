# Cursor API Reverse Engineering Results

## Summary

Successfully reverse-engineered the Cursor CLI to extract API structure and create a working client for calling models (Claude 4.5 Opus, GPT-5.2 Codex, etc.) via Cursor credits.

## API Structure

### Endpoint
- **Base URL**: `https://api2.cursor.sh`
- **Protocol**: Connect-RPC (protobuf over HTTP/2)

### Authentication
- **Method**: Bearer JWT token
- **Token Location**: Extracted via `NODE_DEBUG=http cursor-agent ...`
- **Expiry**: ~60 days (from JWT claims)

### Working JSON Endpoints (metadata)
```
POST /aiserver.v1.DashboardService/GetMe
POST /aiserver.v1.AiService/GetUsableModels
```

### Streaming Chat Endpoint (protobuf only)
```
POST /aiserver.v1.AiService/StreamChat
Content-Type: application/proto
```

## Available Models

| Alias | Model ID | Description |
|-------|----------|-------------|
| opus | claude-4.5-opus-high | Claude 4.5 Opus |
| opus-thinking | claude-4.5-opus-high-thinking | Claude 4.5 Opus with extended thinking |
| sonnet | claude-4.5-sonnet | Claude 4.5 Sonnet |
| gpt-5.2 | gpt-5.2 | GPT-5.2 |
| codex | gpt-5.2-codex | GPT-5.2 Codex (code-optimized) |
| codex-high | gpt-5.2-codex-high | GPT-5.2 Codex High |
| gemini-3-pro | gemini-3-pro | Gemini 3 Pro |
| grok | grok-code-fast-1 | Grok |

## Files Created

### Working Client
- **`cursor_client.py`** - Python client with CLI wrapper (stable) and experimental direct API

### Proto Definitions (extracted)
- **`cursor_api.proto`** - Partial proto definitions extracted from bundled JS
- Key messages: `StreamUnifiedChatRequest`, `StreamUnifiedChatResponse`, `StreamChatToolformerResponse`

### Extraction Scripts
- `cursor_proto_extract.py` - Extracts proto from minified JS
- `find_chat_request.py` - Finds specific message definitions

## Usage

### CLI Wrapper (Recommended - Stable)
```bash
# Using Python client
uv run python cursor_client.py "Your prompt" --model opus
uv run python cursor_client.py "Write code" --model codex

# Direct cursor-agent
cursor-agent --print --model gpt-5.2 "Your prompt"
```

### Python API
```python
from cursor_client import CursorClient

client = CursorClient()

# List models
models = client.get_models()

# Chat (via CLI wrapper - stable)
response = client.chat_cli("Your prompt", model="opus")
print(response.text)

# Chat (direct API - experimental, needs protobuf work)
# response = client.chat("Your prompt", model="opus")
```

## Protobuf Status

The StreamChat endpoint **requires protobuf encoding** - JSON returns 415.

### Extracted Request Structure
```protobuf
message StreamUnifiedChatRequest {
  repeated ConversationMessage conversation = 1;  // Chat history
  ModelDetails model_details = 5;                 // Model selection
  bool is_chat = 22;
  string conversation_id = 23;
  bool is_agentic = 27;
  bool is_headless = 45;
  // ... 70+ total fields
}
```

### Challenge
The exact protobuf field encoding needs to match Cursor's expectations exactly. The minified JS uses variable names like `rt`, `u`, `me` for nested message types, making full reconstruction complex.

### Path Forward
To complete direct API access:
1. Use mitmproxy to capture exact binary request from cursor-agent
2. Decode and match against extracted proto structure
3. Implement precise encoder in Python

For now, the CLI wrapper provides reliable access to all models via Cursor credits.

## Token Extraction

To get your JWT token:
```bash
NODE_DEBUG=http cursor-agent --print "test" 2>&1 | grep authorization
```

The token is in the `Authorization: Bearer <JWT>` header.
