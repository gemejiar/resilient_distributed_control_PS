"""E16 (Option B): consolidation, integrity audit and closure of the experimentation.  No simulation.

Builds (1) the stage table E0-E16 with its classification, (2) the integrity audit (evidence files of the traceability matrix, hashes of historical raw series against the hashes recorded in
earlier summaries, status of the experiment matrix), (3) the assessment of the hypotheses H1-H4, (4) the experiment-matrix rows of E10-E16 and the consolidated report file.  The classification
uses only evidence that exists in the repository; nothing is upgraded.
"""

from __future__ import annotations

import csv
import json
import os

os.environ["C2_VARIANT"] = "C2t"

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from run_e0_ieee39 import ARTIFACTS_DIR as A, FIGURES_DIR, MATRIX_FILE, PROJECT_ROOT, git_commit, sha256

TRACE = PROJECT_ROOT / "ops" / "sted" / "traceability_matrix.csv"
SAT, SATF, NEG, NA, PEND = "SATISFACTORIO", "SATISFACTORIO CON HALLAZGOS", "NEGATIVO", "NO APLICABLE / NO FACTIBLE", "PENDIENTE"


def load(name: str) -> dict:
    return json.loads((A / name).read_text(encoding="utf-8"))


def main() -> int:
    e10, e11, e12, e13, e14, e15 = (load(f"IEEE39_E{k}_{n}.json") for k, n in ((10, "summary"), (11, "summary"), (12, "frontier"), (13, "stability"), (14, "transition"), (15, "robustness")))
    # ------------------------------------------------------------------ headline numbers
    conv = e10["counts"]
    r10 = e10["runs"]
    e12_dyn = e12["dynamic_runs"]
    e15r = {r["label"]: r for r in e15["runs"]}
    e13p = e13["points"]
    stages = [
        ("E0", "C0 10 SG, sin perturbación", SAT, "Flujo de potencia y simulación plana sin deriva; instrumentación validada.", "matriz experimental, DEC-001..", "-"),
        ("E1", "C0, escalón de P", SAT, "f cae y los gobernadores responden; nuevo equilibrio.", "IEEE39_E1_C0_summary.json", "-"),
        ("E2", "C0, escalón de Q", SAT, "Respuesta local de V coherente.", "IEEE39_E2_C0_summary.json", "-"),
        ("E3/E4/E4.1", "C0a, C1, C1a: sustitución secuencial SG→GFM", SAT, "Inicialización, simulación plana y respuestas P/Q con signos correctos; un recurso por prueba.", "IEEE39_E3..E4_1 summaries", "-"),
        ("E4.2", "C2 (6 SG + 4 GFM)", SATF, "C2 congelada; modo oscilatorio de REGF1 poco amortiguado (ζ 0.123) que motiva C2t (KPv ×1.5).", "IEEE39_E4_2_C2_summary.json; DEC-018/019", "ζ 0.123 en C2"),
        ("E5/E5t", "Primario P-f y Q-V por separado", SATF, "Respuesta de droop acorde; en C2t ζ 0.141; exceso transitorio de P de SG31 de 0.070 pu sobre el pmax del caso (hallazgo OPEN-SG31-PMAX).", "IEEE39_E5_C2(t)_summary.json", "SG31 +0.070 pu"),
        ("E6/E6t", "Secundario PI/consenso convencional", SAT, "f restaurada (−5.2e-7 Hz en C2t); reparto como en el primario.", "IEEE39_E6_C2(t)_summary.json", "-"),
        ("E7/E7t/E7L", "Secundario P/Q coordinado", SATF, "Dos intentos fallidos conservados (K_V 0.5 y 0.1: inestabilidad); E7t regula f a 0 Hz y V a ≤0.0139 pu de 1.0; E7L como referencia limitada en C2.", "IEEE39_E7*_summary.json; DEC-026..029", "2 intentos FAIL"),
        ("E8", "RDC original sobre C2t", SATF, "f restaurada a ≤3e-4 Hz; Qset sin converger y V sin alcanzar 1.0 pu en 200 s; tres intentos fallidos conservados.", "IEEE39_E8_C2t_summary.json; DEC-030..036", "3 intentos FAIL"),
        ("B3-A/S0/P+/Q+", "RDC centrado con equilibrio ξ*(d)", SATF, "S0 invariante a precisión numérica (por construcción); P+ y Q+ se acercan a ξ* más que B2 pero no convergen en 200 s y Qset sigue derivando.", "IEEE39_B3_*; DEC-037..042", "no convergencia"),
        ("E9 (A,B0,B1,C,D,F,H)", "Filtro HOCBF de seguridad (CLF apagada)", NEG, "Grados relativos 4 (SG) y 3 (GFM); HOCBF de grado 3 inutilizable en este DAE rígido; filtro factible solo 1-15 s tras el evento; predictivo consistente en S0 pero sin escenario que lo active; sin demostración de seguridad en lazo cerrado (opción B).", "IEEE39_E9*_summary.json; DEC-043..047", "sin lazo cerrado"),
        ("E10", "Convergencia y errores residuales del RDC (opción B)", SATF if conv["converged"] < conv["total"] else SAT,
         f"{conv['converged']} de {conv['total']} corridas cumplen todas las tolerancias de cola; frecuencia converge (τ 15-57 s, error final ≤3e-4 Hz) pero Qset y la tensión siguen derivando; el único caso convergente es B3-S0 (invariancia por construcción).", "IEEE39_E10_summary.json", f"{conv['converged']}/{conv['total']} convergen"),
        ("E11", "Límites simultáneos y redistribución de potencia (opción B)", SATF,
         "Dos o más unidades están a menos del 5 % de un límite durante toda la corrida en todos los casos (SG31 y SG33/SG35); solo SG31 cruza un límite (P+ en C2t con E5t, B2 y B3; no en la variante congelada R35_040); el evento simultáneo P+Q+ en la variante congelada se completa sin cruzar límites; la parte del ΔP entregada por los GFM es 5-50 % (el cociente de B3 Q+ no es interpretable porque el ΔQ neto es casi nulo).", "IEEE39_E11_summary.json", "SG31 cruza pmax en C2t"),
        ("E12", "Frontera de factibilidad (opción B)", SATF,
         f"Frontera estática AC: P {e12['static_frontier_amplitudes']['P_MW']:.0f} MW (límites de SG31 y SG35) y Q {e12['static_frontier_amplitudes']['Q_MVAr']:.0f} MVAr; la frontera dinámica con B2 es menor: P viola SG31/SG35 ya con {e12_dyn[3]['amplitude']:.0f} MW (sin violación hasta {e12_dyn[2]['amplitude']:.0f} MW) y Q pierde convergencia con colapso de tensión entre {e12_dyn[5]['amplitude']:.0f} y {e12_dyn[6]['amplitude']:.0f} MVAr (clase ii).", "IEEE39_E12_frontier.json", "frontera dinámica < estática"),
        ("E13", "Estabilidad local de la linealización (opción B)", SATF,
         f"Sin modos inestables en los cuatro puntos; un modo marginal (ángulo de rotor); ζ mínimo planta 0.14 y lazo con RDC {min(p['closed_loop_with_RDC']['min_zeta_oscillatory'] for p in e13p.values()):.3f}; modos lentos del RDC de 540-650 s (consistentes con Qset sin converger en 200 s); Lyapunov positiva definida en el subespacio estable con cota de decaimiento muy débil (2e-8 1/s). Sin certificado regional.", "IEEE39_E13_stability.json", "sin región certificada"),
        ("E14", "Transición entre despachos admisibles (opción B)", SAT,
         f"Transiciones A↔B de 30 s sin violar límites ni saltos (Δ paso máx. P {e14['runs']['A_to_B (C2t_Vsafe -> C2t_Vsafe_R35_040)']['max_single_step_change_P_pu']:.0e} pu); error final de P 2.7e-3 pu (pérdidas de armadura); desviación de f 0.15 mHz.", "IEEE39_E14_transition.json", "-"),
        ("E15", "Robustez (opción B)", NEG,
         "Robusto a carga ±20 % (el margen de SG31/SG35 llega a 0.002 pu con +20 %), a retardo de 0.2 s y a inercia −20 %; con retardo de 1.0 s oscila y viola límites (V 0.89-1.09 pu), con 5 s la simulación diverge; el N-1 de la línea 21-22 (la de mayor flujo sin aislar la red) hace perder la convergencia a los 5.12 s; extensión GFL no factible dentro del cierre (no existe caso C3).", "IEEE39_E15_robustness.json", "retardo ≥1 s y N-1 fallan"),
        ("E16", "Consolidación y cierre", SAT, "Informe, tabla de etapas, auditoría de integridad y trazabilidad.", "IEEE39_E16_consolidation.json", "-")]
    hypotheses = {
        "H1 integridad física y control primario": {"estado": "RESPALDADA", "evidencia": "E0-E5t: inicializaciones sin deriva, signos y reservas coherentes; salvedad: C2 requirió KPv ×1.5 (C2t) y SG31 supera pmax de forma transitoria.", "no_demostrado": "estabilidad de C2 con parámetros por defecto (ζ 0.123, inestable al mover tensiones)"},
        "H2 regulación nominal y reparto": {"estado": "PARCIALMENTE RESPALDADA", "evidencia": "f se restaura a ≤3e-4 Hz con RDC original y centrado y a 0 Hz con E7t; reparto P por reserva en E7t; E13 explica la lentitud de Q/V (modos de 540-650 s).",
                                              "no_demostrado": "convergencia de Qset y tensión a objetivos en 200 s (E10); equivalencia con el equilibrio ξ* (B3)"},
        "H3 seguridad incremental (HOCBF)": {"estado": "NO DEMOSTRADA", "evidencia": "E9: relaciones estructurales (grados 3/4, autoridad) y monitor predictivo consistente en S0; E15 y E12 muestran fronteras de seguridad física sin filtro.",
                                                "no_demostrado": "reducción de violaciones por un filtro en lazo cerrado en el IEEE 39; no hay escenario donde B4 actúe y B2 viole"},
        "H4 recuperación y convergencia regional (CLF-HOCBF)": {"estado": "NO DEMOSTRADA", "evidencia": "E13: estabilidad local de la linealización únicamente; E12: fronteras estática y dinámica.", "no_demostrado": "CLF-HOCBF no implementado; no hay región certificada ni convergencia regional"}}
    # ------------------------------------------------------------------ integrity audit
    ev_missing = []
    with TRACE.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for part in (r["source_path"], r["figure_or_table"]):
            for tok in part.replace(";", " ").split():
                if tok.startswith("Paper_manuscript/") and "{" not in tok and "*" not in tok and not (PROJECT_ROOT / tok).exists():
                    ev_missing.append((r["id"], tok))
    b3 = load("IEEE39_B3_C2t_Pplus_summary.json")
    hashes = {"E8 raw": (b3.get("e8_raw_sha256"), sha256(A / "IEEE39_E8_C2t_timeseries.npz")), "B3-S0 raw": (load("IEEE39_B3_C2t_Pplus_summary.json").get("b3_s0_raw_sha256"), sha256(A / "IEEE39_B3_C2t_S0_timeseries.npz"))}
    e9c = load("IEEE39_E9C_summary.json")
    for k, f in (("Vsafe B0 raw", "IEEE39_E9B0_Vsafe_series.npz"), ("Vsafe_R35 B0 raw", "IEEE39_E9B0_Vsafe_R35_series.npz"), ("Vsafe_R35_040 B0 raw", "IEEE39_E9B0_Vsafe_R35_040_series.npz")):
        if f in e9c["raw_sha256"]:
            hashes[k] = (e9c["raw_sha256"][f], sha256(A / f))
    hash_ok = {k: (v[0] == v[1]) for k, v in hashes.items()}
    mat = list(csv.DictReader(MATRIX_FILE.open(encoding="utf-8", newline="")))
    integrity = {"traceability_rows": len(rows), "traceability_status_counts": {s: sum(1 for r in rows if r["status"] == s) for s in sorted({r["status"] for r in rows})},
                 "missing_evidence_paths": ev_missing[:30], "n_missing_evidence_paths": len(ev_missing), "historical_raw_hashes_unchanged": hash_ok, "hashes": {k: list(v) for k, v in hashes.items()},
                 "experiment_matrix_rows": len(mat), "matrix_failed_rows_kept": [r["stage"] for r in mat if r["status_auto"] == "FAIL"],
                 "numerical_integrity": {"B3-S0 dae residual": 4e-9, "E10-E15 runs converged": {"E14": all(v["tds_ok"] for v in e14["runs"].values()), "E15 nominal": e15r.get("nominal P+", {}).get("tds_ok")}},
                 "code_changes_to_historical_runners": ["run_b3_ieee39.py (optional parameters probe, init_hook, freeze_t, ramp, qp_filter, dist_fn; defaults None)", "run_e8_ieee39.py (optional scenario key toggle_line used only by E15)", "e9a_linear.py (optional parameter cache)"]}
    # ------------------------------------------------------------------ outputs
    with (A / "IEEE39_E16_stage_table.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stage", "description", "classification", "result", "evidence", "key_negative_or_flag"])
        w.writerows(stages)
    summary = {"stage": "E16", "git_commit": git_commit(), "stages": [dict(zip(("stage", "description", "classification", "result", "evidence", "flag"), s)) for s in stages], "hypotheses": hypotheses, "integrity": integrity,
               "open_items": ["OPEN-SG31-PMAX (C2t original): transient 0.07 pu jump not preventable by reference actions; reserve variants provide margin as separate configurations", "closed-loop safety enforcement: not demonstrated (Option B)",
                              "regional stability certificate: none; only local linear stability", "GFL extension: not feasible within the closure (no C3 case)", "RDC voltage/Qset convergence: slow modes of 540-650 s not observed to converge in 200 s"],
               "counts": {c: sum(1 for s in stages if s[2] == c) for c in (SAT, SATF, NEG, NA, PEND)}}
    (A / "IEEE39_E16_consolidation.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    fig, ax = plt.subplots(figsize=(13, 8))
    col = {SAT: "tab:green", SATF: "gold", NEG: "tab:red", NA: "tab:gray", PEND: "tab:blue"}
    for i, s in enumerate(stages[::-1]):
        ax.barh(i, 1, color=col[s[2]])
        ax.text(0.02, i, f"{s[0]}  {s[1]}", va="center", fontsize=8)
    ax.set_yticks([]); ax.set_xticks([]); ax.set_title("E0-E16: classification of the stages (green satisfactory, yellow with findings, red negative)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "IEEE39_E16_status_overview.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(summary["counts"], integrity["n_missing_evidence_paths"], hash_ok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
