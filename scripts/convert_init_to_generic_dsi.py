#!/usr/bin/env python3
"""Convert the BSP-style init blob in panel-e5p.c into rocknix,generic-dsi
panel_description "I" lines.

Blob format per command: {datatype, wait_ms(hex), payload_len, payload...}
generic-dsi format: "I seq=<payload hex>[ wait=<hex ms>]"
(the driver sends seq= items via mipi_dsi_dcs_write_buffer, which picks
DCS short/long write by length — same behaviour as panel-e5p.c's send loop;
wait= is parsed base-16 by simple_strtoul(..., 16)).
"""
import re
import sys

src = open(sys.argv[1] if len(sys.argv) > 1 else "kernel/panel-e5p.c").read()

m = re.search(r"e5p_init_seq\[\]\s*=\s*\{(.*?)\n\};", src, re.S)
if not m:
    sys.exit("e5p_init_seq[] not found")

body = m.group(1)
# strip comments
body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
body = re.sub(r"//[^\n]*", "", body)
vals = [int(t, 16) for t in re.findall(r"0x([0-9a-fA-F]{2})", body)]

lines, i, n = [], 0, 0
while i < len(vals):
    dtype, wait, dlen = vals[i], vals[i + 1], vals[i + 2]
    payload = vals[i + 3 : i + 3 + dlen]
    assert len(payload) == dlen, f"truncated cmd at index {i}"
    seq = "".join(f"{b:02x}" for b in payload)
    line = f"I seq={seq}"
    if wait:
        line += f" wait={wait:x}"   # generic-dsi parses wait as hex
    lines.append(line)
    i += 3 + dlen
    n += 1

print(f"/* {n} init commands converted from panel-e5p.c e5p_init_seq[] */",
      file=sys.stderr)
out = ",\n".join(f'\t\t\t"{l}"' for l in lines)
print(out)
