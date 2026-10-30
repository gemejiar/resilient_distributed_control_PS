"""DEC-066: LaTeX tables of the ablation (T4, T5b, T6) generated from the CSV files (no hand-typed numbers) -> Paper_manuscript/IEEE39_DEC066_ablation_tables.tex (exclusive).
Run: <venv python> dec066_abl_latex.py write"""
from __future__ import annotations

import csv
import sys

import dec055_common as C55

ART = C55.ART
OUT = ART.parent / "IEEE39_DEC066_ablation_tables.tex"
BS = "\\"


def rd(n):
    return list(csv.DictReader(open(ART / n, encoding="utf-8")))


def f(x, d=4):
    return "--" if x in ("", "None", None) else f"{float(x):.{d}f}"


def esc(s):
    return str(s).replace("_", BS + "_")


CL = {"SAFE": "SAFE", "UNSAFE": "UNSAFE", "NUMERICALLY_INDETERMINATE": "INDET."}
NM = {"A": "A (M3)", "B": "B (+dense)", "C": "C (+dense$+\\varepsilon_{OS}$)", "D": "D (M3+OS)", "E": "E ($U_{D8}$ only)"}
EOL = " \\\\"


def wrap(cap, lab, spec, head, body, star=True):
    env = "table*" if star else "table"
    return "\n".join([f"\\begin{{{env}}}[t]", "\\centering\\footnotesize", f"\\caption{{{cap}}}", f"\\label{{{lab}}}", "\\resizebox{\\linewidth}{!}{\\begin{tabular}{" + spec + "}", "\\toprule", head, "\\midrule"]
                     + body + ["\\bottomrule", "\\end{tabular}}", f"\\end{{{env}}}"])


def t4():
    r = rd("IEEE39_DEC066_T4_OPF_ablation.csv")
    body = [" & ".join([NM[x["variant"]], "feas.\\ pred." if x["status"] == "FEASIBLE_PREDICTED" else esc(x["status"]), f(x["J"], 4), f(x["sumdP_vs_case_MW"], 1), f(x["sumdP_vs_A_MW"], 1), f(x["kkt"], 3),
                       f(x["ext_min_margin_gridonly"], 4), f(x["ext_min_margin_dense_noeps"], 4), esc(x["ext_unit"]) + " " + esc(x["ext_event"]), x["plant_evals"], f(x["seconds"], 0)]) + EOL for x in r]
    return wrap("The five preventive designs (OC1; same 12 design events, objective, solver and settings; none certified optimal). Margins are predicted minimum Pmax margins over the design events without $\\varepsilon$ margins: ``grid'' uses the M3 excursion on the 195~s grid, ``dense'' adds the 0--50~ms evaluation. Design A was optimised with M0 as an additional seed, B--E from M3; the KKT residual of B (0.598) shows that it is not a converged point.",
                "tab:ablation_designs", "llrrrrrrlrr",
                "Design & Status & $J$ & $\\sum|\\Delta P|$ vs case (MW) & vs A (MW) & KKT & margin grid (pu) & margin dense (pu) & limiting & Plant eval. & Time (s)" + EOL, body)


def t5b():
    r = rd("IEEE39_DEC066_T5b_pred_vs_obs.csv")
    body = [" & ".join([esc(x["event"]).replace(BS + "_", " "), x["design"], f(x["pred_min_margin"]), f(x["obs_min_margin_0_50ms"]), f(x["error_obs_minus_pred"]), CL[x["obs_class"]], "yes" if x["obs_physical_violation_mP_lt_0"] == "True" else "no",
                       f(x["max_excess_pu"]), f(x["duration_below_limit_ms_approx"], 2), esc(x["limiting_unit"]), f(x["t_peak_ms"], 2), f(x["obs_margin_50ms_10s"], 3), f(x["f_nadir_hz"], 3), f(x["V_bus_min"], 3)]) + EOL for x in r]
    return wrap("Observed minimum Pmax margin of delivered power against the margin registered before the simulations (B5$'$, OC1, 17 runs). Class by rule M3V-1 (band $\\pm U_{D8}=0.0109$~pu); ``Viol.'' flags $m<0$ even when it lies inside the band (INDET.). Error: observed $-$ predicted (positive: conservative). Duration is the integral of the below-limit indicator over stored samples (local step 0.24~ms), hence approximate. $t_{\\rm pk}$ is the first stored sample of the minimum. The last three columns are the observed margin in 50~ms--10~s (pu), the COI frequency nadir (Hz) and the minimum bus voltage (pu).",
                "tab:ablation_obs", "llrrrlcrrlrrrr",
                "Event & Design & Pred. & Obs. & Error & Class & Viol. & Excess & Dur. (ms) & Unit & $t_{\\rm pk}$ (ms) & $m_{50\\rm ms-10s}$ & $f_{\\rm nadir}$ & $V_{\\min}$" + EOL, body)


def t6():
    r = [x for x in rd("IEEE39_DEC066_T6_contrasts.csv") if x["event"] in ("b8_S3", "b21_S3", "b15_S3", "b23_S3")]
    body = [" & ".join([esc(x["event"]).replace(BS + "_", " "), x["contrast"], esc(x["component"]), f(x["d_margin_obs"]), "yes" if x["viol_a"] == "True" else "no", "yes" if x["viol_b"] == "True" else "no", f(x["d_sumdP_vs_case_MW"], 2), f(x["dJ"], 4)]) + EOL for x in r]
    return wrap("Marginal contrasts between designs: change in the observed minimum Pmax margin (pu) and in the design effort. The five designs are a directed set, not a factorial: the contrasts $B-A$ (dense), $C-B$ ($\\varepsilon_{OS}$), $D-C$ ($U_{D8}$ given dense and $\\varepsilon_{OS}$), $E-A$ ($U_{D8}$ alone) and $D-E$ (dense and $\\varepsilon_{OS}$ given $U_{D8}$) are not additive and interactions are not identified. ``Viol.'' columns: $m<0$ in the first / second design of the pair. The effort difference is a design-level quantity (MW, $J$), identical for all events.",
                "tab:ablation_contrasts", "llllccrr",
                "Event & Contrast & Component & $\\Delta m_{\\rm obs}$ & Viol. (1st) & Viol. (2nd) & $\\Delta\\sum|\\Delta P|$ (MW) & $\\Delta J$" + EOL, body, star=False)


def main(write=False):
    txt = "% Generated by dec066_abl_latex.py from IEEE39_DEC066_T*.csv (DEC-066). Do not edit by hand.\n" + "\n\n".join([t4(), t5b(), t6()]) + "\n"
    print(txt[:700])
    if write:
        with open(OUT, "x", encoding="utf-8") as fh:
            fh.write(txt)


if __name__ == "__main__":
    main("write" in sys.argv)
