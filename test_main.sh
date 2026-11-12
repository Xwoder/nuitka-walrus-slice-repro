#!/usr/bin/env bash
# Run main.py from source, build it with Nuitka, then run the binary.
# Safe to call from any directory (cd's to the directory holding this script).
# No `set -e`: the binary run is expected to exit 139 and must not abort us.
cd "$(dirname "$0")" || exit 1

# 1. Run from source (expected: exit=0, prints OK)
.venv/bin/python main.py; echo "exit=$?"

# 2. Compile (expected: the binary segfaults at iteration 17)
.venv/bin/python -m nuitka \
    --mode=standalone --lto=no --assume-yes-for-downloads \
    --output-dir=dist main.py

# 3. Run the binary (expected exit=139)
./dist/main.dist/main.bin; echo "exit=$?"
