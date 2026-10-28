"""DEC-054 G5: freeze the design before the prospective cohort.  Creates IEEE39_DEC054_design_frozen.json EXCLUSIVELY (to be committed to Git before any P3-C TDS).
Inputs: final design state files in the local G4 state folder (m0, m1/m1b, m2, m3 or m3_final), P3-A/P3-B eps calibration.  One dispatch per method (M0-M3)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

import dec054_calib as CAL
import dec054_common as COM
import dec054_g4_design as G4
import dec054_runner as RUN

SRC = Path(__file__).parent
CODE = ["dec054_common.py", "dec054_plant.py", "dec054_predictor.py", "dec054_rdcinit.py", "dec054_opf.py", "dec054_pool.py", "dec054_runner.py", "dec054_store.py", "dec054_metrics.py",
        "dec054_jump.py", "dec054_calib.py", "dec054_g4_design.py", "dec054_p3a_audit.py", "dec054_p3b.py", "dec054_g5_freeze.py"]
TEST_AMP = 0.58564          # pu (58.564 MW), one P step per test bus
CRITERIA = {
    "primary": "number of (scenario, unit) pairs with stored-sample P outside [Pmin, Pmax]; total and maximum excess; Q/S limits and the 39 voltages [0.95,1.05] reported separately",
    "NUMERICALLY_SUPPORTED_for_M3": "all of: (i) M3 is a new ex-ante policy (not R35_040) using only DESIGN/TUNE data; (ii) on the six frozen scenarios M3 has no more violating (scenario,unit) pairs than each of M0, M1, M2 "
                                    "and strictly fewer than the best comparator at equal cost, or equal (zero) violations with redispatch cost J at least 20 % lower than the cheapest comparator with zero violations; "
                                    "(iii) voltage band respected (post-event) and no TDS_NUMERICAL_FAILURE attributable to M3 only",
    "NEGATIVE_FINDING": "reported in full if M3 does not satisfy the above; criteria are not modified after observing results",
    "equal_cost_contrast": "NOT_MATCHED unless |J(M1)-J(M3)| <= 10 % of J(M3) (single frozen M1 dispatch)",
    "equal_compliance_contrast": "M1 is the smallest rho on the predeclared grid whose DESIGN/TUNE predicted margins (jump+excursion+eps) are all >= 0",
    "small_sample": "six scenarios, one per bus, one amplitude: descriptive counts only, no inferential statistics, no universal-safety claim",
}


def main(m3_state="m3"):
    st = lambda n: G4.load_state(n)
    m0, m2, m3 = st("m0"), st("m2"), st(m3_state)
    m1 = st("m1b")
    grid = {g["rho"]: g for g in st("m1")["grid"] + m1["grid"] if "describe" in g}
    ok_rho = sorted(r for r, g in grid.items() if g["describe"]["n_violated_margins"] == 0)
    rho = ok_rho[0]
    disp = {"M0": m0["describe"], "M1": grid[rho]["describe"], "M2": m2["describe"], "M3": m3["describe"]}
    for k, v in disp.items():
        assert v["init_ok"], f"{k} dispatch is not initialisable"
    dispatches = {k: RUN.make_dispatch_entry(np.array(v["z"]), status={"M0": m0["status"], "M1": grid[rho]["status"], "M2": m2["status"], "M3": m3["status"]}[k], J=v["J"],
                                             note=f"{k}; design set DESIGN+TUNE statics" + (f"; rho={rho}" if k == "M1" else "")) for k, v in disp.items()}
    part = CAL.partition()
    assert part["TEST"] == COM.TEST and part["DESIGN"] == COM.DESIGN and part["TUNE"] == COM.TUNE
    scen = [{"name": f"bus{b}P", "bus": b, "kind": "P", "amp": TEST_AMP} for b in COM.TEST]
    eJ, eEu, eEd = G4.eps_vectors()
    eps = {"source": "P3-A DESIGN calibration (+ P3-B if used); EMPIRICAL_LOCATION_AWARE_MARGIN, kappa=1.5, floor 1e-3; not a bound", "eps_J": eJ.tolist(), "eps_E_up": eEu.tolist(), "eps_E_dn": eEd.tolist(), "units": COM.UNITS}
    params = dict(COM.PROPOSED, design_events=[f"b{b}P" for b in COM.DESIGN + COM.TUNE], design_amp_pu=G4.AMP, m1_rho_grid=G4.RHO_GRID, m1_rho_refine=G4.RHO_REFINE, m1_rho_selected=rho,
                  solver="scipy SLSQP, finite-difference Jacobians, forward h=1e-4", N_it_cfg=int(os.environ.get("DEC054_NIT", "25")))
    import andes
    frozen = RUN.write_frozen(COM.ART / "IEEE39_DEC054_design_frozen.json", SRC, CODE, {"DESIGN": COM.DESIGN, "TUNE": COM.TUNE, "TEST": COM.TEST, "seed": COM.SEED, "calibration_only": COM.CALIBRATION_ONLY,
                                                                                         "eligible": COM.ELIGIBLE}, params, eps, dispatches, {"buses": COM.TEST, "scenarios": scen, "horizon": {"event_s": 5.0, "end_s": 200.0, "dt_s": COM.DT}},
                              andes.__version__, hypotheses="H-A: M2 fewer violations than M0 where the jump dominates; H-B: M3 fewer violations than M2 or equal at lower cost where the excursion dominates; "
                                                           "H-C: M3 needs less redispatch than M1 at equal predicted compliance; H-D: predictor errors reported per unit", criteria=json.dumps(CRITERIA))
    print("frozen; dispatches J:", {k: round(v["J"], 4) for k, v in dispatches.items()}, "rho", rho)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "m3")
