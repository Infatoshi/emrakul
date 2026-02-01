#!/bin/bash
# Block Claude's native Task tool to prevent quota burn
# Redirect to Emrakul MCP tools instead

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')

if [ "$TOOL_NAME" = "Task" ]; then
  cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "BLOCKED: Task tool burns 20x quota. Use Emrakul MCP instead: delegate_cursor (implementation), delegate_codex (tests/debug), delegate_kimi (research), delegate_opencode (quick edits), or swarm_* for batch work."
  }
}
EOF
  exit 0
fi

# Allow all other tools
exit 0
