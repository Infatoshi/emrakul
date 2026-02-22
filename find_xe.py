#!/usr/bin/env python3
"""Find the full StreamUnifiedChatRequest (xe) definition."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find class xe (StreamUnifiedChatRequest)
# The pattern should be: class xe extends ... typeName="aiserver.v1.StreamUnifiedChatRequest"
print("=== Looking for StreamUnifiedChatRequest class ===")

# Search for the actual class definition
idx = js.find('typeName="aiserver.v1.StreamUnifiedChatRequest"')
if idx > 0:
    # Go back to find the class definition start
    start = max(0, idx - 3000)
    end = min(len(js), idx + 500)
    context = js[start:end]

    # Find the class definition
    class_match = re.search(r'class\s+(\w+)\s+extends[^{]*\{[^}]*static\s+runtime[^}]*typeName="aiserver\.v1\.StreamUnifiedChatRequest"[^}]*fields=\w+\.\w+\.util\.newFieldList\(\(\)=>\[([^\]]+)\]', context)
    if class_match:
        print(f"Class name: {class_match.group(1)}")
        print(f"Fields: {class_match.group(2)}")
    else:
        # Print more context
        print(f"Context around StreamUnifiedChatRequest:\n{context}")

# Also search for conversation field definition
print("\n\n=== Looking for conversation field ===")
conv_idx = js.find('name:"conversation"')
while conv_idx > 0:
    start = max(0, conv_idx - 100)
    end = min(len(js), conv_idx + 300)
    context = js[start:end]
    print(f"\n--- At position {conv_idx} ---")
    print(context)
    conv_idx = js.find('name:"conversation"', conv_idx + 1)
    if conv_idx > 3000000:  # Limit search
        break
