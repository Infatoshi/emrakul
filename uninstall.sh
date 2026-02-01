#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "  Emrakul Uninstallation"
echo "======================================"
echo ""

# Remove UV tool
echo "Removing Emrakul UV tool..."
uv tool uninstall emrakul 2>/dev/null || true
echo ""

# Remove config files
echo "Removing config files..."

remove_file() {
    if [ -f "$1" ]; then
        rm "$1"
        echo "  Removed $1"
    fi
}

remove_file ~/.claude/hooks/block-task-tool.sh
remove_file ~/.cursor/rules/emrakul.mdc

# Restore backups if they exist
restore_backup() {
    if [ -f "$1.backup" ]; then
        mv "$1.backup" "$1"
        echo "  Restored $1 from backup"
    else
        remove_file "$1"
    fi
}

restore_backup ~/.claude/CLAUDE.md
restore_backup ~/.codex/AGENTS.md

echo ""

# Remove MCP server from claude.json
echo "Removing MCP server config..."
if [ -f ~/.claude.json ]; then
    TMP_FILE=$(mktemp)
    jq 'del(.mcpServers.emrakul)' ~/.claude.json > "$TMP_FILE" && mv "$TMP_FILE" ~/.claude.json
    echo "  Removed Emrakul from ~/.claude.json"
fi

# Remove hook from settings.json
echo "Removing hooks..."
if [ -f ~/.claude/settings.json ]; then
    TMP_FILE=$(mktemp)
    jq 'del(.hooks.PreToolUse[] | select(.matcher == "Task"))' ~/.claude/settings.json > "$TMP_FILE" && mv "$TMP_FILE" ~/.claude/settings.json
    echo "  Removed Task-blocking hook"
fi

echo ""
echo "======================================"
echo -e "  ${GREEN}Uninstallation complete!${NC}"
echo "======================================"
echo ""
echo "Restart Claude Code to apply changes."
echo "The native Task tool is now unblocked."
echo ""
