"""DEC-052 shared helpers (post-processing / static evaluation only; no time-domain simulation).  Reuses the DEC-051 reduced model without modifying it."""
from __future__ import annotations

import hashlib
import json
import platform
import sys

import numpy as np
import scipy

import run_dec051_h4 as H4
import dec051_core as C
import run_dec051_equilibrium as EQ
from run_e0_ieee39 import ARTIFACTS_DIR as A, git_commit

EPS = np.finfo(float).eps / 2            # unit roundoff u = 2^-53


def sha(path) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def env() -> dict:
    import andes
    return {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__, "andes": andes.__version__, "platform": platform.platform(), "float": "IEEE-754 binary64, round-to-nearest (no directed rounding)"}


def gamma(n: int) -> float:
    return n * EPS / (1 - n * EPS)


def dump(name: str, obj: dict) -> None:
    (A / name).write_text(json.dumps(obj, indent=2, default=float), encoding="utf-8")
