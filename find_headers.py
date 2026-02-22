#!/usr/bin/env python3
"""Find what headers cursor-agent sends."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Look for header patterns
print("=== Looking for authorization/header patterns ===")
patterns = [
    r'["\']x-cursor-[^"\']+',
    r'["\']X-[Cc]ursor-[^"\']+',
    r'Authorization[^}]{0,200}',
    r'headers\s*[:=]\s*\{[^}]+\}',
    r'x-ghost-mode',
    r'x-cursor-checksum',
    r'x-request-id',
]

for pat in patterns:
    matches = list(re.finditer(pat, js, re.IGNORECASE))
    if matches:
        print(f"\n--- Pattern: {pat} ({len(matches)} matches) ---")
        for m in matches[:5]:
            start = max(0, m.start() - 50)
            end = min(len(js), m.end() + 50)
            print(f"  ...{js[start:end]}...")

# Look for user-agent strings
print("\n\n=== Looking for user-agent ===")
idx = js.find('cursor/')
if idx > 0:
    start = max(0, idx - 100)
    end = min(len(js), idx + 200)
    print(js[start:end])
