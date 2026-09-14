#!/usr/bin/env python3
from pathlib import Path
import hashlib

parts = sorted(Path('.').glob('actors.viv.part*'))
out = Path('actors.viv')
with out.open('wb') as w:
    for part in parts:
        w.write(part.read_bytes())

sha = hashlib.sha256(out.read_bytes()).hexdigest()
expected = "04dabd8aca4113cd1489097a9deaf8deb9ae30468246487e5745df6a00f92803"
print(f"Wrote {out} ({out.stat().st_size} bytes)")
print(f"SHA-256: {sha}")
if sha != expected:
    raise SystemExit("ERROR: reconstructed file hash does not match original")
print("Verified: reconstructed file is byte-identical to the original.")
