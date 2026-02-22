#!/usr/bin/env python3
"""Find how cursor-agent creates API connections."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find where HTTP2 or streaming connections are made
print("=== Connection creation patterns ===")
patterns = [
    r'createClient\s*\(',
    r'connect\s*\([^)]*cursor',
    r'http2\.connect',
    r'transport[^}]*proto',
    r'createGrpcWebTransport',
    r'createConnectTransport',
]

for pat in patterns:
    matches = list(re.finditer(pat, js, re.IGNORECASE))
    if matches:
        print(f"\n--- Pattern: {pat} ({len(matches)} matches) ---")
        for m in matches[:2]:
            start = max(0, m.start() - 200)
            end = min(len(js), m.end() + 400)
            print(f"{js[start:end]}\n{'='*60}")

# Find the main API client creation
print("\n\n=== Looking for AiService client creation ===")
idx = js.find('AiService')
count = 0
while idx > 0 and count < 5:
    start = max(0, idx - 300)
    end = min(len(js), idx + 300)
    context = js[start:end]
    if 'create' in context.lower() or 'Client' in context:
        print(f"\n--- At {idx} ---")
        print(context)
    idx = js.find('AiService', idx + 1)
    count += 1

# Find stream handling
print("\n\n=== Stream handling ===")
for pat in ['serverStream', 'bidiStream', 'clientStream']:
    matches = list(re.finditer(pat, js, re.IGNORECASE))
    if matches:
        print(f"\nFound {len(matches)} references to {pat}")
        for m in matches[:1]:
            start = max(0, m.start() - 100)
            end = min(len(js), m.end() + 200)
            print(f"{js[start:end]}")
