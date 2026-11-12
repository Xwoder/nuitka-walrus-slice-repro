"""Reproduction playground for a Nuitka 4.3.5 heap corruption bug.

The known trigger is a loop-carried offset used in a slice as a walrus
expression
    v = struct.unpack('<H', data[cur:(cur := cur + 2)])[0]
plus an `import numpy` in the module (no numpy API call needed) and a NON-ZERO
initial offset in cur (28 in the original layout): the compiled binary then
segfaults (exit=139) from 17 iterations on, while CPython runs the same source
normally.

Current revision: the first data byte has been dropped and cur = 27, so the
loop reads the very same bytes as the crashing version at a shifted offset.
Whether any non-zero initial offset (not just 28) triggers the crash is what
this revision tests. ./test_main.sh runs the source, builds and runs it.
"""

import struct

import numpy as np  # noqa: F401  importing numpy is required for the repro (API not called)

ITERS = 17              # smallest crashing threshold measured (16 fine, 17 crashes)

# 285 bytes of arbitrary content (original 286 minus the first byte; only the
# total length and the offsets matter)
data = bytes.fromhex(
    "53e40246520c00010801170f3b3b00240000000d0a0d0a464d8002784f000ca5"
    "190058082400599e0f005a794f000ca4190058072400599e0f005a7a4f000ca3"
    "190058062400599d0f005a7b4f000ca2190058052400599d0f005a7c4f000ca2"
    "190058052400599d0f005a7d4f000ca2190058042400599d0f005a7e4f000ca2"
    "190058042400599d0f005a7f4f000ca2190058042400599d0f005a804f000ca1"
    "190058042400599d0f005a814f000ca1190058042400599c0f005a824f000ca1"
    "190058042400599b0f005a834f000ca1190058032400599a0f005a844f000ca1"
    "19005802240059980f005a854f000ca119005801240059970f005a864f000ca1"
    "190058ff230059960f005a874f000ca1190058fe230059950f005a884f"
)
cur = 27                # first data byte dropped, offset decremented to match; still non-zero (tests whether ANY non-zero value triggers)
for _i in range(ITERS):  # the loop itself is part of the trigger (no loop, no crash)
    # the walrus writes cur inside the slice (+2); +14 here -> 16 bytes per record
    v = struct.unpack('<H', data[cur:(cur := cur + 2)])[0]
    cur += 14

print(f"OK iters={ITERS} cur={cur} file={len(data)}")
