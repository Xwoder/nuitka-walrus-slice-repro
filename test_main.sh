#!/usr/bin/env bash
# Run main.py from source, build it with Nuitka, then run the binary -- each
# step with WALRUS=1 and WALRUS=0.
# Safe to call from any directory (cd's to the directory holding this script).
# No `set -e`: the WALRUS=1 runs are expected to exit 139 and must not abort us.
cd "$(dirname "$0")" || exit 1

# 1. Run from source (expected: exit=0 for both settings)
WALRUS=1 .venv/bin/python main.py; echo "exit=$?"
WALRUS=0 .venv/bin/python main.py; echo "exit=$?"

# 2. Compile (expected: the binary segfaults at iteration 17)
.venv/bin/python -m nuitka \
    --mode=standalone --lto=no --assume-yes-for-downloads \
    --output-dir=dist main.py

# 3. Run the binary (expected exit=139)
WALRUS=1 ./dist/main.dist/main.bin; echo "exit=$?"

# 4. Control switch (no walrus: the binary is fine, exit=0)
WALRUS=0 ./dist/main.dist/main.bin; echo "exit=$?"
