"""DEC-054 persistent, exclusive per-run evidence store.  One directory per run_id (created with exist_ok=False); every file is opened in exclusive-create
mode ('x'/'xb'), so nothing can be overwritten.  Failed runs keep their evidence (error text, diagnostics, partial series if any).
Files: config.json, metrics.json, diag.json, status.json, ledger_row.json, series.npz (or series_missing.json), hashes.json (SHA-256 of every other file, written last)."""
from __future__ import annotations

import datetime as _dt
import json
import traceback
from pathlib import Path

import numpy as np

from dec054_common import sha_file


def to_jsonable(o):
    if isinstance(o, dict):
        return {str(k): to_jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return to_jsonable(o.tolist())
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))):
        return repr(o)
    if isinstance(o, Path):
        return str(o)
    return o


def _wjson(path: Path, obj):
    with open(path, "x", encoding="utf-8") as f:
        json.dump(to_jsonable(obj), f, indent=1)


def save_run(root, run_id: str, *, status: str, tds_id: str = "", series: dict | None = None, metrics: dict | None = None, config: dict | None = None,
             diag: dict | None = None, notes: str = "", error: BaseException | str | None = None, ledger_row: dict | None = None) -> dict:
    """Persist one run exclusively.  Raises FileExistsError if the run directory (or any file) already exists."""
    d = Path(root) / run_id
    d.mkdir(parents=True, exist_ok=False)
    err = None
    if isinstance(error, BaseException):
        err = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    elif error:
        err = str(error)
    if series:
        with open(d / "series.npz", "xb") as f:
            np.savez_compressed(f, **{k: np.asarray(v) for k, v in series.items()})
    else:
        _wjson(d / "series_missing.json", {"reason": "no series available (failed before data or not produced)", "status": status})
    _wjson(d / "config.json", config or {})
    _wjson(d / "metrics.json", metrics or {})
    _wjson(d / "diag.json", diag or {})
    _wjson(d / "ledger_row.json", ledger_row or {})
    _wjson(d / "status.json", {"run_id": run_id, "tds_id": tds_id, "status": status, "notes": notes, "error": err, "saved_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(), "has_series": bool(series)})
    hashes = {p.name: sha_file(p) for p in sorted(d.iterdir())}
    _wjson(d / "hashes.json", hashes)
    return hashes


def verify_run(root, run_id: str) -> dict:
    """Recompute every hash; returns {'ok': bool, 'mismatch': [...], 'missing': [...]}."""
    d = Path(root) / run_id
    rec = json.loads((d / "hashes.json").read_text(encoding="utf-8"))
    mismatch = [n for n, h in rec.items() if not (d / n).exists() or sha_file(d / n) != h]
    extra = [p.name for p in d.iterdir() if p.name not in rec and p.name != "hashes.json"]
    return {"ok": not mismatch and not extra, "mismatch": mismatch, "unlisted": extra}
