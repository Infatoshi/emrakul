#!/usr/bin/env python3
"""Find all available endpoints in Cursor bundle."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find all service methods
print("=== aiserver.v1.AiService methods ===")

# Look for method definitions
method_pattern = r'name:"(\w+)",I:[^,]+,O:[^,]+,kind:i\.I\.(\w+)'
for m in re.finditer(method_pattern, js):
    method_name = m.group(1)
    method_type = m.group(2)
    if 'Chat' in method_name or 'Stream' in method_name:
        print(f"  {method_name} ({method_type})")

# Look for BidiService
print("\n\n=== aiserver.v1.BidiService methods ===")
idx = js.find('typeName="aiserver.v1.BidiService"')
if idx > 0:
    start = max(0, idx - 200)
    end = min(len(js), idx + 2000)
    print(js[start:end])

# Look for agent.v1 service
print("\n\n=== agent.v1.AgentService methods ===")
idx = js.find('typeName="agent.v1.AgentService"')
if idx > 0:
    start = max(0, idx - 200)
    end = min(len(js), idx + 2000)
    print(js[start:end])
