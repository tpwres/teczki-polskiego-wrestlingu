#!/usr/bin/env bash
set -euo pipefail
set -x

# Install uv (official installer)
echo "Installing uv (official installer)..."
curl -LsSf https://astral.sh/uv/install.sh | sh

echo "Installing zola"
export ZOLA_VER=v0.20.0
curl -sSfL https://github.com/getzola/zola/releases/download/$ZOLA_VER/zola-$ZOLA_VER-x86_64-unknown-linux-gnu.tar.gz | tar xz -C $HOME/.local/bin

export PATH="$HOME/.local/bin:$PATH"

echo "Creating venv"
uv venv

echo "Installing Python dependencies with uv..."
uv pip install -e .

echo "Running make all with uv..."
uv run make all

echo "Starting Zola server on port 1111 in the background..."
uv run zola serve --port 1111 &
