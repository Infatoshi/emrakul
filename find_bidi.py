#!/usr/bin/env python3
"""Find BidiService and newer endpoints."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find BidiService
print("=== Looking for BidiService ===")
idx = js.find('"BidiService"')
if idx > 0:
    start = max(0, idx - 500)
    end = min(len(js), idx + 2000)
    print(js[start:end])

# Find what calls StreamChat
print("\n\n=== Functions that reference StreamChat ===")
patterns = [
    r'\.streamChat\s*\(',
    r'StreamChat[^"]\w*\(',
    r'/aiserver\.v1\.AiService/Stream',
]
for pat in patterns:
    matches = list(re.finditer(pat, js))
    if matches:
        print(f"\n--- Pattern: {pat} ({len(matches)} matches) ---")
        for m in matches[:3]:
            start = max(0, m.start() - 200)
            end = min(len(js), m.end() + 200)
            print(f"{js[start:end]}\n")

# Look for agent communication
print("\n\n=== Agent/Chat communication patterns ===")
idx = js.find('api2.cursor.sh')
if idx > 0:
    start = max(0, idx - 100)
    end = min(len(js), idx + 200)
    print(f"Found API URL at: {js[start:end]}")

# Search for newer endpoint patterns
print("\n\n=== Newer endpoint patterns ===")
for pattern in ['v2', 'V2', 'Bidi', 'WebSocket', 'ws://']:
    idx = js.find(pattern)
    if idx > 0:
        start = max(0, idx - 100)
        end = min(len(js), idx + 100)
        print(f"\n{pattern}: {js[start:end]}")
