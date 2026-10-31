"""DEC-066 closure: LaTeX tables generated from the CSV files (no hand-typed numbers) -> Paper_manuscript/IEEE39_DEC066_closure_tables.tex (exclusive).
  tab:equaleffort   (T7)  designs at equal redispatch effort: design-level and observed margins
  tab:convergence   (T4e) start-point sensitivity of the optimisations
  tab:validation    (T8)  out-of-design cells, counter-condition and step-sensitivity cells
Run: <venv python> dec066_close_latex.py write"""
from __future__ import annotations

import csv
import sys

import dec055_common as C55

ART = C55.ART
OUT = ART.parent / "IEEE39_DEC066_closure_tables.tex"
BS = "\\"
EOL = " \\\\"


def rd(n):
    return list(csv.DictReader(open(ART / n, encoding="utf-8")))


def f(x, d=4):
    return "--" if x in ("", "None", None) else f"{float(x):.{d}f}"


def esc(s):
    return str(s).replace("_", BS + "_").replace("%", BS + "%")


def wrap(cap, lab, spec, head, body, star=False):
    env = "table*" if star else "table"
    return "\n".join([f"\\begin{{{env}}}[t]", "\\centering\\footnotesize", f"\\caption{{{cap}}}", f"\\label{{{lab}}}", "\\resizebox{\\linewidth}{!}{\\begin{tabular}{" + spec + "}", "\\toprule", head, "\\midrule"]
                     + body + ["\\bottomrule", "\\end{tabular}}", f"\\end{{{env}}}"])


NM = {"A": "A (M3)", "E": "E ($U$ only, 0.0109)", "DQ1": "DQ1 (dense$+\\varepsilon_{OS}$, $U=0.0044$)", "EQ1": "EQ1 ($U$ only, 0.0193)", "D": "D (M3+OS, $U=0.0109$)"}


def t7():
    d = {r["design"]: r for r in rd("IEEE39_DEC066_T7_equal_effort.csv")}
    o = {(r["design"], r["event"]): r for r in rd("IEEE39_DEC066_T8_all_cells.csv") if r["step"].startswith("nominal")}
    body = []
    for k in ("A", "E", "DQ1", "EQ1", "D"):
        r = d[k]
        cells = []
        for ev in ("b8P_S3", "b21P_S3"):
            c = o.get((k, ev))
            cells += [f(c["obs_0_10s"]) + (" (viol.)" if c["physical_violation"] == "True" else ""), f(c["pre_headroom_limiting"], 3)] if c else ["--", "--"]
        body.append(" & ".join([NM[k], f(r["sumdP_vs_case_MW"], 1), f(r["J"], 4), f(r["ext_min_margin_design"]), r["n_events_margin_lt_0"] + "/" + r["n_events"]] + cells) + EOL)
    return wrap("Designs at (approximately) equal redispatch effort: E and DQ1 at about 58.7~MW, D and EQ1 at about 61.2~MW (sum of $|\\Delta P|$ against the case dispatch; equal redispatch is not equal economic cost, see $J$). Predicted: minimum external margin over the 12 design events (grid+dense excursion, no $\\varepsilon$) and number of the 27 valid design and evaluation events with negative predicted margin. Observed: minimum Pmax margin 0--10~s in the time-domain simulation (pu; ``viol.'' = $m<0$) and pre-event headroom of the limiting unit at the two events simulated for all five designs (bus 8: SG31; bus 21: SG33).",
                "tab:equaleffort", "lrrrrrrrr",
                "Design & $\\sum|\\Delta P|$ (MW) & $J$ & pred. min margin & events $m<0$ & obs. b8 S3 & headroom SG31 & obs. b21 S3 & headroom SG33" + EOL, body, star=True)


def t4e():
    rows = rd("IEEE39_DEC066_T4e_convergence.csv")
    body = [" & ".join([esc(r["design"]), esc(r["start"]), esc(r["status"]).replace("FEASIBLE" + BS + "_PREDICTED", "feas.\\ pred.").replace("SOLVER" + BS + "_FAILED", "solver failed"), f(r["J"], 6), f(r["kkt_residual"], 3), f(r["sum_abs_dP_vs_case_MW"], 2),
                       "--" if r["max_abs_dz_vs_group_first"] in ("", "0.0") else f"{float(r['max_abs_dz_vs_group_first']):.1e}"]) + EOL for r in rows]
    return wrap("Convergence and start-point sensitivity of the optimisations (OC1; no design reaches the local-optimum test $\\mathrm{KKT}\\le10^{-3}(1+|J|)$ used by the solver wrapper). Algorithm~1 always starts from the case dispatch and uses the stored seed only if that start fails; rows marked ``replaced by'' force another start (control runs). The last column is the largest change of the decision vector with respect to the first design of the same group. The KKT residual is a finite-difference residual that depends on the active-set tolerance: the same point returns 0.027 (B3) and 0.60 (B, B4).",
                "tab:convergence", "llllrrr", "Run & Start & Status & $J$ & KKT & $\\sum|\\Delta P|$ (MW) & max $|\\Delta z|$" + EOL, body, star=True)


def t8():
    rows = [r for r in rd("IEEE39_DEC066_T8_all_cells.csv") if r["lot"] in ("F3", "F5", "F4") or r["step"] != "nominal (dt, local dt/16)"]
    body = []
    for r in rows:
        body.append(" & ".join([esc(r["event"]).replace(BS + "_", " ").replace("P" + BS + "_", " "), r["design"], esc(r["step"]).replace("nominal (dt, local dt/16)", "nominal"), esc(r["evidence_role"].split(" (")[0]),
                                f(r["pred_0_10s"]), f(r["obs_0_10s"]), f(r["error_obs_minus_pred"]) if r["error_obs_minus_pred"] != "" else "--", f(r["obs_10_195s"], 4) if r["lot"] != "F4" else "--",
                                f(r["t_peak_ms"], 2), "yes" if r["physical_violation"] == "True" else "no"]) + EOL)
    return wrap("Cells outside the ablation matrix: out-of-design validation (bus 18), counter-condition (bus 39, a previously observed bus), step-sensitivity runs (E2, F5: step $\\Delta t/2$ with local refinement; F4: fixed $\\Delta t/16$ over 20~s, no local refinement, so the 10--195~s column is not available). Pred.: margin registered before the run for 0--10~s; obs.: minimum Pmax margin 0--10~s; error: observed $-$ predicted (positive: conservative). $t_{\\rm pk}$: instant of the 0--50~ms minimum after the event.",
                "tab:validation", "lllllrrrrc", "Event & Design & Step & Role & Pred. & Obs.\\ 0--10~s & Error & Obs.\\ 10--195~s & $t_{\\rm pk}$ (ms) & Viol." + EOL, body, star=True)


def main(write=False):
    txt = "% Generated by dec066_close_latex.py from IEEE39_DEC066_T4e/T7/T8 CSV (DEC-066). Do not edit by hand.\n" + "\n\n".join([t7(), t4e(), t8()]) + "\n"
    print(txt[:600])
    if write:
        with open(OUT, "x", encoding="utf-8") as fh:
            fh.write(txt)


if __name__ == "__main__":
    main("write" in sys.argv)
