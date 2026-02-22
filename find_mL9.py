#!/usr/bin/env python3
"""Find the s.mL9 type definition (StreamChat input)."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find where mL9 is defined/exported
print("=== Looking for mL9 definition ===")

# Pattern: class mL9 extends ... or mL9 = class
patterns = [
    r'class\s+mL9\s+extends[^{]+\{[^}]{0,5000}',
    r'mL9\s*=\s*class[^{]+\{[^}]{0,5000}',
    r'\.mL9\s*=\s*[^;]+',
    r'mL9[^,}]{0,200}typeName[^}]+',
]

for pat in patterns:
    matches = list(re.finditer(pat, js))
    if matches:
        print(f"\n--- Pattern: {pat[:50]}... ---")
        for m in matches[:3]:
            print(f"{m.group(0)[:500]}\n")

# Also search for the full field list
print("\n\n=== Looking for field definitions with mL9 ===")
# Find context around mL9
idx = js.find('mL9')
while idx > 0:
    start = max(0, idx - 200)
    end = min(len(js), idx + 800)
    context = js[start:end]
    if 'fields' in context or 'typeName' in context:
        print(f"\n--- Context at {idx} ---")
        print(context)
        print()
    idx = js.find('mL9', idx + 1)
    if idx > 1000000:  # Stop after first 1M chars
        break

# Also find WCW (output type)
print("\n\n=== Looking for WCW (output type) ===")
idx = js.find('WCW')
while idx > 0 and idx < 2000000:
    start = max(0, idx - 100)
    end = min(len(js), idx + 500)
    context = js[start:end]
    if 'typeName' in context:
        print(f"\n--- Context at {idx} ---")
        print(context)
    idx = js.find('WCW', idx + 1)
