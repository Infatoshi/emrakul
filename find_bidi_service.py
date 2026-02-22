#!/usr/bin/env python3
"""Find BidiService and agent.v1 service details."""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Find BidiService methods
print("=== Looking for BidiService ===")
idx = js.find('BidiService')
count = 0
while idx > 0 and count < 5:
    start = max(0, idx - 100)
    end = min(len(js), idx + 1000)
    context = js[start:end]
    print(f"\n--- At {idx} ---")
    print(context[:1000])
    idx = js.find('BidiService', idx + 1)
    count += 1

# Find agent.v1.AgentService
print("\n\n=== Looking for AgentService methods ===")
idx = js.find('AgentService')
count = 0
while idx > 0 and count < 5:
    start = max(0, idx - 100)
    end = min(len(js), idx + 2000)
    context = js[start:end]
    if 'methods' in context or 'name:' in context:
        print(f"\n--- At {idx} ---")
        print(context[:2000])
    idx = js.find('AgentService', idx + 1)
    count += 1

# Look for ConversationService or ChatService
print("\n\n=== Looking for other chat-related services ===")
for service in ['ConversationService', 'ChatService', 'MessageService']:
    idx = js.find(service)
    if idx > 0:
        start = max(0, idx - 100)
        end = min(len(js), idx + 500)
        print(f"\n{service}: {js[start:end]}")
