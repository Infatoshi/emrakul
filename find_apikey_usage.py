#!/usr/bin/env python3
"""Find how ApiKeyCredentials is used - could bypass system prompt injection."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find RequestedModel structure with credentials
print("=== RequestedModel with credentials ===")
patterns = [
    r'RequestedModel[^}]{0,1000}credentials',
    r'typeName="agent\.v1\.RequestedModel"[^}]*fields[^]]+\]',
]
for pat in patterns:
    matches = list(re.finditer(pat, js))
    if matches:
        print(f"\n--- {pat[:50]}... ---")
        for m in matches[:2]:
            start = max(0, m.start() - 50)
            end = min(len(js), m.end() + 100)
            print(f"{js[start:end]}\n")

# Find where credentials are used in requests
print("\n\n=== Credentials usage in requests ===")
patterns = [
    r'credentials\s*:\s*\{[^}]{0,300}api_key',
    r'apiKeyCredentials\s*[:=][^;,]{0,200}',
]
for pat in patterns:
    matches = list(re.finditer(pat, js, re.IGNORECASE))
    if matches:
        print(f"\n--- {pat[:50]}... ({len(matches)} matches) ---")
        for m in matches[:3]:
            start = max(0, m.start() - 100)
            end = min(len(js), m.end() + 100)
            print(f"{js[start:end]}\n")

# Check if base_url is used for passthrough
print("\n\n=== base_url passthrough ===")
patterns = [
    r'base_url[^}]{0,200}',
    r'baseUrl[^}]{0,200}anthropic',
]
for pat in patterns:
    matches = list(re.finditer(pat, js, re.IGNORECASE))
    if matches:
        print(f"\n--- {pat[:40]}... ({len(matches)} matches) ---")
        for m in matches[:3]:
            start = max(0, m.start() - 50)
            end = min(len(js), m.end() + 50)
            text = js[start:end]
            if 'api' in text.lower() or 'credential' in text.lower():
                print(f"{text}\n")
