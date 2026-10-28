"""DEC-054 pooled plant: the same interface as AndesPlant/SyntheticPlant, with caching of every evaluation and parallel (multi-process) computation of the
event responses (algebraic jump + post-event predictor excursion), one ANDES instance per worker.  Used by the OPF (G4).  The gate is checked in every worker."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool

import numpy as np

import dec054_opf as OPF
import dec054_plant as PL

_W = None


def _init_worker():
    global _W
    _W = PL.AndesPlant()


def _task(args):
    z, sc, need_exc = args
    scn = OPF.Scenario("w", *sc)
    try:
        j = _W.jump(np.asarray(z, float), scn)
        if not j["ok"]:
            return {"jump": {"ok": False, "reason": j.get("reason")}, "exc": {"ok": False}}
        if not need_exc:
            return {"jump": {"ok": True, "dP": j["dP"], "dQ": j["dQ"]}, "exc": None}
        x = _W.excursion(np.asarray(z, float), scn)
        return {"jump": {"ok": True, "dP": j["dP"], "dQ": j["dQ"]}, "exc": {k: x.get(k) for k in ("ok", "E_up", "E_dn", "t_up", "sampling_error")}}
    except Exception as ex:                       # never silently turned into feasibility
        return {"jump": {"ok": False, "reason": repr(ex)}, "exc": {"ok": False, "reason": repr(ex)}}


def _key(z):
    return tuple(np.round(np.asarray(z, float), 12))


def _skey(sc):
    return (int(sc.bus), sc.kind, round(float(sc.amp), 12))


class PooledPlant:
    units = PL.UNITS

    def __init__(self, workers: int = 7):
        import os
        for v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            os.environ[v] = "1"                  # one BLAS thread per worker (inherited by the spawned children): avoids thread oversubscription
        self.local = PL.AndesPlant()
        for a in ("limits", "z_ref", "z_lo", "z_hi", "var_names"):
            setattr(self, a, getattr(self.local, a))
        self.workers = workers
        self._pool = ProcessPoolExecutor(max_workers=workers, initializer=_init_worker)
        self._ev, self._evt = {}, {}
        self.n_event_tasks = 0
        self.pool_rebuilds = 0
        self.n_eval = 0

    def close(self):
        self._pool.shutdown(wait=True, cancel_futures=True)

    # ----------------------------------------------------------------- interface
    def evaluate(self, z):
        k = _key(z)
        if k not in self._ev:
            self.n_eval += 1
            self._ev[k] = self.local.evaluate(np.asarray(z, float))
        return self._ev[k]

    def prefetch(self, zs, scs, exc: bool = True):
        """Compute (in parallel) the event responses missing from the cache for every (z, scenario) pair with a valid initialisation."""
        todo, keys = [], []
        for z in zs:
            if not self.evaluate(z)["ok"]:
                continue
            for sc in scs:
                k = (_key(z), _skey(sc))
                have = self._evt.get(k)
                if (have is None or (exc and have["exc"] is None and have["jump"].get("ok"))) and k not in keys:
                    keys.append(k)
                    todo.append((np.asarray(z, float).tolist(), _skey(sc), exc))
        if todo:
            self.n_event_tasks += len(todo)
            for attempt in (0, 1):
                try:
                    for k, r in zip(keys, self._pool.map(_task, todo, chunksize=1)):
                        self._evt[k] = r
                    break
                except BrokenProcessPool:         # a worker died: rebuild the pool once and recompute (event responses are deterministic and cached)
                    self.pool_rebuilds += 1
                    self._pool.shutdown(wait=False, cancel_futures=True)
                    self._pool = ProcessPoolExecutor(max_workers=self.workers, initializer=_init_worker)
                    if attempt == 1:
                        for k in keys:
                            self._evt.setdefault(k, {"jump": {"ok": False, "reason": "BrokenProcessPool"}, "exc": {"ok": False}})

    def _event(self, z, sc, exc):
        k = (_key(z), _skey(sc))
        have = self._evt.get(k)
        if have is None or (exc and have["exc"] is None and have["jump"].get("ok")):
            self.prefetch([z], [sc], exc)
        return self._evt.get(k, {"jump": {"ok": False}, "exc": {"ok": False}})

    def jump(self, z, sc):
        return self._event(z, sc, False)["jump"]

    def excursion(self, z, sc):
        r = self._event(z, sc, True)["exc"]
        return r if r is not None else {"ok": False}
