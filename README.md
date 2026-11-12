# Nuitka heap-corruption reproducer (walrus in a slice + `import numpy`)

Minimal, single-file reproducer for a heap corruption bug in binaries compiled
with **Nuitka 4.3.5**. `main.py` is self-contained (286 bytes of embedded data),
no external input files are needed.

Measured on 2026-11-12 with Python 3.13.18 (python-build-standalone), Nuitka
4.3.5 and numpy 2.5.4, compiled as
`--mode=standalone --lto=no --assume-yes-for-downloads`.

## Symptom

The compiled binary exits with a segfault (`exit=139`) after the loop, with no
output at all before the crash. CPython runs the very same source normally.

```
lldb: EXC_BAD_ACCESS (code=1, address=0x1)
      frame #0  libpython3.13.dylib  _PyObject_Malloc + 116   (ldr x10, [x0])
```

That is a downstream symptom of corrupted heap metadata, not a bad pointer
produced by the generated code. The binary is stripped, so no further frames
can be resolved.

## Trigger

All three ingredients are required:

1. a loop whose carried offset is used in a slice **as a walrus expression**:

   ```python
   v = struct.unpack('<H', data[cur:(cur := cur + 2)])[0]
   ```

2. an `import numpy` in the module -- calling any numpy API is **not** needed;
3. a **non-zero initial offset** in `cur` (28 here). With `cur = 0` the same
   code does not crash.

Boundary: 16 iterations are fine, 17 iterations deterministically crash
(bisected). `main.py` is pinned at 17.

## Controls

| Variant | Result |
|---|---|
| `WALRUS=0` (plain slice, two statements) | no crash |
| `import numpy` commented out | no crash |
| no loop (single direct unpack) | no crash |
| `records` counter removed | still crashes |
| first 28 bytes of data dropped, `cur = 0` | no crash |
| data unchanged, only `cur` changed from 28 to 0 | no crash |

The last two rows show that the *initial offset 28 itself* is part of the
trigger, not the "skip the header" semantics: data length and content are not
the key. Keep `cur = 28` and the full 286 bytes -- do not drop the header just
to "simplify" the file.

## How to run

```bash
./test_main.sh            # source run, build, then both WALRUS settings
```

Manual steps:

```bash
# 1. Run from source (expected: fine, prints OK)
WALRUS=1 .venv/bin/python main.py
WALRUS=0 .venv/bin/python main.py

# 2. Compile with Nuitka (the binary segfaults at iteration 17; needs a C
#    compiler, takes about a minute)
.venv/bin/python -m nuitka \
    --mode=standalone --lto=no --assume-yes-for-downloads \
    --output-dir=dist main.py

# 3. Run the binary (expected exit=139)
WALRUS=1 ./dist/main.dist/main.bin; echo "exit=$?"

# 4. Control switch (no walrus: the binary is fine, exit=0)
WALRUS=0 ./dist/main.dist/main.bin; echo "exit=$?"
```

## Measured results

| Case | exit code |
|---|---|
| source, `WALRUS=1` and `WALRUS=0` | 0 (prints `OK walrus=... iters=17 cur=380 file=286`) |
| binary, `WALRUS=1`, `ITERS=17` | 139 (segfault, 5/5 deterministic, no output) |
| binary, `WALRUS=1`, `ITERS=16` | 0 (5/5, verified with a separate copy) |
| binary, `WALRUS=0` | 0 (5/5, prints `OK walrus=False iters=17 cur=380 file=286`) |
| binary, `WALRUS=1`, no `import numpy` | 0 (5/5) |
| binary, `WALRUS=1`, no `records` counter | 139 (5/5) |
| binary, `WALRUS=1`, first 28 bytes dropped + `cur = 0` | 0 (5/5) |

Side notes from an earlier repository, not re-verified here: compiling the
walrus variant without the loop (a single direct unpack) does not crash, i.e.
the loop structure participates in the trigger.

Re-tested with the Nuitka `develop` branch (4.4rc6, commit 7759b7c4, fetched
2026-11-12): still crashes -- `WALRUS=1` exit=139 5/5, `WALRUS=0` exit=0 3/3.
Not fixed as of that revision.

## Notes

- After changing the source you must recompile before testing; running an old
  `dist/` binary only reflects the old code.
- The probe reads `<H` little-endian values; `cur += 14` (walrus branch) and
  `cur += 16` (control branch) both advance the offset by 16 bytes per record,
  so both variants read the same bytes and print the same `cur=380`.
