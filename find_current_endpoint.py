#!/usr/bin/env python3
"""Find the actual endpoint cursor-agent uses."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Look for endpoint/path strings
print("=== Looking for /aiserver paths ===")
for m in re.finditer(r'/aiserver[^"\']+', js):
    path = m.group(0)[:100]
    print(f"  {path}")

# Look for streamChat function calls
print("\n\n=== Looking for actual streamChat calls ===")
patterns = [
    r'\.streamChat\s*\([^)]*\)',
    r'streamChat[^(]*\([^)]*\)',
]
for pat in patterns:
    for m in re.finditer(pat, js):
        start = max(0, m.start() - 200)
        end = min(len(js), m.end() + 100)
        context = js[start:end]
        # Filter out method definitions
        if 'name:"StreamChat"' not in context:
            print(f"\n{context}\n{'='*50}")

# Look for agent.v1 service usage
print("\n\n=== Looking for agent.v1 service ===")
for m in re.finditer(r'agent\.v1\.[^"]+', js):
    service = m.group(0)[:80]
    if 'Stream' in service or 'Chat' in service:
        print(f"  {service}")
