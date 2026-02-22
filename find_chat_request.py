#!/usr/bin/env python3
"""Find StreamUnifiedChatRequest fields."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find StreamUnifiedChatRequest
type_name = "aiserver.v1.StreamUnifiedChatRequest"
pattern = f'typeName="{type_name}"'
match = re.search(pattern, js)

if match:
    pos = match.start()
    # Get more context
    context = js[pos:pos+10000]
    print(f"Found at position {pos}")
    print("\nFirst 4000 chars after typeName:")
    print(context[:4000])
else:
    print("Not found")
