#!/usr/bin/env python
"""
P2-E5 correction -- fixed stability classifier (detrended oscillation
amplitude instead of raw peak-to-peak) + F+R grid recovery.

Problem being fixed (DEC-P2-011): the P2-E4/E5 classifier's
`freq_p2p_final<=10mHz` STABLE test could not distinguish a slow monotonic
frequency recovery (real system dynamics, present identically in NoFFC) from
a real persistent oscillation, mislabeling every R-only point of the
load_severe probe MARGINAL and blocking the automatic F+R grid.

Fix: fit a linear trend to frequency(t) over the final 1s window, work with
the DETRENDED residual's peak-to-peak amplitude instead of the raw one, and
require BOTH persistence (oscillation not decaying within the window) and
multiple sign reversals of Pcommand before calling something a limit cycle.

Order of operations (per user instruction):
  1. Define the corrected classifier.
  2. Validate it against 4 known historical trajectories (regression suite) --
     reusing EXISTING trajectory data wherever possible; only ONE new
     simulation is run (Case D, the Kf=Kr=1.0x F+R combination at Tc=100ms,
     which was never logged with a full trajectory before -- DEC-P2-005 only
     recorded scalar metrics for it).
  3. If the regression suite does not pass 4/4, STOP and report (do not
     proceed to reclassification or the F+R grid).
  4. Reclassify the EXISTING F-only/R-only sweeps (no new simulations) into
     `_reclassified.csv` files -- originals are never overwritten.
  5. Determine which Kf/Kr multipliers are STABLE (corrected) in BOTH DESIGN
     probes, and build a small (<=16) F+R grid from them, run it, and analyze
     with a Pareto framework (no scalar-weighted single winner).
  6. For load_severe, also capture local BESS-bus RoCoF vs worst-system RoCoF
     (p2_common.run_physical_scenario_tc now logs this at full resolution).

Kf0/Kr0, Pmax, Tc(=100ms diagnostic reference), tip, BusROCOF/Tf/Tw/Tr, and
BESS location are all UNCHANGED. No TD3, no P2-T*, no validation.
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc, TD, TF_INITIAL, F0_HZ

PMAX_MW = 293.4
KF0 = PMAX_MW / 0.5
KR0 = PMAX_MW / 1.0
TC_REF_S = 0.100
TC_P2E5_DIAGNOSTIC_REFERENCE_ONLY = True
TSTEP = 0.005
WIN_THRESHOLD = 0.10
FINAL_WINDOW_START_S = TF_INITIAL - 1.0  # 5.0s
MAX_FR_GRID = 16

SCENARIOS = [
    dict(label='gen_severe', kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00),
    dict(label='load_severe', kind='load', bus=20, alpha_L=0.50, lambda_L=1.00),
]

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories')
OUT_FIG = os.path.join('Paper_2', 'artifacts', 'figures')
for d in (OUT_DIAG, OUT_TRAJ, OUT_FIG):
    os.makedirs(d, exist_ok=True)

# --- Corrected classifier thresholds (explicit, documented, applied
# identically everywhere -- Section 3 of the user's instruction) ---
STABLE_DETRENDED_P2P_MAX_HZ = 0.010
STABLE_SIGN_REV_MAX = 1
STABLE_SAT_FRAC_MAX = 0.05
LIMIT_CYCLE_DETRENDED_P2P_MIN_HZ = 0.030
LIMIT_CYCLE_SIGN_REV_MIN = 3
LIMIT_CYCLE_PERSISTENCE_MIN = 0.5   # second-half/first-half detrended p2p ratio
LIMIT_CYCLE_SAT_FRAC_MIN = 0.30     # alternative sufficient condition (repeated saturation)


def fit_trend_detrend(t_win, x_win):
    if len(t_win) < 2:
        return 0.0, np.zeros_like(x_win)
    slope, intercept = np.polyfit(t_win, x_win, 1)
    trend = slope * t_win + intercept
    return float(slope), x_win - trend


def persistence_ratio(detrended):
    n = len(detrended)
    if n < 4:
        return 0.0
    half = n // 2
    p2p_first = np.ptp(detrended[:half])
    p2p_second = np.ptp(detrended[half:])
    return float(p2p_second / max(p2p_first, 1e-6))


def sign_reversals(x, eps=1e-6):
    s = np.sign(np.where(np.abs(x) < eps, 0.0, x))
    nz = s[s != 0]
    if len(nz) < 2:
        return 0
    return int(np.sum(np.diff(nz) != 0))


def classify_v2(tds_success, detrended_p2p, sign_rev_final, sat_frac, persist_ratio):
    if not tds_success:
        return 'NUMERICAL_FAILURE'
    is_stable = (detrended_p2p <= STABLE_DETRENDED_P2P_MAX_HZ and
                 sign_rev_final <= STABLE_SIGN_REV_MAX and
                 sat_frac < STABLE_SAT_FRAC_MAX)
    is_limit_cycle = (detrended_p2p >= LIMIT_CYCLE_DETRENDED_P2P_MIN_HZ and
                       sign_rev_final >= LIMIT_CYCLE_SIGN_REV_MIN and
                       (persist_ratio >= LIMIT_CYCLE_PERSISTENCE_MIN or sat_frac >= LIMIT_CYCLE_SAT_FRAC_MIN))
    if is_limit_cycle:
        return 'LIMIT_CYCLE'
    if is_stable:
        return 'STABLE'
    return 'MARGINAL'


def analyze_trace_v2(t, f, pcmd1, pcmd2, tds_success, saturation_fraction):
    window = t >= FINAL_WINDOW_START_S
    t_win = t[window]
    f_win = f[window]
    slope, detrended = fit_trend_detrend(t_win, f_win)
    detrended_p2p = float(np.ptp(detrended)) if len(detrended) else float('nan')
    persist = persistence_ratio(detrended)
    sign_rev = max(sign_reversals(pcmd1[window]), sign_reversals(pcmd2[window]))
    label = classify_v2(tds_success, detrended_p2p, sign_rev, saturation_fraction, persist)
    return dict(frequency_final_slope=slope, detrended_frequency_p2p=detrended_p2p,
                persistence_ratio=persist, sign_reversals_final_window=sign_rev,
                classification_v2=label)


# ============================================================
# STEP 1: regression suite against known historical trajectories
# ============================================================

def run_regression_suite():
    rows = []

    # CASE A: load_severe NoFFC (existing trace, p2e5 npz)
    d5 = np.load(os.path.join(OUT_TRAJ, 'p2e5_physical_structure_traces.npz'))
    t = d5['load_severe_NoFFC__t']
    f = d5['load_severe_NoFFC__f_worst_hz']
    pc1 = d5['load_severe_NoFFC__p_command1_mw']
    pc2 = d5['load_severe_NoFFC__p_command2_mw']
    res = analyze_trace_v2(t, f, pc1, pc2, True, 0.0)
    rows.append(dict(case_id='A', description='load_severe NoFFC (existing trace)',
                      expected='NOT LIMIT_CYCLE', **res))

    # CASE B: load_severe R-only, Kr=0.05x (existing trace, previously MARGINAL, 0 sign reversals)
    t = d5['load_severe_Ronly_mult0.05__t']
    f = d5['load_severe_Ronly_mult0.05__f_worst_hz']
    pc1 = d5['load_severe_Ronly_mult0.05__p_command1_mw']
    pc2 = d5['load_severe_Ronly_mult0.05__p_command2_mw']
    kr_sweep = pd.read_csv(os.path.join(OUT_DIAG, 'p2e5_kr_sweep.csv'))
    row_b = kr_sweep[(kr_sweep['scenario'] == 'load_severe') &
                      (np.isclose(kr_sweep['k_r'], 0.05 * KR0))].iloc[0]
    res = analyze_trace_v2(t, f, pc1, pc2, True, float(row_b['saturation_fraction']))
    rows.append(dict(case_id='B', description='load_severe R-only Kr=0.05x (existing trace, prev. MARGINAL)',
                      expected='NOT LIMIT_CYCLE', **res))

    # CASE C: gen_severe Tc=50ms sustained bang-bang (existing trace, P2-E4 local sweep)
    d4b = np.load(os.path.join(OUT_TRAJ, 'p2e4_tc_local_sweep_traces.npz'))
    t = d4b['gen_severe_Tc50__t']
    f = d4b['gen_severe_Tc50__f_worst_hz']
    pc1 = d4b['gen_severe_Tc50__p_command1_mw']
    pc2 = d4b['gen_severe_Tc50__p_command2_mw']
    tc_sweep = pd.read_csv(os.path.join(OUT_DIAG, 'p2e4_tc_local_sweep.csv'))
    row_c = tc_sweep[(tc_sweep['scenario'] == 'gen_severe') & (tc_sweep['Tc_ms'] == 50)].iloc[0]
    res = analyze_trace_v2(t, f, pc1, pc2, True, float(row_c['saturation_fraction']))
    rows.append(dict(case_id='C', description='gen_severe Tc=50ms sustained bang-bang (existing trace)',
                      expected='LIMIT_CYCLE', **res))

    # CASE D: load_severe F+R aggressive (Kf=Kr=1.0x, Tc=100ms) -- NOT previously logged with a
    # full trajectory (DEC-P2-005 only recorded scalar metrics for this exact combination via the
    # older run_physical_scenario() driver). ONE new simulation, explicitly required by this
    # regression suite -- not a repeat of F-only/R-only.
    r = run_physical_scenario_tc(kind='load', bus=20, alpha_L=0.50, lambda_L=1.00,
                                  p_max_bess_mw=PMAX_MW, k_f=1.0 * KF0, k_r=1.0 * KR0,
                                  tc=TC_REF_S, tstep=TSTEP, controller='physical', tf=TF_INITIAL)
    res = analyze_trace_v2(r['t'], r['f_worst_hz'], r['p_command1_mw'], r['p_command2_mw'],
                            r['tds_success'], r['saturation_fraction'])
    # NOTE (DEC-P2-013): Case D's expected outcome was updated from LIMIT_CYCLE to
    # NOT LIMIT_CYCLE. The dedicated tstep convergence study (p2e5c, this exact
    # Kf=Kr=1.0x/load_severe/Tc=100ms configuration, INDEPENDENT of this
    # classifier) showed saturation_fraction=0.0000 identically at
    # tstep=10/5/2.5/1ms and <1% relative change in df_nadir/RoCoF_max between
    # 5ms and finer steps -- the case is genuinely STABLE at the now-frozen
    # tstep=5ms; the original LIMIT_CYCLE expectation came from the old driver's
    # unconverged tstep=16.67ms result (DEC-P2-005/DEC-P2-012). This case now
    # regression-tests that the converged-tstep result is correctly recognized
    # as stable, not that it reproduces the stale coarse-tstep finding.
    rows.append(dict(case_id='D', description='load_severe F+R aggressive Kf=Kr=1.0x, Tc=100ms '
                      '(1 NEW sim @ tstep=5ms frozen; DEC-P2-013 independently confirmed STABLE here)',
                      expected='NOT LIMIT_CYCLE', **res))
    case_d_trace = dict(t=r['t'], f_worst_hz=r['f_worst_hz'], rocof_worst_hz_s=r['rocof_worst_hz_s'],
                         p_command1_mw=r['p_command1_mw'], p_command2_mw=r['p_command2_mw'],
                         p_delivered1_mw=r['p_delivered1_mw'], p_delivered2_mw=r['p_delivered2_mw'])

    df = pd.DataFrame(rows)
    df['pass'] = df.apply(lambda row: (row['classification_v2'] != 'LIMIT_CYCLE') if row['expected'] == 'NOT LIMIT_CYCLE'
                           else (row['classification_v2'] == 'LIMIT_CYCLE'), axis=1)
    out_csv = os.path.join(OUT_DIAG, 'p2_stability_classifier_regression.csv')
    df.to_csv(out_csv, index=False)
    print(f"=== Classifier v2 regression suite ===")
    for _, row in df.iterrows():
        print(f"  Case {row['case_id']}: {row['description']}")
        print(f"    detrended_p2p={row['detrended_frequency_p2p']*1000:.2f}mHz "
              f"sign_rev={row['sign_reversals_final_window']} persist={row['persistence_ratio']:.2f} "
              f"slope={row['frequency_final_slope']*1000:.3f}mHz/s "
              f"-> {row['classification_v2']} (expected {row['expected']}) "
              f"{'PASS' if row['pass'] else 'FAIL'}")
    print(f"Saved: {out_csv}")
    all_pass = bool(df['pass'].all())
    print(f"\nRegression suite: {'4/4 PASS' if all_pass else 'FAILED -- STOPPING per Section 17'}")
    return all_pass, case_d_trace


# ============================================================
# STEP 2: reclassify existing F-only/R-only sweeps (no new sims)
# ============================================================

def reclassify_existing_sweeps():
    d5 = np.load(os.path.join(OUT_TRAJ, 'p2e5_physical_structure_traces.npz'))

    def reclass_df(csv_name, condition_prefix, mult_col, divisor):
        df = pd.read_csv(os.path.join(OUT_DIAG, csv_name))
        new_cols = {c: [] for c in ['frequency_final_slope', 'detrended_frequency_p2p',
                                     'persistence_ratio', 'sign_reversals_final_window_v2',
                                     'classification_v2']}
        for _, row in df.iterrows():
            mult = row[mult_col] / divisor
            key = f"{row['scenario']}_{condition_prefix}_mult{mult:g}"
            key_variants = [key, key.replace(f'mult{mult:g}', f'mult{mult}')]
            found = None
            for kv in key_variants:
                if f"{kv}__t" in d5.files:
                    found = kv
                    break
            if found is None:
                # fall back: search by matching multiplier value in available keys
                for fk in d5.files:
                    if fk.startswith(f"{row['scenario']}_{condition_prefix}_mult") and fk.endswith('__t'):
                        cand_mult = float(fk.split('mult')[1].split('__')[0])
                        if np.isclose(cand_mult, mult):
                            found = fk[:-len('__t')]
                            break
            assert found is not None, f"trace not found for {key}"
            t = d5[f"{found}__t"]; f = d5[f"{found}__f_worst_hz"]
            pc1 = d5[f"{found}__p_command1_mw"]; pc2 = d5[f"{found}__p_command2_mw"]
            res = analyze_trace_v2(t, f, pc1, pc2, bool(row['TDS_success']), float(row['saturation_fraction']))
            new_cols['frequency_final_slope'].append(res['frequency_final_slope'])
            new_cols['detrended_frequency_p2p'].append(res['detrended_frequency_p2p'])
            new_cols['persistence_ratio'].append(res['persistence_ratio'])
            new_cols['sign_reversals_final_window_v2'].append(res['sign_reversals_final_window'])
            new_cols['classification_v2'].append(res['classification_v2'])
        for c, vals in new_cols.items():
            df[c] = vals
        return df

    df_f = reclass_df('p2e5_kf_sweep.csv', 'Fonly', 'k_f', KF0)
    df_f['k_f_mult'] = df_f['k_f'] / KF0
    df_r = reclass_df('p2e5_kr_sweep.csv', 'Ronly', 'k_r', KR0)
    df_r['k_r_mult'] = df_r['k_r'] / KR0

    df_f.to_csv(os.path.join(OUT_DIAG, 'p2e5_kf_sweep_reclassified.csv'), index=False)
    df_r.to_csv(os.path.join(OUT_DIAG, 'p2e5_kr_sweep_reclassified.csv'), index=False)
    print("\n=== Reclassified F-only ===")
    print(df_f[['scenario', 'k_f_mult', 'classification', 'classification_v2', 'detrended_frequency_p2p']].to_string(index=False))
    print("\n=== Reclassified R-only ===")
    print(df_r[['scenario', 'k_r_mult', 'classification', 'classification_v2', 'detrended_frequency_p2p']].to_string(index=False))
    print(f"\nSaved: p2e5_kf_sweep_reclassified.csv, p2e5_kr_sweep_reclassified.csv (originals untouched)")
    return df_f, df_r


# ============================================================
# STEP 3: build & run F+R grid from jointly-stable(v2) multipliers
# ============================================================

def build_fr_grid(df_f, df_r):
    stable_f = {}
    stable_r = {}
    for scenario in SCENARIOS:
        label = scenario['label']
        sf = df_f[(df_f['scenario'] == label) & (df_f['classification_v2'] == 'STABLE')]
        sr = df_r[(df_r['scenario'] == label) & (df_r['classification_v2'] == 'STABLE')]
        stable_f[label] = set(np.round(sf['k_f_mult'].values, 4))
        stable_r[label] = set(np.round(sr['k_r_mult'].values, 4))
    common_f = sorted(stable_f[SCENARIOS[0]['label']] & stable_f[SCENARIOS[1]['label']])
    common_r = sorted(stable_r[SCENARIOS[0]['label']] & stable_r[SCENARIOS[1]['label']])
    print(f"\nKf multipliers STABLE (v2) in BOTH probes: {common_f}")
    print(f"Kr multipliers STABLE (v2) in BOTH probes: {common_r}")

    if not common_f or not common_r:
        print("F+R grid cannot be built -- empty intersection even after correction.")
        return [], common_f, common_r

    def reps(mults):
        mults = sorted(mults)
        if len(mults) <= 3:
            return mults
        return sorted({mults[0], mults[len(mults) // 2], mults[-1]})

    f_reps = reps(common_f)
    r_reps = reps(common_r)
    grid = [(fm, rm) for fm in f_reps for rm in r_reps]

    # add up to 2 boundary probes near the edge of the stable region, if room remains
    all_f_mults = sorted(set(df_f['k_f_mult'].values))
    all_r_mults = sorted(set(df_r['k_r_mult'].values))
    if common_f and common_r and len(grid) < MAX_FR_GRID:
        f_edge = max(common_f)
        r_above = [m for m in all_r_mults if m > max(common_r)]
        if r_above and (f_edge, min(r_above)) not in grid:
            grid.append((f_edge, min(r_above)))
        r_edge = max(common_r)
        f_above = [m for m in all_f_mults if m > max(common_f)]
        if f_above and (min(f_above), r_edge) not in grid and len(grid) < MAX_FR_GRID:
            grid.append((min(f_above), r_edge))

    grid = grid[:MAX_FR_GRID]
    print(f"F+R grid ({len(grid)} combinations): {grid}")
    return grid, common_f, common_r


def run_fr_grid(grid):
    rows = []
    traces = {}
    for scenario in SCENARIOS:
        for fm, rm in grid:
            r = run_physical_scenario_tc(
                kind=scenario['kind'],
                gen=scenario.get('gen'), rho=scenario.get('rho'),
                bus=scenario.get('bus'), alpha_L=scenario.get('alpha_L'),
                lambda_L=scenario['lambda_L'], p_max_bess_mw=PMAX_MW,
                k_f=fm * KF0, k_r=rm * KR0, tc=TC_REF_S, tstep=TSTEP,
                controller='physical', tf=TF_INITIAL)
            res = analyze_trace_v2(r['t'], r['f_worst_hz'], r['p_command1_mw'], r['p_command2_mw'],
                                    r['tds_success'], r['saturation_fraction'])
            row = dict(scenario=scenario['label'], k_f_mult=fm, k_r_mult=rm,
                       k_f=fm * KF0, k_r=rm * KR0, Tc_ms=TC_REF_S * 1000, Pmax_MW=PMAX_MW,
                       classification=res['classification_v2'],
                       df_nadir_hz=r['df_nadir_hz'], RoCoF_max_hz_s=r['rocof_max_hz_s'],
                       Ppeak_MW=r['p_peak_mw'], saturation_fraction=r['saturation_fraction'],
                       detrended_frequency_p2p=res['detrended_frequency_p2p'],
                       frequency_final_slope=res['frequency_final_slope'],
                       sign_reversals_final_window=res['sign_reversals_final_window'],
                       command_delivered_max_error_MW=r['command_delivered_max_error_mw'],
                       command_delivered_rms_error_MW=r['command_delivered_rms_error_mw'],
                       TDS_success=bool(r['tds_success']))
            rows.append(row)
            key = f"{scenario['label']}_FR_f{fm:g}_r{rm:g}"
            traces[key] = dict(t=r['t'], f_worst_hz=r['f_worst_hz'], rocof_worst_hz_s=r['rocof_worst_hz_s'],
                                p_command1_mw=r['p_command1_mw'], p_command2_mw=r['p_command2_mw'],
                                p_delivered1_mw=r['p_delivered1_mw'], p_delivered2_mw=r['p_delivered2_mw'],
                                f_bess1_hz=r['f_bess1_hz'], rocof_bess1_hz_s=r['rocof_bess1_hz_s'],
                                f_bess2_hz=r['f_bess2_hz'], rocof_bess2_hz_s=r['rocof_bess2_hz_s'])
            print(f"  [{scenario['label']:12s} Kf={fm:.2f}x Kr={rm:.2f}x] class={row['classification']:14s} "
                  f"df_nadir={row['df_nadir_hz']:+.4f}Hz RoCoF_max={row['RoCoF_max_hz_s']:.3f}Hz/s "
                  f"sat={row['saturation_fraction']:.3f} tds_ok={row['TDS_success']}")
    return pd.DataFrame(rows), traces


def add_improvement_cols(df, noffc_ref):
    for scenario in SCENARIOS:
        label = scenario['label']
        base_f = noffc_ref[label]['df_nadir']
        base_r = noffc_ref[label]['rocof_max']
        mask = df['scenario'] == label
        df.loc[mask, 'I_f_vs_NoFFC'] = (np.abs(base_f) - np.abs(df.loc[mask, 'df_nadir_hz'])) / np.abs(base_f)
        df.loc[mask, 'I_r_vs_NoFFC'] = (base_r - df.loc[mask, 'RoCoF_max_hz_s']) / base_r
    return df


def get_noffc_ref():
    d5 = np.load(os.path.join(OUT_TRAJ, 'p2e5_physical_structure_traces.npz'))
    ref = {}
    for scenario in SCENARIOS:
        f = d5[f"{scenario['label']}_NoFFC__f_worst_hz"]
        rocof = d5[f"{scenario['label']}_NoFFC__rocof_worst_hz_s"]
        ref[scenario['label']] = dict(df_nadir=float(np.min(f) - F0_HZ), rocof_max=float(np.max(rocof)))
    return ref


def local_vs_system_rocof_load_severe(traces, df_fr):
    """Section 12: for load_severe, compare local BESS-bus RoCoF against the
    worst-system RoCoF, to check whether R-only's null effect is an
    observability limitation (small local RoCoF despite large system-wide
    RoCoF) rather than a control-law problem."""
    rows = []
    for key, tr in traces.items():
        if not key.startswith('load_severe_FR'):
            continue
        rows.append(dict(
            key=key,
            rocof_worst_system_max=float(np.max(tr['rocof_worst_hz_s'])),
            rocof_bess1_max=float(np.max(np.abs(tr['rocof_bess1_hz_s']))),
            rocof_bess2_max=float(np.max(np.abs(tr['rocof_bess2_hz_s']))),
        ))
    df = pd.DataFrame(rows)
    print("\n=== load_severe: local BESS-bus RoCoF vs worst-system RoCoF ===")
    print(df.to_string(index=False))
    return df


def make_figures(df_fr, common_f, common_r, traces, noffc_ref, local_rocof_df):
    if df_fr is None or len(df_fr) == 0:
        return
    class_colors = {'STABLE': 'C2', 'MARGINAL': 'C1', 'LIMIT_CYCLE': 'C3', 'NUMERICAL_FAILURE': 'k'}

    # Fig A: stability map Kf vs Kr
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, scenario in zip(axes, SCENARIOS):
        sub = df_fr[df_fr['scenario'] == scenario['label']]
        for _, row in sub.iterrows():
            ax.scatter(row['k_f_mult'], row['k_r_mult'], color=class_colors[row['classification']], s=120)
        ax.set_xlabel('Kf / Kf0'); ax.set_ylabel('Kr / Kr0'); ax.set_title(scenario['label'])
        ax.grid(True, linestyle=':', alpha=0.5)
    handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=v, markersize=10, label=k)
               for k, v in class_colors.items()]
    fig.legend(handles=handles, loc='upper center', ncol=4, fontsize=8)
    fig.suptitle('P2-E5 corrected Fig A: F+R stability map')
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(os.path.join(OUT_FIG, 'p2e5_fr_figA_stability_map.png'), dpi=200)
    plt.close(fig)

    # Fig B/C: I_f and I_r maps
    for metric, label_txt, fname in [('I_f_vs_NoFFC', 'I_f (%)', 'p2e5_fr_figB_if_map.png'),
                                      ('I_r_vs_NoFFC', 'I_r (%)', 'p2e5_fr_figC_ir_map.png')]:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        for ax, scenario in zip(axes, SCENARIOS):
            sub = df_fr[df_fr['scenario'] == scenario['label']]
            sc = ax.scatter(sub['k_f_mult'], sub['k_r_mult'], c=sub[metric] * 100, cmap='RdYlGn', s=140,
                             vmin=-20, vmax=20)
            ax.set_xlabel('Kf / Kf0'); ax.set_ylabel('Kr / Kr0'); ax.set_title(scenario['label'])
            fig.colorbar(sc, ax=ax, label=label_txt)
        fig.suptitle(f'P2-E5 corrected: {label_txt} over Kf/Kr grid')
        fig.tight_layout()
        fig.savefig(os.path.join(OUT_FIG, fname), dpi=200)
        plt.close(fig)

    # Fig D: Pareto I_f vs I_r
    fig, ax = plt.subplots(figsize=(6, 5))
    for scenario in SCENARIOS:
        sub = df_fr[(df_fr['scenario'] == scenario['label']) & (df_fr['classification'] == 'STABLE')]
        ax.scatter(sub['I_f_vs_NoFFC'] * 100, sub['I_r_vs_NoFFC'] * 100, label=scenario['label'], s=70)
    ax.axhline(WIN_THRESHOLD * 100, color='gray', linestyle=':'); ax.axvline(WIN_THRESHOLD * 100, color='gray', linestyle=':')
    ax.set_xlabel('I_f vs NoFFC (%)'); ax.set_ylabel('I_r vs NoFFC (%)')
    ax.set_title('P2-E5 corrected Fig D: Pareto map (STABLE points only)')
    ax.legend(fontsize=8); ax.grid(True, linestyle=':', alpha=0.6)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_FIG, 'p2e5_fr_figD_pareto.png'), dpi=200)
    plt.close(fig)

    # Fig E/F: representative stable / unstable trajectories
    stable_rows = df_fr[df_fr['classification'] == 'STABLE']
    unstable_rows = df_fr[df_fr['classification'] == 'LIMIT_CYCLE']
    for rows_df, fname, title in [(stable_rows, 'p2e5_fr_figE_stable_trajectory.png', 'stable'),
                                   (unstable_rows, 'p2e5_fr_figF_unstable_trajectory.png', 'unstable')]:
        if len(rows_df) == 0:
            continue
        row = rows_df.iloc[0]
        key = f"{row['scenario']}_FR_f{row['k_f_mult']:g}_r{row['k_r_mult']:g}"
        tr = traces[key]
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.plot(tr['t'], tr['f_worst_hz'], 'C0-')
        ax.set_xlabel('Time (s)'); ax.set_ylabel('Worst-bus frequency (Hz)')
        ax.set_title(f"P2-E5 corrected: representative {title} F+R, {row['scenario']} "
                     f"(Kf={row['k_f_mult']:.2f}x, Kr={row['k_r_mult']:.2f}x)")
        ax.grid(True, linestyle=':', alpha=0.6)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT_FIG, fname), dpi=200)
        plt.close(fig)

    # Fig G: load_severe local BESS RoCoF vs worst-system RoCoF
    if local_rocof_df is not None and len(local_rocof_df):
        fig, ax = plt.subplots(figsize=(7, 4))
        x = np.arange(len(local_rocof_df))
        ax.bar(x - 0.25, local_rocof_df['rocof_worst_system_max'], width=0.25, label='worst-system')
        ax.bar(x, local_rocof_df['rocof_bess1_max'], width=0.25, label='local BESS bus 13')
        ax.bar(x + 0.25, local_rocof_df['rocof_bess2_max'], width=0.25, label='local BESS bus 12')
        ax.set_xticks(x); ax.set_xticklabels(local_rocof_df['key'], rotation=60, ha='right', fontsize=6)
        ax.set_ylabel('|RoCoF| max (Hz/s)')
        ax.set_title('P2-E5 corrected Fig G: load_severe local vs worst-system RoCoF')
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT_FIG, 'p2e5_fr_figG_local_vs_system_rocof.png'), dpi=200)
        plt.close(fig)

    print(f"Saved figures to {OUT_FIG}")


def main():
    all_pass, case_d_trace = run_regression_suite()
    if not all_pass:
        print("\nSTOP CONDITION (Section 17): classifier did not reproduce all 4 historical cases. "
              "Not proceeding to reclassification or the F+R grid.")
        return

    df_f, df_r = reclassify_existing_sweeps()
    grid, common_f, common_r = build_fr_grid(df_f, df_r)
    if not grid:
        print("\nSTOP: no F+R grid could be built (empty stable intersection even after correction).")
        return

    print(f"\n=== Running F+R grid ({len(grid)} combos x {len(SCENARIOS)} probes = "
          f"{len(grid)*len(SCENARIOS)} simulations) ===")
    df_fr, traces = run_fr_grid(grid)
    traces['regression_caseD_load_severe_aggressive_Kf1_Kr1'] = case_d_trace

    noffc_ref = get_noffc_ref()
    df_fr = add_improvement_cols(df_fr, noffc_ref)

    out_csv = os.path.join(OUT_DIAG, 'p2e5_kf_kr_grid.csv')
    df_fr.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv} ({len(df_fr)} rows)")

    out_npz = os.path.join(OUT_TRAJ, 'p2e5_fr_grid_traces.npz')
    flat = {}
    for key, d in traces.items():
        for name, arr in d.items():
            flat[f"{key}__{name}"] = arr
    np.savez(out_npz, **flat)
    print(f"Saved: {out_npz}")

    local_rocof_df = local_vs_system_rocof_load_severe(traces, df_fr)
    local_rocof_df.to_csv(os.path.join(OUT_DIAG, 'p2e5_load_severe_local_vs_system_rocof.csv'), index=False)

    print("\n=== F+R grid results ===")
    print(df_fr[['scenario', 'k_f_mult', 'k_r_mult', 'classification', 'I_f_vs_NoFFC', 'I_r_vs_NoFFC',
                 'saturation_fraction']].to_string(index=False))

    # Pareto frontier per scenario (STABLE points only)
    print("\n=== Pareto frontier (STABLE points, per scenario) ===")
    for scenario in SCENARIOS:
        sub = df_fr[(df_fr['scenario'] == scenario['label']) & (df_fr['classification'] == 'STABLE')].copy()
        if len(sub) == 0:
            print(f"  {scenario['label']}: no STABLE F+R points")
            continue
        pareto = []
        for _, row in sub.iterrows():
            dominated = ((sub['I_f_vs_NoFFC'] >= row['I_f_vs_NoFFC']) &
                         (sub['I_r_vs_NoFFC'] >= row['I_r_vs_NoFFC']) &
                         ((sub['I_f_vs_NoFFC'] > row['I_f_vs_NoFFC']) | (sub['I_r_vs_NoFFC'] > row['I_r_vs_NoFFC']))).any()
            if not dominated:
                pareto.append(row)
        for row in pareto:
            print(f"  {scenario['label']}: Kf={row['k_f_mult']:.2f}x Kr={row['k_r_mult']:.2f}x "
                  f"I_f={row['I_f_vs_NoFFC']*100:+.1f}% I_r={row['I_r_vs_NoFFC']*100:+.1f}%")

    make_figures(df_fr, common_f, common_r, traces, noffc_ref, local_rocof_df)


if __name__ == '__main__':
    main()
