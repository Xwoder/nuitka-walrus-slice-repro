#!/usr/bin/env bash

cd "$(dirname "$0")" || exit 1

# 1. Run from source
.venv/bin/python main.py
echo "Source exit=$?"

# 2. Compile with Nuitka debug mode
.venv/bin/python -m nuitka \
    --mode=standalone \
    --lto=no \
    --assume-yes-for-downloads \
    --output-dir=dist-debug \
    main.py

echo "Compile exit=$?"

# 3. Run compiled binary
./dist-debug/main.dist/main.bin
echo "Binary exit=$?"