#!/usr/bin/env python3
"""Find the enum W (message type) definition."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find MessageType enum
print("=== Looking for MessageType enum ===")
for pattern in ['MessageType', 'ConversationMessageType', 'aiserver.v1.MessageType']:
    idx = js.find(f'"{pattern}"')
    if idx > 0:
        start = max(0, idx - 500)
        end = min(len(js), idx + 500)
        print(f"\n--- {pattern} ---")
        print(js[start:end])

# Look for enum definition with UNSPECIFIED, USER, ASSISTANT values
print("\n\n=== Looking for USER/ASSISTANT enum values ===")
enum_pattern = r'name:"(USER|ASSISTANT|SYSTEM)"[^}]*no:(\d+)'
for m in re.finditer(enum_pattern, js):
    print(f"Found: {m.group(1)} = {m.group(2)}")

# Find the actual enum W
print("\n\n=== Looking for enum W with MessageType ===")
idx = js.find('getEnumType(W)')
if idx > 0:
    # Search backwards for enum definition
    search_start = max(0, idx - 5000)
    context = js[search_start:idx+100]
    # Find enum W definition
    enum_match = re.search(r'W\s*=\s*[^;]+;', context)
    if enum_match:
        print(f"Enum definition: {enum_match.group(0)[:500]}")

    # Alternative: find where W is defined with enum values
    w_def = re.search(r'function\s+\w+\(W\)[^}]+\}', context)
    if w_def:
        print(f"W function: {w_def.group(0)[:500]}")

# Look for the full enum definition with values
print("\n\n=== Looking for full MessageType enum ===")
type_pattern = r'"aiserver\.v1\.[^"]*Type"[^]]*\[([^\]]+)\]'
for m in re.finditer(type_pattern, js):
    if 'USER' in m.group(1) or 'ASSISTANT' in m.group(1):
        print(f"Found: {m.group(0)[:800]}")
