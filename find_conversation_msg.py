#!/usr/bin/env python3
"""Find the ConversationMessage structure in Cursor bundle."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# The conversation field is type 'rt' based on our extraction
# Let's find what 'rt' is

# Search for class definitions that look like conversation messages
patterns = [
    r'typeName="[^"]*[Cc]onversation[^"]*"',
    r'typeName="[^"]*[Mm]essage[^"]*"',
    r'"role"[^}]{0,200}"content"',
    r'role.*kind:"scalar".*content.*kind:',
]

for pat in patterns:
    print(f"\n=== Pattern: {pat} ===")
    matches = re.findall(pat, js)
    for m in matches[:5]:
        print(f"  {m[:200]}")

# Find the specific 'rt' class
print("\n\n=== Looking for 'rt' class definition ===")
# In minified JS, look for: class rt extends
rt_match = re.search(r'class rt extends[^}]+\{[^}]+typeName="([^"]+)"[^}]+fields=[^]]+\]', js)
if rt_match:
    print(f"Found: {rt_match.group(0)[:500]}")

# Try finding message structure near "conversation"
print("\n\n=== Context around 'conversation' field ===")
conv_matches = re.finditer(r'name:"conversation"[^}]+', js)
for m in list(conv_matches)[:3]:
    start = max(0, m.start() - 100)
    end = min(len(js), m.end() + 500)
    print(f"Context: ...{js[start:end]}...")
    print()
