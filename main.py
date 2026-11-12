"""Reproduction playground for a Nuitka heap corruption bug (develop branch,
reports itself as 4.4rc6, commit 7759b7c4).

The known trigger is a loop-carried offset used in a slice as a walrus
expression
    v = struct.unpack('<H', data[cur:(cur := cur + 2)])[0]
plus an `import numpy` in the module (no numpy API call needed) and a NON-ZERO
initial offset in cur (28 in the original layout): the compiled binary then
segfaults (exit=139) from 17 iterations on, while CPython runs the same source
normally.

Current revision: back to the walrus form (the walrus-free control experiment
was run and did not crash, as expected). cur = 1, 17 iterations -- every
non-zero initial offset crashes (1, 2, 27, 28 all verified), cur = 0 does NOT
crash (see README.md, Controls). ./build.sh runs the source, builds the
binary and runs it.
"""

import struct

import numpy as np  # noqa: F401  importing numpy is required for the repro (API not called)

ITERS = 17              # smallest crashing threshold measured (16 fine, 17 crashes)

# 259 bytes of arbitrary content (only the total length and the offsets matter)
data = bytes.fromhex(
    "02784f000ca5190058082400599e0f005a794f000ca4190058072400599e0f00"
    "5a7a4f000ca3190058062400599d0f005a7b4f000ca2190058052400599d0f00"
    "5a7c4f000ca2190058052400599d0f005a7d4f000ca2190058042400599d0f00"
    "5a7e4f000ca2190058042400599d0f005a7f4f000ca2190058042400599d0f00"
    "5a804f000ca1190058042400599d0f005a814f000ca1190058042400599c0f00"
    "5a824f000ca1190058042400599b0f005a834f000ca1190058032400599a0f00"
    "5a844f000ca119005802240059980f005a854f000ca119005801240059970f00"
    "5a864f000ca1190058ff230059960f005a874f000ca1190058fe230059950f00"
    "5a884f"
)
cur = 1                 # non-zero initial offset: required for the crash (cur = 0 does NOT crash)
for _i in range(ITERS):  # the loop itself is part of the trigger (no loop, no crash)
    # the walrus writes cur inside the slice (+2); +14 here -> 16 bytes per record
    v = struct.unpack('<H', data[cur:(cur := cur + 2)])[0]
    cur += 14

print(f"OK iters={ITERS} cur={cur} file={len(data)}")
