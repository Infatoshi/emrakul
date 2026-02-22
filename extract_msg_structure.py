#!/usr/bin/env python3
"""Extract protobuf message structures from Cursor bundle."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find all message type definitions
# Pattern: {runtime:...,typeName:"...",fields:[...]}
type_pattern = r'typeName:"([^"]+)"[^}]*fields:\[([^\]]*)\]'

messages = {}
for match in re.finditer(type_pattern, js):
    type_name = match.group(1)
    fields_str = match.group(2)

    # Parse fields
    field_pattern = r'\{[^}]*no:(\d+)[^}]*name:"([^"]+)"[^}]*kind:"([^"]+)"[^}]*\}'
    fields = []
    for fm in re.finditer(field_pattern, fields_str):
        fields.append({
            'no': int(fm.group(1)),
            'name': fm.group(2),
            'kind': fm.group(3),
        })

    if fields:
        messages[type_name] = fields

print(f"Found {len(messages)} message types\n")

# Look for relevant types
keywords = ['chat', 'message', 'conversation', 'unified', 'stream', 'request']
for name, fields in sorted(messages.items()):
    if any(kw in name.lower() for kw in keywords):
        print(f"\n=== {name} ===")
        for f in fields:
            print(f"  {f['no']}: {f['name']} ({f['kind']})")

# Look specifically for StreamUnifiedChatRequest
print("\n\n=== Looking for StreamUnifiedChatRequest ===")
for name, fields in messages.items():
    if 'StreamUnifiedChat' in name or 'UnifiedChat' in name:
        print(f"\n{name}:")
        for f in sorted(fields, key=lambda x: x['no']):
            print(f"  {f['no']}: {f['name']} ({f['kind']})")

# Find conversation message type by looking for role+content fields
print("\n\n=== Types with 'role' field ===")
for name, fields in messages.items():
    field_names = [f['name'] for f in fields]
    if 'role' in field_names:
        print(f"\n{name}:")
        for f in sorted(fields, key=lambda x: x['no']):
            print(f"  {f['no']}: {f['name']} ({f['kind']})")
