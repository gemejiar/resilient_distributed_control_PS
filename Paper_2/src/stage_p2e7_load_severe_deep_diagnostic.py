#!/usr/bin/env python
"""
P2-E7 -- load_severe deep diagnostic: verify the disturbance implementation
itself, then compare NoFFC / F+R (frozen Kf,Kr,Tc,Pmax at the new BESS
locations 16,20) / open-loop positive injection, with full signal logging
(local BESS frequency, worst-bus frequency, COI-proxy frequency, RoCoF,
delivered power).

BESS buses (16,20), Pmax, Tc, tstep, Kf, Kr, BusROCOF/Tf/Tw/Tr all held fixed
at their frozen values (DEC-P2-018). No TD3, no validation, no P2-T*.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import (BASE_CASE, GEN_BUSES, BESS_ADMISSIBLE_BUSES, ROCOF_PARAMS, AREA_GENS,
                        K_FROZEN, TD, F0_HZ, BESS_BUS_1, BESS_BUS_2, TF_INITIAL,
                        run_physical_scenario_tc)
import andes

PMAX_MW = 293.4
KF0 = PMAX_MW / 0.5
KR0 = PMAX_MW / 1.0
KF = 1.0 * KF0
KR = 0.75 * KR0
TC_S = 0.100
TSTEP = 0.005
ALPHA_L = 0.50
LOAD_BUS = 20

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'diagnostics')
OUT_TRAJ = os.path.join('Paper_2', 'artifacts', 'trajectories')
os.makedirs(OUT_DIAG, exist_ok=True)
os.makedirs(OUT_TRAJ, exist_ok=True)


def verify_disturbance_mechanics():
    """Step 3: confirm exactly how load_severe is implemented -- affected
    load, initial MW, applied increment, event instant, actual MW before/
    after, total load before/after. No BESS involved -- pure disturbance
    verification."""
    print("=== Step 3: load_severe disturbance mechanics verification ===")
    ss = andes.load(BASE_CASE, setup=False, no_output=True, default_config=True)
    for b in GEN_BUSES:
        ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))
    pq_idx = ss.PQ.find_idx(keys='bus', values=[LOAD_BUS])[0]
    alter_idx = ss.add('Alter', dict(model='PQ', dev=pq_idx, src='Ppf', t=TD, method='+', amount=0.0))
    ss.setup()

    ss.PQ.config.p2p = 1.0; ss.PQ.config.p2i = 0.0; ss.PQ.config.p2z = 0.0
    ss.PQ.config.q2q = 1.0; ss.PQ.config.q2i = 0.0; ss.PQ.config.q2z = 0.0
    ss.PQ.config.pq2z = 0
    ss.Toggle.u.v[:] = 0
    uids = ss.GENROU.idx2uid(AREA_GENS)
    ss.GENROU.M.v[uids] = ss.GENROU.M.v[uids] * K_FROZEN
    ss.GENROU.M.vin[uids] = ss.GENROU.M.vin[uids] * K_FROZEN

    pq_uid = list(ss.PQ.bus.v).index(LOAD_BUS)
    load_p0_nom_pu = float(ss.PQ.p0.v[pq_uid])
    print(f"PQ_9 (bus {LOAD_BUS}) nominal P0 = {load_p0_nom_pu:.4f} pu = {load_p0_nom_pu*100:.2f} MW")

    alter_uid = ss.Alter.idx2uid([alter_idx])[0]
    ss.Alter.amount.v[alter_uid] = ALPHA_L * load_p0_nom_pu
    increment_mw = ALPHA_L * load_p0_nom_pu * 100.0
    print(f"alpha_L = {ALPHA_L} -> increment applied = {increment_mw:.2f} MW "
          f"(Alter: model=PQ, dev=PQ_9, src=Ppf, t={TD}s, method='+')")

    ss.TDS.config.tstep = TSTEP
    ss.TDS.config.fixt = 1
    ss.TDS.config.method = 'trapezoid'
    ss.TDS.config.save_every = 0
    ss.TDS.config.no_tqdm = 1

    ss.PFlow.run()
    total_load_before_mw = float(np.sum(ss.PQ.p0.v)) * 100.0
    total_gen_before_mw = float(np.sum(ss.PV.p0.v)) * 100.0
    ss.TDS.init()

    dae = ss.dae
    tds = ss.TDS
    n_steps = int(round(TF_INITIAL / TSTEP))
    step_at_td = int(round(TD / TSTEP))
    p_load_before = p_load_after = None

    for step in range(n_steps):
        if step == step_at_td - 1:
            p_load_before = float(ss.PQ.Ppf.v[pq_uid]) * 100.0
        tds.do_switch()
        tds.calc_h()
        if tds.itm_step():
            dae.t += tds.h
        if step == step_at_td:
            p_load_after = float(ss.PQ.Ppf.v[pq_uid]) * 100.0
            total_load_after_mw = float(np.sum(ss.PQ.Ppf.v)) * 100.0
            break

    print(f"\nPQ_9.Ppf immediately BEFORE t=TD ({TD}s): {p_load_before:.2f} MW")
    print(f"PQ_9.Ppf immediately AFTER  t=TD ({TD}s): {p_load_after:.2f} MW")
    print(f"Actual step observed: {p_load_after - p_load_before:.2f} MW "
          f"(expected {increment_mw:.2f} MW)")
    print(f"\nTotal system load (PFlow, before any dynamics): {total_load_before_mw:.2f} MW")
    print(f"Total system load (Ppf, immediately after t=TD): {total_load_after_mw:.2f} MW")
    print(f"Total generation dispatch (PV.p0, static, before TDS): {total_gen_before_mw:.2f} MW")
    print(f"Immediate post-event load-generation mismatch: "
          f"{total_load_after_mw - total_load_before_mw:.2f} MW "
          f"(generation has not yet responded -- this is the initial imbalance driving the "
          f"frequency decline)")

    return dict(load_p0_nom_mw=load_p0_nom_pu * 100.0, increment_mw=increment_mw,
                p_load_before_mw=p_load_before, p_load_after_mw=p_load_after,
                total_load_before_mw=total_load_before_mw, total_load_after_mw=total_load_after_mw,
                total_gen_before_mw=total_gen_before_mw)


def run_case(controller, open_loop_command_mw=None):
    r = run_physical_scenario_tc(kind='load', bus=LOAD_BUS, alpha_L=ALPHA_L, lambda_L=1.00,
                                  p_max_bess_mw=PMAX_MW, k_f=KF, k_r=KR, tc=TC_S, tstep=TSTEP,
                                  controller=controller, open_loop_command_mw=open_loop_command_mw,
                                  bess_bus1=BESS_BUS_1, bess_bus2=BESS_BUS_2, tf=TF_INITIAL)
    return r


def main():
    disturbance_info = verify_disturbance_mechanics()

    print(f"\n=== Step 4: three cases (BESS buses ({BESS_BUS_1},{BESS_BUS_2}), Kf={KF:.1f}, "
          f"Kr={KR:.1f}, Tc=100ms, tstep=5ms) ===")
    cases = {}
    print("\n--- Case A: NoFFC ---")
    cases['A_NoFFC'] = run_case('no_ffc')
    print("--- Case B: F+R (frozen Kf/Kr at new locations) ---")
    cases['B_FplusR'] = run_case('physical')
    print("--- Case C: open-loop positive injection (+293.4MW per BESS, "
          f"~{2*PMAX_MW/disturbance_info['increment_mw']*100:.0f}% of the load increment combined) ---")
    cases['C_OpenLoop'] = run_case('open_loop_fixed', open_loop_command_mw=PMAX_MW)

    summary_rows = []
    traces = {}
    for name, r in cases.items():
        summary_rows.append(dict(
            case=name, df_nadir_hz=r['df_nadir_hz'], f_nadir_hz=r['f_nadir_hz'],
            RoCoF_max_hz_s=r['rocof_max_hz_s'],
            f_bess1_min_hz=float(np.min(r['f_bess1_hz'])), f_bess2_min_hz=float(np.min(r['f_bess2_hz'])),
            rocof_bess1_max=float(np.max(np.abs(r['rocof_bess1_hz_s']))),
            rocof_bess2_max=float(np.max(np.abs(r['rocof_bess2_hz_s']))),
            f_coi_min_hz=float(np.min(r['f_coi_hz'])),
            p_delivered1_peak_mw=float(np.max(np.abs(r['p_delivered1_mw']))),
            p_delivered2_peak_mw=float(np.max(np.abs(r['p_delivered2_mw']))),
            TDS_success=bool(r['tds_success']),
        ))
        traces[name] = dict(t=r['t'], f_worst_hz=r['f_worst_hz'], rocof_worst_hz_s=r['rocof_worst_hz_s'],
                             f_coi_hz=r['f_coi_hz'], f_bess1_hz=r['f_bess1_hz'], f_bess2_hz=r['f_bess2_hz'],
                             rocof_bess1_hz_s=r['rocof_bess1_hz_s'], rocof_bess2_hz_s=r['rocof_bess2_hz_s'],
                             p_command1_mw=r['p_command1_mw'], p_command2_mw=r['p_command2_mw'],
                             p_delivered1_mw=r['p_delivered1_mw'], p_delivered2_mw=r['p_delivered2_mw'])

    df = pd.DataFrame(summary_rows)
    print("\n=== Step 5/6: summary across cases ===")
    print(df.to_string(index=False))

    out_csv = os.path.join(OUT_DIAG, 'p2e7_load_severe_deep_diagnostic.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    out_npz = os.path.join(OUT_TRAJ, 'p2e7_load_severe_deep_diagnostic_traces.npz')
    flat = {}
    for key, d in traces.items():
        for name, arr in d.items():
            flat[f"{key}__{name}"] = arr
    np.savez(out_npz, **flat)
    print(f"Saved: {out_npz}")

    a, b, c = summary_rows[0], summary_rows[1], summary_rows[2]
    print("\n=== Causal conclusion inputs ===")
    print(f"Case A (NoFFC)     df_nadir={a['df_nadir_hz']*1000:+.2f}mHz RoCoF_max={a['RoCoF_max_hz_s']:.4f}Hz/s")
    print(f"Case B (F+R)       df_nadir={b['df_nadir_hz']*1000:+.2f}mHz RoCoF_max={b['RoCoF_max_hz_s']:.4f}Hz/s")
    print(f"Case C (open-loop) df_nadir={c['df_nadir_hz']*1000:+.2f}mHz RoCoF_max={c['RoCoF_max_hz_s']:.4f}Hz/s")
    open_loop_helps = abs(c['df_nadir_hz'] - a['df_nadir_hz']) > 1e-4 or abs(c['RoCoF_max_hz_s'] - a['RoCoF_max_hz_s']) > 1e-3
    fr_helps = abs(b['df_nadir_hz'] - a['df_nadir_hz']) > 1e-4 or abs(b['RoCoF_max_hz_s'] - a['RoCoF_max_hz_s']) > 1e-3
    print(f"\nOpen-loop clearly changes frequency vs NoFFC: {open_loop_helps}")
    print(f"F+R clearly changes frequency vs NoFFC: {fr_helps}")
    if open_loop_helps and not fr_helps:
        print("CONCLUSION: open-loop injection moves the metric but F+R does not -- "
              "problem is in the control law / activation signal for this disturbance type.")
    elif not open_loop_helps:
        print("CONCLUSION: even open-loop injection does not move the metric -- "
              "review disturbance/metric implementation before continuing.")
    else:
        print("CONCLUSION: both open-loop and F+R change the metric -- re-examine relative magnitude.")


if __name__ == '__main__':
    main()
