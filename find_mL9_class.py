#!/usr/bin/env python3
"""Find where mL9 class is defined."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find the export of mL9
# Patterns like: e.mL9=class... or exports.mL9=...
print("=== Looking for mL9 export/definition ===")

# Search for mL9 assignment
patterns = [
    r'\.mL9\s*=\s*class[^{]*\{[^}]{0,3000}',
    r'\.mL9\s*=\s*[a-zA-Z_$][^;,]{0,500}',
    r'mL9:\s*class[^{]*\{[^}]{0,3000}',
    r'mL9\s*=\s*\([^)]*\)[^{]*\{[^}]{0,3000}',
]

for pat in patterns:
    matches = list(re.finditer(pat, js))
    if matches:
        print(f"\n--- Pattern: {pat[:50]}... ({len(matches)} matches) ---")
        for m in matches[:2]:
            text = m.group(0)
            print(f"{text[:1000]}\n")

# Alternative: find where s.mL9 gets its value by looking at module structure
# Look for patterns like (s.mL9 = ... or s["mL9"] = ...
print("\n\n=== Alternative patterns ===")
alt_patterns = [
    r's\.mL9\s*=\s*[^;,]+',
    r's\["mL9"\]\s*=\s*[^;,]+',
    r'exports\.mL9\s*=\s*[^;,]+',
]

for pat in alt_patterns:
    matches = list(re.finditer(pat, js))
    if matches:
        print(f"\n--- Pattern: {pat} ({len(matches)} matches) ---")
        for m in matches[:3]:
            print(f"{m.group(0)[:500]}\n")

# Search for StreamUnifiedChatRequest typename
print("\n\n=== Looking for StreamUnifiedChatRequest ===")
idx = js.find('StreamUnifiedChatRequest')
if idx > 0:
    start = max(0, idx - 500)
    end = min(len(js), idx + 1500)
    print(f"Context:\n{js[start:end]}")
