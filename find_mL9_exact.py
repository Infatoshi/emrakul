#!/usr/bin/env python3
"""Find the exact mL9 message definition by searching the export location."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# The 's' module exports mL9. Let's find where it's defined.
# In webpack bundles, exports are typically done like: t.mL9 = class ...

print("=== Looking for mL9 class assignment ===")
# Find the chunk where mL9 is defined
# Pattern: something.mL9 = or mL9: class

patterns = [
    r'\bmL9\s*=\s*class\s+\w*\s+extends\s+\w+',
    r'\.mL9\s*=\s*class\s+\w*\s+extends\s+\w+',
    r't\.mL9\s*=\s*\w+',
    r'exports\.mL9\s*=',
    r'n\.d\([^)]+mL9',
]

for pat in patterns:
    matches = list(re.finditer(pat, js))
    if matches:
        print(f"\n--- Pattern: {pat} ({len(matches)} matches) ---")
        for m in matches[:2]:
            start = max(0, m.start() - 100)
            end = min(len(js), m.end() + 1500)
            print(f"{js[start:end][:2000]}\n{'='*60}")

# Alternative: find where the module with mL9 is defined
print("\n\n=== Looking for module chunk with mL9 ===")
# Find context where mL9 appears in an export mapping
idx = js.find('mL9:')
count = 0
while idx > 0 and count < 3:
    start = max(0, idx - 200)
    end = min(len(js), idx + 500)
    print(f"\n--- At {idx} ---")
    print(js[start:end])
    idx = js.find('mL9:', idx + 1)
    count += 1
