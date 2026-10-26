"""Plant variant selector for the E5--E7 runners (environment variable ``C2_VARIANT``).

``C2``  : frozen C2 case with ANDES default REGF1 parameters (default).
``C2t`` : C2 with REGF1 KPv x1.5 (DEC-027), a separate case file; C2 is never modified.
"""

import os

VARIANT = os.environ.get("C2_VARIANT", "C2")
_CASES = {"C2": "ieee39_C2_6SG_4GFM.xlsx", "C2t": "ieee39_C2t_6SG_4GFM_KPv1p5.xlsx"}
if VARIANT not in _CASES:
    raise SystemExit(f"Unknown C2_VARIANT {VARIANT!r}; use one of {sorted(_CASES)}.")
CASE_FILE = _CASES[VARIANT]
SUFFIX = "" if VARIANT == "C2" else "t"
CASE_LABEL = "C2_6SG_4GFM" if VARIANT == "C2" else "C2t_6SG_4GFM_KPv1p5"
