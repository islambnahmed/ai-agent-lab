"""Probe whether encode/decode transformations preserve canonical content."""
from __future__ import annotations
import json
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path

_fp_path=Path(__file__).with_name("artifact_fingerprint.py")
_s=spec_from_file_location("_fp",_fp_path);_fp=module_from_spec(_s);_s.loader.exec_module(_fp)

def run(value, encode, decode):
    before=_fp.run(value)["sha256"]
    encoded=encode(value)
    restored=decode(encoded)
    after=_fp.run(restored)["sha256"]
    return {"preserved":before==after,"before":before,"after":after,"restored":restored}
