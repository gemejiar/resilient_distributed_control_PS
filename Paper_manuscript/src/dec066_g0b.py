"""DEC-066 G0 (b): theoretical algebraic jump vs first numerical step vs first stored point, for the 36 DEC-062 blind cells.  Read-only.  Writes IEEE39_DEC066_G0_alignment.csv exclusively with 'write'.
columns: jump_pmax_margin (pred JSON, algebraic jump with frozen x), tds_margin_t5.0 (first stored post-jump sample, one dt/16 step after the pre-event sample), tds_margin_pre (last pre-event sample), m50 (minimum over [t_e, t_e+50 ms])."""
import csv
import json
import sys

import numpy as np

import dec055_common as C55
import dec055_oc as OCM
import dec059_tds as T
import dec062_r5 as R5

TE = 5.0


def main(write=False):
    rows = []
    for oc in ("OC1", "OC2"):
        pmax = np.asarray(OCM.make_plant(oc).limits["pmax"], float)
        for m in ("M0", R5.DES[oc]):
            pr = json.loads((C55.ART / f"IEEE39_DEC059_pred_{oc}_{'M0' if m == 'M0' else m}_test.json").read_text(encoding="utf-8"))
            cells = {c["name"]: c for c in pr["cells"]}
            for b in R5.TEST:
                for s in R5.SEV:
                    name = f"b{b}P_{s}"
                    z = np.load(T.RUNS / f"D62TEST_B5P_{oc}_{m}_{name}" / "series.npz", allow_pickle=True)
                    t, P = z["t"], z["P"]
                    k = int(np.searchsorted(t, TE - 1e-9))
                    w = (t >= TE) & (t <= TE + 0.05)
                    c = cells[name]
                    rows.append([oc, m, name, c["jump_pmax_margin_min"], float((pmax - P[k]).min()), float((pmax - P[k - 1]).min()), float((pmax[None, :] - P[w]).min()), float(t[k - 1]), float(t[k]),
                                 float((pmax - P[k]).min()) - c["jump_pmax_margin_min"]])
    d = np.array([r[-1] for r in rows])
    print("n", len(rows), "tds_t5.0 - jump: min", d.min(), "max", d.max(), "mean", d.mean(), "max abs", np.abs(d).max())
    if write:
        with open(C55.ART / "IEEE39_DEC066_G0_alignment.csv", "x", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["oc", "dispatch", "cell", "jump_pmax_margin_pred", "tds_margin_t5.0", "tds_margin_last_pre_sample", "m50_tds", "t_pre", "t_first_post", "tds_t5.0_minus_jump"])
            w.writerows(rows)


if __name__ == "__main__":
    main("write" in sys.argv)
