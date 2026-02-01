#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "  Emrakul Installation"
echo "======================================"
echo ""

# Check for required CLIs
echo "Checking prerequisites..."
echo ""

MISSING=()

check_cli() {
    if command -v "$1" &> /dev/null; then
        echo -e "  ${GREEN}[OK]${NC} $1"
        return 0
    else
        echo -e "  ${RED}[MISSING]${NC} $1"
        MISSING+=("$1")
        return 1
    fi
}

check_cli "claude"
check_cli "cursor"
check_cli "codex"
check_cli "kimi"
check_cli "opencode"
check_cli "uv"
check_cli "jq"

echo ""

if [ ${#MISSING[@]} -gt 0 ]; then
    echo -e "${YELLOW}Missing CLIs: ${MISSING[*]}${NC}"
    echo ""
    echo "Install instructions:"
    for cli in "${MISSING[@]}"; do
        case $cli in
            claude)
                echo "  claude:    npm install -g @anthropic-ai/claude-code"
                ;;
            cursor)
                echo "  cursor:    Download from https://cursor.com/downloads"
                ;;
            codex)
                echo "  codex:     npm install -g @openai/codex"
                ;;
            kimi)
                echo "  kimi:      pip install kimi-cli"
                ;;
            opencode)
                echo "  opencode:  pip install opencode"
                ;;
            uv)
                echo "  uv:        curl -LsSf https://astral.sh/uv/install.sh | sh"
                ;;
            jq)
                echo "  jq:        brew install jq (macOS) or apt install jq (Linux)"
                ;;
        esac
    done
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check authentication status
echo "Checking authentication..."
echo ""
echo "  Make sure you have authenticated each CLI:"
echo "    claude login"
echo "    cursor login"
echo "    codex auth"
echo "    kimi auth"
echo "    opencode auth"
echo ""

# Install as UV tool (globally available)
echo "Installing Emrakul as UV tool..."
uv tool install git+https://github.com/Infatoshi/emrakul.git --force
echo ""

# Create directories
echo "Creating config directories..."
mkdir -p ~/.claude/hooks
mkdir -p ~/.codex
mkdir -p ~/.cursor/rules
mkdir -p ~/.emrakul/outputs
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Backup existing configs
backup_if_exists() {
    if [ -f "$1" ]; then
        echo "  Backing up $1 to $1.backup"
        cp "$1" "$1.backup"
    fi
}

echo "Backing up existing configs..."
backup_if_exists ~/.claude/CLAUDE.md
backup_if_exists ~/.codex/AGENTS.md
echo ""

# Copy config files
echo "Installing config files..."

# Claude config
cp "$SCRIPT_DIR/config/claude/CLAUDE.md" ~/.claude/CLAUDE.md
echo "  Installed ~/.claude/CLAUDE.md"

# Hook to block Task tool
cp "$SCRIPT_DIR/config/hooks/block-task-tool.sh" ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-task-tool.sh
echo "  Installed ~/.claude/hooks/block-task-tool.sh"

# Codex config
cp "$SCRIPT_DIR/config/codex/AGENTS.md" ~/.codex/AGENTS.md
echo "  Installed ~/.codex/AGENTS.md"

# Cursor config
cp "$SCRIPT_DIR/config/cursor/emrakul.mdc" ~/.cursor/rules/emrakul.mdc
echo "  Installed ~/.cursor/rules/emrakul.mdc"

echo ""

# Configure hooks in Claude settings
echo "Configuring Task-blocking hook..."
SETTINGS_FILE=~/.claude/settings.json

if [ -f "$SETTINGS_FILE" ]; then
    TMP_FILE=$(mktemp)
    jq '.hooks.PreToolUse = [{"matcher": "Task", "hooks": [{"type": "command", "command": "~/.claude/hooks/block-task-tool.sh"}]}]' "$SETTINGS_FILE" > "$TMP_FILE" && mv "$TMP_FILE" "$SETTINGS_FILE"
    echo "  Added Task-blocking hook to settings.json"
else
    # Create settings.json with hooks
    cat > "$SETTINGS_FILE" << 'EOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-task-tool.sh"
          }
        ]
      }
    ]
  }
}
EOF
    echo "  Created settings.json with Task-blocking hook"
fi

echo ""
echo "======================================"
echo -e "  ${GREEN}Installation complete!${NC}"
echo "======================================"
echo ""
echo "Usage:"
echo "  emrakul delegate cursor 'Implement feature X'"
echo "  emrakul delegate codex 'Write tests for Y'"
echo "  emrakul delegate kimi 'Research topic Z'"
echo "  emrakul delegate opencode 'Quick fix'"
echo ""
echo "Parallel execution:"
echo "  emrakul delegate kimi 'task 1' --bg &"
echo "  emrakul delegate kimi 'task 2' --bg &"
echo "  emrakul status all"
echo ""
echo "Restart Claude Code to pick up the new config."
echo ""
