"""DEC-066: LaTeX fragments of paper tables T1-T3 generated from the CSV files (no hand-typed numbers).  Writes Paper_manuscript/IEEE39_DEC066_tables.tex exclusively.
Run: <venv python> dec066_paper_latex_tables.py write"""
from __future__ import annotations

import csv
import sys

import dec055_common as C55

ART = C55.ART
OUT = ART.parent / "IEEE39_DEC066_tables.tex"


def rd(n):
    return list(csv.DictReader(open(ART / n, encoding="utf-8")))


def f(x, d=3):
    return "--" if x in (None, "", "None") else f"{float(x):.{d}f}"


def esc(s):
    return str(s).replace("_", "\\_").replace("&", "\\&").replace("%", "\\%")


def t1():
    rows = rd("IEEE39_DEC066_T1_dispatches.csv")
    lab = {"DEC054": "A", "DEC055": "B", "DEC059": "B", "DEC060": "B", "DEC061": "B"}
    s = ["\\begin{table*}[t]", "\\centering\\footnotesize", "\\caption{Preventive dispatches used in this study. $J$ is a normalised displacement/pattern cost, not an economic cost. $\\sum|\\Delta P|$ is over the nine decision units (slack excluded), in MW on the 100~MVA base, against the M0 dispatch of the same group and, where recorded, against the original case dispatch. Min.\\ margin is the smallest predicted design margin as recorded in the state file. Group A: DEC-054 design set; group B: DEC-055/059--061 design sets (OC1 and OC2). All optimisations are SLSQP runs with predictor-based constraints; none is certified optimal.}",
         "\\label{tab:dispatches}", "\\begin{tabular}{llllrrrrrr}", "\\toprule",
         "OC & Method & Status & $J$ & $\\sum|\\Delta P|$ vs M0 & vs case & Min.\\ margin & KKT & Time (s) & Plant eval.\\\\", "\\midrule"]
    for r in rows:
        s.append(" & ".join([esc(r["oc"]), esc(r["method"]), esc(r["status"]).replace("FEASIBLE\\_PREDICTED", "feas.\\ pred.").replace("LOCAL\\_OPTIMUM\\_FOUND", "local opt."), f(r["J"]), f(r["sumdP_MW_vs_M0"], 1), f(r["sumdP_MW_vs_case_recorded"], 1),
                             f(r["pred_min_margin_design"], 4), f(r["kkt"], 3), f(r["seconds"], 0), f(r["plant_evaluations"], 0)]) + "\\\\")
    s += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    return "\n".join(s)


def t2():
    rows = [r for r in rd("IEEE39_DEC066_T2_observed_safety.csv")]
    s = ["\\begin{table*}[t]", "\\centering\\footnotesize", "\\caption{Observed safety of the 36 blind cells (ANDES time-domain, 0--195~s after the event, B5$'$ controller). Class by the frozen rule M3V-1: delivered-power margin to Pmax within the first 50~ms with the numerical band $U_{D8}=0.0109$~pu; binary after 50~ms and for Q, S and voltage. Worst margin: smallest Pmax margin over 0--195~s. Counts are listed as S1/S2/S3 (three cells per severity). Peak window: where the worst margin occurs (J: first stored sample, F: 0--50~ms, M: 50~ms--10~s, S: 10--195~s). QSV: cells with an observed Q, S or voltage-band violation.}",
         "\\label{tab:observed}", "\\begin{tabular}{lcccccrcc}", "\\toprule", "OC / dispatch & SAFE (S1/S2/S3) & INDET. & UNSAFE (S1/S2/S3) & False SAFE (50~ms) & Inadm.\\ at jump & Worst margin & Peak J/F/M/S & QSV\\\\", "\\midrule"]
    order = [("OC1", "M0"), ("OC1", "M3REV3"), ("OC2", "M0"), ("OC2", "M3OS")]
    name = {"M0": "M0", "M3REV3": "M3+OS rev3", "M3OS": "M3+OS"}
    for oc, m in order:
        a = {r["severity"]: r for r in rows if r["oc"] == oc and r["dispatch"] == m}
        al = a["ALL"]
        s.append(" & ".join([f"{oc} {name[m]}", "/".join(a[k]["SAFE"] for k in ("S1", "S2", "S3")), al["INDET"], "/".join(a[k]["UNSAFE"] for k in ("S1", "S2", "S3")), al["false_SAFE_50ms"], al["inadmissible_at_jump_pred"],
                             f(al["worst_margin"], 3), f"{al['peak_window_JUMP']}/{al['peak_window_FAST']}/{al['peak_window_MID']}/{al['peak_window_SLOW']}", al["qsv_violating_cells"]]) + "\\\\")
    s += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    return "\n".join(s)


def t3():
    rows = rd("IEEE39_DEC066_T3_predictor.csv")
    s = ["\\begin{table*}[t]", "\\centering\\footnotesize", "\\caption{Accuracy of the predicted worst Pmax margin against the stored time-domain series. $e=$ observed $-$ predicted margin (positive: conservative prediction). 50~ms: dense predictor, observed over $[t_e,t_e+50~\\mathrm{ms}]$; 195~s: M3 grid predictor, observed over $[t_e,195~\\mathrm{s}]$. The 195~s RMSE excluding divergent predictions (margin magnitude $\\ge1$~pu) is also given. Class counts are against the observed class over 0--195~s.}",
         "\\label{tab:predictor}", "\\begin{tabular}{lrrrrrrrrr}", "\\toprule", "Group & $n$ & Bias$_{50}$ & RMSE$_{50}$ & RMSE$_{195}$ & RMSE$_{195}^{\\rm excl}$ & FS$_{50}$ & FU$_{50}$ & FS$_{195}$ & FU$_{195}$\\\\", "\\midrule"]
    for r in rows:
        s.append(" & ".join([esc(r["group"]), r["n"], f(r["e50_bias"], 5), f(r["e50_RMSE"], 5), f(r["eF_RMSE"], 3), f(r["eF_excl_RMSE"], 4), r["pred50_false_SAFE"], r["pred50_false_UNSAFE"], r["predF_false_SAFE"], r["predF_false_UNSAFE"]]) + "\\\\")
    s += ["\\bottomrule", "\\multicolumn{10}{l}{FS: false SAFE (predicted SAFE, observed not SAFE); FU: false UNSAFE. Margins in pu.}\\\\", "\\end{tabular}", "\\end{table*}"]
    return "\n".join(s)


def t3b():
    rows = [r for r in rd("IEEE39_DEC066_T3b_horizon_sweep.csv") if r["group"] in ("ALL", "OC1 M0")]
    s = ["\\begin{table}[t]", "\\centering\\footnotesize", "\\caption{Retrospective horizon sweep of the predicted classification (predicted margin over $[t_e,t_e+T_c]$ on the saved M3 grid, no parabolic refinement). Exploratory: the horizon was examined on the same 36 observed cells and it is not a blind result.}",
         "\\label{tab:horizon}", "\\begin{tabular}{lrrrrr}", "\\toprule", "Group & $T_c$ (s) & Agree & False SAFE & False UNSAFE & Pred.\\ INDET.\\\\", "\\midrule"]
    for r in rows:
        s.append(" & ".join([esc(r["group"]), f(r["T_c_s"], 2), f"{r['agree']}/{r['n']}", r["false_SAFE"], r["false_UNSAFE"], r["INDET_pred"]]) + "\\\\")
    s += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    return "\n".join(s)


def main(write=False):
    txt = "% Generated by dec066_paper_latex_tables.py from IEEE39_DEC066_T*.csv (DEC-066). Do not edit by hand.\n" + "\n\n".join([t1(), t2(), t3(), t3b()]) + "\n"
    txt = txt.replace("\\begin{tabular}", "\\resizebox{\\linewidth}{!}{\\begin{tabular}").replace("\\end{tabular}", "\\end{tabular}}")
    print(txt[:1500])
    if write:
        with open(OUT, "x", encoding="utf-8") as fh:
            fh.write(txt)


if __name__ == "__main__":
    main("write" in sys.argv)
