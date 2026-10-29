"""DEC-056 figures for D7 and OC3 (post-processing of stored runs and state files; no TDS, no solve).
  IEEE39_DEC056_D7_settling.png      rolling 20-s bus-voltage drift vs time since RDC activation (L1 flat runs, OC1 pre-settling, OC2 self-consistent flat run)
  IEEE39_DEC056_D7_OC3_instability.png  OC3 pre-settling run up to the numerical failure: unit Q and the 1-s peak-to-peak envelope of P (log scale)
  IEEE39_DEC056_OC3_spectrum.png      rightmost real part of the post-jump closed-loop linearisation per DESIGN scenario at M0, the phase-1b point and phase-1b + SG30 v0 -0.01"""
from __future__ import annotations

import json

import numpy as np

import dec054_common as C54
import dec055_common as C55
import dec056_tds as T

R55 = C54.RUNS_DIR.parent / "DEC055_runs"
ST56 = C54.RUNS_DIR.parent / "DEC056_state"


def drift20(p, t_act):
    z = np.load(p / "series.npz")
    t, V = z["t"], z["V"]
    step = int(round(1.0 / (t[1] - t[0])))
    ts, Vs = t[::step], V[::step]
    d = np.array([np.abs(Vs[k:k + 21] - Vs[k]).max() for k in range(len(ts) - 20)])
    return ts[:len(d)] - t_act, d


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for oc, c in (("OC1", "tab:blue"), ("OC2", "tab:orange"), ("OC3", "tab:green")):
        t, d = drift20(R55 / f"D55L1_flat_{oc}_M0", 5.0)
        ax.semilogy(t, d, c=c, lw=1, label=f"{oc} M0, RDC on at 5 s (L1, 200 s)")
    t, d = drift20(T.RUNS / "D56D7_presettle_OC1_M0", 0.0)
    ax.semilogy(t, d, c="tab:blue", ls="--", lw=1.2, label="OC1 M0, RDC on at 0 s (D7, 600 s)")
    t, d = drift20(T.RUNS / "D56D7_flat_OC2_SCv0", 5.0)
    ax.semilogy(t, d, c="tab:red", lw=1.4, label="OC2 self-consistent dispatch, RDC on at 5 s")
    ax.axhline(C55.THR["flat_drift_pu"], c="k", ls=":", lw=0.9, label="G1 criterion 1e-3 pu (frozen)")
    ax.set(xlabel="time since RDC activation (s)", ylabel="max |V(s) - V(t)| over [t, t+20 s] (pu)", title="Closed-loop voltage settling of B2 from the dispatch point")
    ax.legend(fontsize=7)
    fig.tight_layout()
    with open(C55.FIG / "IEEE39_DEC056_D7_settling.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    z = np.load(T.RUNS / "D56RES_presettle_OC3_M0_partial" / "series.npz")
    t, P, Q = z["t"], z["P"], z["Q"]
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.2))
    k = t <= 343.0
    for i, u in enumerate(C55.UNITS):
        ax[0].plot(t[k], Q[k, i], lw=0.8, label=u)
    ax[0].set(xlabel="t (s), RDC on from 0 s", ylabel="Q (pu)", title="OC3 M0, B2 active from t = 0: unit reactive power", ylim=(-1, 5))
    ax[0].legend(fontsize=6, ncol=2)
    a = np.arange(250, 343, 0.5)
    env = np.array([(P[(t >= x) & (t < x + 0.5)].max(0) - P[(t >= x) & (t < x + 0.5)].min(0)).max() for x in a])
    ax[1].semilogy(a, np.maximum(env, 1e-7), "k.-", lw=0.8)
    ax[1].set(xlabel="t (s)", ylabel="max unit P peak-to-peak in 0.5 s (pu)", title="growth of the 1.27 Hz oscillation (SG30 P, SG39 Q) before the TDS failure at 343.4 s")
    fig.tight_layout()
    with open(C55.FIG / "IEEE39_DEC056_D7_OC3_instability.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    sp = json.loads((ST56 / "oc3_spectrum.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(10, 4))
    names = list(sp["M0"].keys())
    x = np.arange(len(names))
    for j, (lab, c) in enumerate((("M0", "tab:gray"), ("phase1b", "tab:orange"), ("phase1b_SG30_v0_-0.01", "tab:blue"))):
        ax.bar(x + (j - 1) * 0.27, [sp[lab][n] for n in names], width=0.27, color=c, label=lab)
    ax.axhline(0, c="k", lw=0.8)
    ax.set_xticks(x, names, rotation=45, fontsize=7)
    ax.set(ylabel="max Re(eig) of the post-jump closed loop (1/s)", title="OC3: post-jump linearisation used by the M3 excursion predictor", yscale="symlog")
    ax.legend(fontsize=7)
    fig.tight_layout()
    with open(C55.FIG / "IEEE39_DEC056_OC3_spectrum.png", "xb") as f:
        fig.savefig(f, dpi=140, format="png")
    plt.close(fig)
    print("figures written")


def spectrum():
    """Static: max Re eig of plant.affine A for each DESIGN scenario at the three OC3 points (written exclusively to the DEC-056 state)."""
    import dec055_l0 as L0
    import dec055_oc as OCM
    plant = OCM.make_plant("OC3")
    m0 = np.array(json.loads((C55.STATE / "m0_OC3.json").read_text(encoding="utf-8"))["z"])
    zb = np.array(json.loads((ST56 / "oc3_phase1b.json").read_text(encoding="utf-8"))["z"])
    zc = zb.copy()
    zc[9] -= 0.01
    out = {}
    for lab, z in (("M0", m0), ("phase1b", zb), ("phase1b_SG30_v0_-0.01", zc)):
        out[lab] = {sc.name: float(np.max(np.linalg.eigvals(plant.affine(z, sc)[0]).real)) for sc in L0.design_scenarios()}
        print(lab, out[lab], flush=True)
    with open(ST56 / "oc3_spectrum.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1)


def collect():
    """Copy the key static DEC-056 results from the local state into one tracked artifact (with the SHA-256 of every source file)."""
    out = {"stage": "DEC-056 static results (copied from backups/DEC056_state; 0 TDS)", "sources": {}}
    for name in ("oc3_phase1b", "oc3_seeded_reduced", "oc3_seeded_full", "oc3_spectrum", "oc3_spectrum_seeded_full",
                 "d7_selfc2_OC2_M0_v0", "d7_selfc2_OC2_M0_all", "d7_selfc2_OC1_M0_v0_gq0.2", "d7_selfc2_OC3_M0_v0_gq0.2"):
        p = ST56 / f"{name}.json"
        out["sources"][name] = C54.sha_file(p)
        out[name] = json.loads(p.read_text(encoding="utf-8"))
    for oc in ("OC1", "OC2", "OC3"):
        p = ST56 / f"d7_diag_{oc}_M0.json"
        out["sources"][f"d7_diag_{oc}_M0"] = C54.sha_file(p)
        out[f"d7_diag_{oc}_M0"] = json.loads(p.read_text(encoding="utf-8"))
    with open(C55.ART / "IEEE39_DEC056_static_results.json", "x", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("static results written")


if __name__ == "__main__":
    import sys
    {"spectrum": spectrum, "collect": collect}.get(sys.argv[1] if sys.argv[1:] else "", main)()
