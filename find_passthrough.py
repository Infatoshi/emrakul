#!/usr/bin/env python3
"""Find passthrough or raw API endpoints."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Look for passthrough-related endpoints
print("=== Passthrough/Raw endpoints ===")
patterns = [
    r'getPassthroughPrompt[^}]{0,300}',
    r'Passthrough[^}]{0,200}',
    r'rawCompletion[^}]{0,200}',
    r'directApi[^}]{0,200}',
]
for pat in patterns:
    matches = list(re.finditer(pat, js, re.IGNORECASE))
    if matches:
        print(f"\n--- {pat} ({len(matches)} matches) ---")
        for m in matches[:3]:
            start = max(0, m.start() - 100)
            end = min(len(js), m.end() + 100)
            print(f"{js[start:end]}\n")

# Look for API key passthrough (using your own API key)
print("\n\n=== API Key/Credentials passthrough ===")
patterns = [
    r'apiKeyCredentials[^}]{0,300}',
    r'api_key_credentials[^}]{0,300}',
    r'ownApiKey[^}]{0,200}',
]
for pat in patterns:
    matches = list(re.finditer(pat, js, re.IGNORECASE))
    if matches:
        print(f"\n--- {pat} ({len(matches)} matches) ---")
        for m in matches[:2]:
            start = max(0, m.start() - 100)
            end = min(len(js), m.end() + 100)
            print(f"{js[start:end]}\n")
