"""DEC-054 end-to-end pipeline demo on the SYNTHETIC plant (no ANDES, no TDS, no historical plant).  Output is NOT evidence about IEEE-39:
it only shows that M0-M3, Algorithm 1 and the margin bookkeeping run together.  Writes IEEE39_DEC054_synthetic_pipeline_demo.csv (exclusive creation)."""
import csv

import numpy as np

import dec054_common as COM
import dec054_opf as OPF
import dec054_synth as SYN


def main(out=None):
    plant = SYN.SyntheticPlant(seed=1)
    sc = [OPF.Scenario(f"b{b}", b, "P", 0.58564 * a) for b in (8, 23, 28) for a in (0.5, 1.0)]
    cfg = dict(COM.PROPOSED, K_max=8, N_it=120)
    eJ, eE = np.full(10, COM.PROPOSED["eps_floor_pu"]), np.full(10, COM.PROPOSED["eps_floor_pu"])
    res = {"M0": OPF.solve_static(plant, "M0", sc, cfg=cfg), "M1": OPF.solve_static(plant, "M1", sc, rho=0.02, cfg=cfg),
           "M2": OPF.algorithm1(plant, "M2", sc, eJ, eE, cfg=cfg), "M3": OPF.algorithm1(plant, "M3", sc, eJ, eE, cfg=cfg)}
    judge2 = OPF.Problem(plant, "M2", sc, eps_J=eJ, cfg=cfg)
    judge3 = OPF.Problem(plant, "M3", sc, eps_J=eJ, eps_E=eE, cfg=cfg)
    rows = []
    for m, r in res.items():
        if r.z is None:
            rows.append(dict(method=m, status=r.status, note="SYNTHETIC_NOT_EVIDENCE"))
            continue
        pb = OPF.Problem(plant, "M0", sc, cfg=cfg)
        n_v2 = sum(int(((judge2.margins_d(r.z, d)[0] < -1e-4).sum() + (judge2.margins_d(r.z, d)[1] < -1e-4).sum())) for d in range(len(sc)))
        n_v3 = sum(int(((judge3.margins_d(r.z, d)[0] < -1e-4).sum() + (judge3.margins_d(r.z, d)[1] < -1e-4).sum())) for d in range(len(sc)))
        rows.append(dict(method=m, status=r.status, J=pb.J(r.z), C_disp=pb.C_disp(r.z), C_pat=pb.C_pat(r.z), min_margin_jump_only=judge2.most_violated(r.z)[0], min_margin_jump_excursion=judge3.most_violated(r.z)[0],
                         violated_margins_jump_only=n_v2, violated_margins_jump_excursion=n_v3, cuts=len(r.cuts), note="SYNTHETIC_NOT_EVIDENCE"))
    cols = ["method", "status", "J", "C_disp", "C_pat", "min_margin_jump_only", "min_margin_jump_excursion", "violated_margins_jump_only", "violated_margins_jump_excursion", "cuts", "note"]
    path = out or (COM.ART / "IEEE39_DEC054_synthetic_pipeline_demo.csv")
    with open(path, "x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(rows)
    return rows


if __name__ == "__main__":
    for r in main():
        print(r)
