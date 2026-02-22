#!/usr/bin/env python3
"""Find agent.v1 message types for Run/RunSSE."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find u.KS (input type for Run)
print("=== Looking for u.KS (Run input type) ===")
idx = js.find('KS:')
count = 0
while idx > 0 and count < 5:
    start = max(0, idx - 200)
    end = min(len(js), idx + 100)
    context = js[start:end]
    if '()=>' in context:
        print(f"\n{context}")
    idx = js.find('KS:', idx + 1)
    count += 1

# Find i.$r (input type for RunSSE)
print("\n\n=== Looking for $r (RunSSE input type) ===")
idx = js.find('$r:')
count = 0
while idx > 0 and count < 10:
    start = max(0, idx - 200)
    end = min(len(js), idx + 100)
    context = js[start:end]
    if '()=>' in context and 'agent' not in context.lower():
        print(f"\n{context}")
    idx = js.find('$r:', idx + 1)
    count += 1

# Find agent.v1 message definitions
print("\n\n=== Looking for agent.v1 messages ===")
patterns = [
    r'typeName="agent\.v1\.[^"]*Request[^"]*"',
    r'typeName="agent\.v1\.[^"]*Response[^"]*"',
]
for pat in patterns:
    for m in re.finditer(pat, js):
        start = max(0, m.start() - 300)
        end = min(len(js), m.end() + 1500)
        typename = m.group(0)
        if 'Run' in typename or 'Agent' in typename:
            print(f"\n--- {typename} ---")
            print(js[start:end][:2000])
