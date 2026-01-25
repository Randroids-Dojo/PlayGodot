#!/bin/bash
# Claude Code start hook for PlayGodot

# Ensure we're in the right directory
cd "$(dirname "$0")/../.." || exit 0

# Check if there are uncommitted changes in pyproject.toml
if git diff --name-only | grep -q "python/pyproject.toml"; then
    echo "Note: python/pyproject.toml has uncommitted changes"
fi

# Show current version
if [ -f "python/pyproject.toml" ]; then
    VERSION=$(grep '^version = ' python/pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
    echo "PlayGodot version: $VERSION"
fi
