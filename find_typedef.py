#!/usr/bin/env python3
"""Find where module 's' exports mL9."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find all occurrences of s.mL9 with context
print("=== Context around s.mL9 references ===")
pattern = r'.{200}s\.mL9.{200}'
for m in re.finditer(pattern, js):
    print(f"\n{m.group(0)}\n{'='*60}")

# The module 's' is likely defined/imported somewhere
# Look for import patterns
print("\n\n=== Looking for 's' module definition ===")

# Find where 's' is assigned from an import
# Patterns like: var s=require(...) or s=n(...) or import * as s
s_pattern = r'[,;]s=\w+\([^\)]+\)'
for m in re.finditer(s_pattern, js[:100000]):
    print(f"Found: {m.group(0)}")

# Search for CheckLongFilesFit which also uses s.mL9 as input
print("\n\n=== CheckLongFilesFit context ===")
idx = js.find('CheckLongFilesFit')
if idx > 0:
    start = max(0, idx - 500)
    end = min(len(js), idx + 200)
    print(js[start:end])
