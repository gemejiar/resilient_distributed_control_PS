"""DEC-055 TDS executor for L1+ (NOT executed in L0).  Wraps dec054_runner.execute_tds without editing it:
  * selects the OC case (dec055_oc.select) and the PFlow tolerance of DEC-055;
  * additionally records the SG rotor speeds (GENROU.omega), M and Sn, so that f_COI can be computed (DEC-055 point 8).
The extra recording reads the stored state trajectory after the run (system.dae.ts.x) and cannot change the dynamics; the bit-for-bit regression
against an unmodified run is deferred to L1 (it needs a TDS)."""
from __future__ import annotations

import numpy as np

import dec055_common as C
import dec055_oc as OCM


def coi_record(system) -> dict:
    """Rotor speeds of the synchronous machines and the COI weights, from a finished ANDES system (pure read)."""
    x = np.asarray(system.dae.ts.x)
    om = np.asarray(x[:, system.GENROU.omega.a], float)
    M, Sn = np.asarray(system.GENROU.M.v, float), np.asarray(system.GENROU.Sn.v, float)
    fn = float(np.asarray(system.GENROU.fn.v, float)[0])
    return {"sg_omega_pu": om, "sg_M_s": M, "sg_Sn_MVA": Sn, "f_coi_hz": C.f_coi_hz(om, M, Sn, fn), "fn_hz": fn}


def execute_tds_oc(oc: str, z, scenario, time_step_s=None, pflow_tol=None) -> dict:
    """Same contract as dec054_runner.execute_tds plus COI series.  Only callable after an L1+ authorisation and a ledger request.
    pflow_tol overrides the DEC-055 PFlow tolerance (used only by the L1 regression against stored DEC-054 runs, which used the ANDES default 1e-6)."""
    OCM.select(oc)
    OCM.PFLOW_TOL = OCM.PFLOW_TOL if pflow_tol is None else pflow_tol
    import dec054_runner as R
    import run_b3_ieee39 as b
    captured = {}
    orig = b.run

    def run(*a, **k):
        system, d, diag = orig(*a, **k)
        if diag.get("tds_ok"):
            captured.update(coi_record(system))
        return system, d, diag
    b.run = run
    try:
        res = R.execute_tds(z, scenario, time_step_s)
    finally:
        b.run = orig
    if res.get("series") is not None and captured:
        res["series"].update({k: v for k, v in captured.items() if k != "fn_hz"})
        res.setdefault("diag", {})["fn_hz"] = captured["fn_hz"]
    res.setdefault("diag", {})["oc"] = oc
    return res
