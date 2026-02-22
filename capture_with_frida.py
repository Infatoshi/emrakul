#!/usr/bin/env python3
"""
Alternative approach: Use the cursor-agent but hook into its protobuf encoding
to see what it actually sends.
"""

import subprocess
import json
import re
from pathlib import Path

# Read the minified bundle and search for message structures
js = Path("/tmp/cursor-index.js").read_text()

# Find the StreamUnifiedChatRequest input type
# Look for patterns like: I:typeName,O:typeName for input/output
print("=== Searching for StreamChat I/O types ===")

# Find StreamChat method with its input/output types
# Pattern in protobuf-es: {name:"StreamChat",I:SomeType,O:SomeOtherType}
idx = js.find('"StreamChat"')
if idx > 0:
    # Get context around it
    start = max(0, idx - 500)
    end = min(len(js), idx + 1000)
    context = js[start:end]
    print(f"Context around StreamChat:\n{context}\n")

# Alternative: find field definitions with kind:"message"
print("\n=== Field definitions with message type ===")

# Look for field definitions that reference other messages
# Pattern: {no:N,name:"...",kind:"message",T:SomeClass}
field_pattern = r'\{no:(\d+),name:"([^"]+)",kind:"message",T:([^,}]+)'
matches = list(re.finditer(field_pattern, js))
print(f"Found {len(matches)} message field references")

for m in matches[:50]:
    field_no = m.group(1)
    field_name = m.group(2)
    type_ref = m.group(3)
    print(f"  {field_no}: {field_name} -> {type_ref}")

# Find where these types are defined
print("\n\n=== Looking for type definitions ===")
# Look for class definitions that are protobuf messages
class_pattern = r'class\s+(\w+)\s+extends\s+\w+\s*\{[^}]*static\s+runtime[^}]*typeName'
for m in re.finditer(class_pattern, js[:500000]):  # First 500K chars
    print(f"Found: {m.group(0)[:200]}")
