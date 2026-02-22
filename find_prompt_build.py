#!/usr/bin/env python3
"""Find where the system prompt is actually constructed."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Look for the actual prompt text or template
print("=== Looking for prompt text/template ===")
patterns = [
    r'You are a[^"]{0,200}',
    r'"You are[^"]{0,200}',
    r'assistant[^"]*tool[^"]{0,200}',
    r'IMPORTANT.*tool[^"]{0,200}',
]

for pat in patterns:
    matches = list(re.finditer(pat, js, re.IGNORECASE))
    if matches:
        print(f"\n--- Pattern: {pat[:40]}... ({len(matches)} matches) ---")
        for m in matches[:5]:
            start = max(0, m.start() - 50)
            end = min(len(js), m.end() + 100)
            print(f"  ...{js[start:end]}...\n")

# Look for where buildPrompt or getPrompt functions are
print("\n\n=== Looking for prompt building functions ===")
patterns = [
    r'buildSystemPrompt[^}]{0,500}',
    r'getSystemPrompt[^}]{0,500}',
    r'formatPrompt[^}]{0,500}',
    r'buildRootPrompt[^}]{0,500}',
]

for pat in patterns:
    matches = list(re.finditer(pat, js, re.IGNORECASE))
    if matches:
        print(f"\n--- Pattern: {pat[:40]}... ({len(matches)} matches) ---")
        for m in matches[:2]:
            start = max(0, m.start() - 100)
            end = min(len(js), m.end() + 200)
            print(f"  ...{js[start:end]}...\n")

# Look for where JSON messages are constructed
print("\n\n=== Looking for role:system message construction ===")
patterns = [
    r'"role"\s*:\s*"system"[^}]{0,300}',
    r'role:\s*["\']system["\'][^}]{0,300}',
]

for pat in patterns:
    matches = list(re.finditer(pat, js))
    if matches:
        print(f"\n--- Pattern: {pat[:40]}... ({len(matches)} matches) ---")
        for m in matches[:3]:
            start = max(0, m.start() - 100)
            end = min(len(js), m.end() + 100)
            print(f"  ...{js[start:end]}...\n")
