#!/usr/bin/env bash
set -euo pipefail

# Install uv (official installer)
echo "Installing uv (official installer)..."
curl -LsSf https://astral.sh/uv/install.sh | sh

echo "Installing zola"
export ZOLA_VER=v0.20.0
curl -sSfL https://github.com/getzola/zola/releases/download/$ZOLA_VER/zola-$ZOLA_VER-x86_64-unknown-linux-gnu.tar.gz | tar xz -C /usr/local/bin

export PATH="$HOME/.local/bin:$PATH"

echo "Installing Python dependencies with uv..."
uv pip install -e .

echo "Running make build with uv..."
uv run make build

echo "Starting Zola server on port 1111 in the background..."
uv run zola serve --port 1111 &
