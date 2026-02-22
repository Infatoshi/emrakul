#!/usr/bin/env python3
"""Find RunSSE input type from bidi_pb.js."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find the bidi_pb module definition
print("=== Looking for bidi_pb module ===")
idx = js.find('"../proto/dist/generated/aiserver/v1/bidi_pb.js":(')
if idx > 0:
    # Find the module end
    end = js.find('}},"', idx + 100)
    if end < 0:
        end = idx + 5000
    print(js[idx:end])

# Find what $r is exported as
print("\n\n=== Looking for $r class definition ===")
# Search for typeName near $r export
for m in re.finditer(r'typeName="aiserver\.v1\.[^"]*SSE[^"]*"', js):
    start = max(0, m.start() - 800)
    end = min(len(js), m.end() + 200)
    print(f"\n{js[start:end]}")

for m in re.finditer(r'typeName="aiserver\.v1\.SSE[^"]*"', js):
    start = max(0, m.start() - 800)
    end = min(len(js), m.end() + 200)
    print(f"\n{js[start:end]}")
