#!/usr/bin/env python3
"""Find the rt class (conversation message type) definition."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# The field was: {no:1,name:"conversation",kind:"message",T:rt,repeated:!0}
# Find class rt with its fields

print("=== Looking for class rt (ConversationMessage) ===")

# Search for rt class definition near message types
# Pattern: class rt extends ... fields=...
rt_pattern = r'class\s+rt\s+extends[^{]*\{[^}]*static\s+runtime[^}]*static\s+typeName="([^"]*)"[^}]*static\s+fields=[^(]*\(\(\)=>\[([^\]]+)\]'

matches = list(re.finditer(rt_pattern, js))
if matches:
    for m in matches:
        print(f"TypeName: {m.group(1)}")
        print(f"Fields: {m.group(2)}")
else:
    print("Pattern not found, trying alternative...")

    # Try finding typeName with ConversationMessage
    print("\n=== Looking for ConversationMessage/ConversationTurn ===")
    for typename in ['ConversationMessage', 'ConversationTurn', 'ChatMessage']:
        idx = js.find(f'typeName="aiserver.v1.{typename}"')
        if idx > 0:
            start = max(0, idx - 2000)
            end = min(len(js), idx + 500)
            print(f"\n--- {typename} ---")
            print(js[start:end])

# Also look at what fields rt actually has by searching for it
print("\n\n=== Searching for 'T:rt' patterns ===")
rt_refs = list(re.finditer(r'T:rt[,}]', js))
print(f"Found {len(rt_refs)} references to T:rt")
if rt_refs:
    for ref in rt_refs[:3]:
        start = max(0, ref.start() - 100)
        end = min(len(js), ref.end() + 100)
        print(f"\n{js[start:end]}")

# Look for u.Gm (ModelDetails)
print("\n\n=== Looking for u.Gm (ModelDetails) ===")
gm_pattern = r'typeName="[^"]*ModelDetails[^"]*"[^}]*fields=[^(]*\(\(\)=>\[([^\]]+)\]'
gm_matches = list(re.finditer(gm_pattern, js))
if gm_matches:
    for m in gm_matches[:2]:
        print(f"Fields: {m.group(1)[:500]}")
