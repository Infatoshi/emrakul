#!/usr/bin/env python3
"""Find the u.hS class definition (conversation message type)."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find export mapping for hS
print("=== Looking for hS export mapping ===")
idx = js.find('hS:')
count = 0
while idx > 0 and count < 5:
    start = max(0, idx - 200)
    end = min(len(js), idx + 50)
    context = js[start:end]
    if '()=>' in context:
        print(f"\n--- At {idx} ---")
        print(context)
    idx = js.find('hS:', idx + 1)
    count += 1

# Find class hS definition
print("\n\n=== Looking for hS class definition ===")
idx = js.find('class hS ')
if idx > 0:
    end = min(len(js), idx + 3000)
    print(js[idx:end])
