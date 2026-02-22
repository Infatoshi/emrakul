#!/usr/bin/env python3
"""Debug proto extraction."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find StreamChatToolformerResponse - we saw its fields clearly
type_name = "aiserver.v1.StreamChatToolformerResponse"
pattern = f'typeName="{type_name}"'
match = re.search(pattern, js)

if match:
    pos = match.start()
    # Get 2000 chars after typeName
    after = js[pos:pos+2000]
    print("Context after typeName:")
    print(after[:1000])
    print("\n\n=== Looking for newFieldList ===")

    # Find newFieldList
    fl_match = re.search(r'newFieldList\(\(\)=>\[', after)
    if fl_match:
        print(f"Found at position: {fl_match.start()}")
        print(f"Content starting there: {after[fl_match.start():fl_match.start()+500]}")

        # Extract the array content
        start = fl_match.end()
        print(f"\nArray content starts at: {start}")
        print(f"Content: {after[start:start+400]}")
