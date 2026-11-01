"""Verify archived source hashes only; never execute study entry points."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / "SOURCE-MANIFEST.json").read_text())
expected = set(manifest["files"])
actual = {str(p.relative_to(root)) for p in (root / "source").rglob("*") if p.is_file()}
assert actual == expected, "Source file inventory differs from manifest"
for relative, record in manifest["files"].items():
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == record["sha256"], relative
print(f"Verified {len(expected)} historical source files; no study code executed.")
