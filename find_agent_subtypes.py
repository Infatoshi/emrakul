#!/usr/bin/env python3
"""Find agent.v1 sub-message types."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find ConversationState
print("=== Looking for ConversationState ===")
for m in re.finditer(r'typeName="agent\.v1\.ConversationState"[^}]*fields[^]]+\]', js):
    start = max(0, m.start() - 500)
    end = min(len(js), m.end() + 100)
    print(f"\n{js[start:end]}")

# Find Action
print("\n\n=== Looking for agent.v1.Action ===")
for m in re.finditer(r'typeName="agent\.v1\.Action"[^}]*fields[^]]+\]', js):
    start = max(0, m.start() - 500)
    end = min(len(js), m.end() + 100)
    print(f"\n{js[start:end]}")

# Find ModelDetails for agent
print("\n\n=== Looking for agent.v1 ModelDetails ===")
for m in re.finditer(r'typeName="agent\.v1\.[^"]*Model[^"]*"[^}]*fields[^]]+\]', js):
    start = max(0, m.start() - 300)
    end = min(len(js), m.end() + 100)
    print(f"\n{js[start:end]}")

# Find the RunSSE input type (bidi_pb.$r)
print("\n\n=== Looking for RunSSE input type ===")
idx = js.find('"../proto/dist/generated/aiserver/v1/bidi_pb.js"')
if idx > 0:
    end = min(len(js), idx + 3000)
    print(js[idx:end])
