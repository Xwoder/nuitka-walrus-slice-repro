#!/usr/bin/env bash

cd "$(dirname "$0")" || exit 1

# Run original Python code
echo "=== Python source ==="
uv run python main.py

# Compile with Nuitka
echo "=== Nuitka compilation ==="
uv run python -m nuitka \
    --mode=standalone \
    --lto=no \
    --assume-yes-for-downloads \
    --output-dir=dist \
    main.py

# Run compiled executable
echo "=== Nuitka binary ==="
./dist/main.dist/main.bin
echo "Exit code: $?"