#!/usr/bin/env python3
"""Find the zi class definition (the actual StreamUnifiedChatRequest)."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find class zi definition
print("=== Looking for class zi ===")
patterns = [
    r'class zi extends[^{]+\{[^}]*typeName[^}]+fields[^]]+\]',
    r'\bzi\s*=\s*class[^{]+\{',
    r'class\s+zi\s+extends',
]

for pat in patterns:
    matches = list(re.finditer(pat, js))
    if matches:
        print(f"\n--- Pattern: {pat[:50]}... ({len(matches)} matches) ---")
        for m in matches[:1]:
            start = max(0, m.start() - 100)
            end = min(len(js), m.end() + 3000)
            print(f"{js[start:end][:4000]}\n{'='*60}")

# Alternative: search for zi with typeName
print("\n\n=== Looking for zi with its fields ===")
idx = js.find('class zi ')
if idx > 0:
    end = min(len(js), idx + 5000)
    print(js[idx:end])
