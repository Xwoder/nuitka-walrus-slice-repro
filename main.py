"""Minimal reproducer for a Nuitka 4.3.5 heap corruption bug (self-contained).

Inside a loop the loop-carried offset is used in a slice as a walrus expression
    v = struct.unpack('<H', data[cur:(cur := cur + 2)])[0]
together with an `import numpy` in the module (no numpy API needs to be called)
and a non-zero initial offset in cur: the compiled binary segfaults (exit=139)
from 17 iterations on, while CPython runs the very same source normally.

WALRUS=0 in the environment switches to the control variant without the walrus
(no crash). See README.md for the full trigger analysis and measured results;
./test_main.sh runs the source, builds the binary and runs both settings.
"""

import os
import struct

import numpy  # noqa: F401  importing numpy is required for the repro (API not called)

WALRUS = os.environ.get("WALRUS", "1") == "1"
ITERS = 17              # smallest crashing threshold measured (16 fine, 17 crashes)

# 286 bytes of arbitrary content (only the total length and the offsets matter)
data = bytes.fromhex(
    "4853e40246520c00010801170f3b3b00240000000d0a0d0a464d8002784f000c"
    "a5190058082400599e0f005a794f000ca4190058072400599e0f005a7a4f000c"
    "a3190058062400599d0f005a7b4f000ca2190058052400599d0f005a7c4f000c"
    "a2190058052400599d0f005a7d4f000ca2190058042400599d0f005a7e4f000c"
    "a2190058042400599d0f005a7f4f000ca2190058042400599d0f005a804f000c"
    "a1190058042400599d0f005a814f000ca1190058042400599c0f005a824f000c"
    "a1190058042400599b0f005a834f000ca1190058032400599a0f005a844f000c"
    "a119005802240059980f005a854f000ca119005801240059970f005a864f000c"
    "a1190058ff230059960f005a874f000ca1190058fe230059950f005a884f"
)
cur = 28                # non-zero initial offset (28 bytes skipped); 0 would not crash -- part of the trigger
for _i in range(ITERS):  # the loop itself is part of the trigger (no loop, no crash)
    if WALRUS:
        v = struct.unpack('<H', data[cur:(cur := cur + 2)])[0]
        cur += 14
    else:
        v = struct.unpack('<H', data[cur:cur + 2])[0]
        cur += 16
cur += 80               # trailing bytes, never read (kept so the end offset matches the original layout)

print(f"OK walrus={WALRUS} iters={ITERS} cur={cur} file={len(data)}")
