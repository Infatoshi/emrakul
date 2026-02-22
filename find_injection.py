#!/usr/bin/env python3
"""
Trace the exact injection flow.

Based on analysis:
1. cursor-agent sends AgentRunRequest to server
2. AgentRunRequest has:
   - conversationState.rootPromptMessagesJson (user's messages)
   - customSystemPrompt (user's rules from CLAUDE.md/.cursorrules)
3. Server adds the base system prompt with tools

So injection is SERVER-SIDE. The tools and main system prompt live on Cursor's servers,
not in the cursor-agent bundle.
"""

import re
from pathlib import Path

js = Path("/tmp/cursor-index.js").read_text()

# Look for any embedded prompt templates
print("=== Checking for embedded prompt templates ===")

# Tool definitions might be in the bundle
tool_patterns = [
    r'"Shell"[^}]{0,500}',
    r'"Glob"[^}]{0,500}',
    r'tools\s*:\s*\[[^\]]{0,2000}\]',
]

for pat in tool_patterns:
    matches = list(re.finditer(pat, js))
    if matches:
        print(f"\n--- Pattern: {pat[:30]}... ({len(matches)} matches) ---")
        for m in matches[:2]:
            start = max(0, m.start() - 50)
            end = min(len(js), m.end() + 50)
            text = js[start:end]
            # Filter out noise (like "ShellStream")
            if 'function' not in text.lower() and 'description' in text.lower():
                print(f"\n{text}\n")

# Look for where tools are defined for sending to server
print("\n\n=== Tool definitions sent to server ===")
patterns = [
    r'supportedTools[^}]{0,500}',
    r'mcpTools[^}]{0,300}',
]
for pat in patterns:
    matches = list(re.finditer(pat, js))
    if matches:
        print(f"\n--- Pattern: {pat} ({len(matches)} matches) ---")
        for m in matches[:3]:
            start = max(0, m.start() - 100)
            end = min(len(js), m.end() + 100)
            print(f"\n{js[start:end]}\n")

# Summary
print("\n" + "="*60)
print("CONCLUSION: The system prompt is SERVER-SIDE injected.")
print("="*60)
print("""
cursor-agent sends to server:
- conversationState (with user messages)
- customSystemPrompt (user's CLAUDE.md/.cursorrules content)
- modelDetails (model selection)
- supportedTools (which tools client supports)

The server then:
1. Takes the base Cursor system prompt (with tool definitions, formatting rules)
2. Merges in user's customSystemPrompt
3. Adds the conversation messages
4. Sends to the LLM

This is why we can't simply "bypass" the system prompt - it's added server-side.
The only way to use a custom system prompt would be if the API supported it
via the customSystemPrompt field, but it appears this is ADDED to the base
prompt, not REPLACING it.
""")
