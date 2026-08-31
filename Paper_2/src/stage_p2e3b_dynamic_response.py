#!/usr/bin/env python
"""
P2-E3B -- BESS dynamic response characterization (command -> delivered power).

Open-loop step tests (no closed frequency loop, no Alter contingency, same
driver as P2-E3A) at moderate amplitudes within the actuator range, for both
BESS units independently. Measures effective delay, 10-90% rise time,
settling time (+/-2% band), steady-state error, and overshoot of the
command->power path, at fine time resolution (tstep=2ms) so the ESD1
internal current-lag time constant (`tip`, default 0.02s -- NOT `Tf`, which
is the unrelated SOC integrator constant, see report) is properly resolved.

Output: Paper_2/artifacts/diagnostics/p2_dynamic_response.csv (metrics per
step test) and Paper_2/artifacts/trajectories/p2e3b_step_traces.npz (raw
P_command(t)/P_delivered(t) for every test) plus an example figure. Does NOT
train or run TD3; does NOT touch the P2 final test.
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import BESS_BUS_1, BESS_BUS_2, run_command_step_response

PMAX_MW = 293.4  # same provisional Pmax as P2-E3A
FRACTIONS = [0.25, 0.5, 0.75, -0.25, -0.5, -0.75]  # moderate amplitudes, away from saturation

TF = 1.0
T_STEP = 0.2
TSTEP = 0.002  # 2 ms -- resolves ESD1's tip=0.02s (default) current lag with ~10 samples/tau
SETTLING_BAND = 0.02  # +/-2%


def analyze_step(t, p_command, p_delivered, t_step):
    i0 = int(np.searchsorted(t, t_step))
    p_initial = float(np.mean(p_delivered[max(0, i0 - 5):i0])) if i0 >= 5 else float(p_delivered[0])
    p_final = float(p_delivered[-1])
    cmd_final = float(p_command[-1])
    delta = p_final - p_initial

    if abs(delta) < 1e-6:
        return dict(effective_delay_s=float('nan'), rise_time_10_90_s=float('nan'),
                    settling_time_s=float('nan'), steady_state_error_MW=p_final - cmd_final,
                    overshoot_pct=0.0)

    frac = (p_delivered - p_initial) / delta  # 0 at start, 1 at final (for a monotone step)

    post = t >= t_step
    t_post = t[post]
    frac_post = frac[post]

    def first_crossing(level):
        # frac already normalizes direction (0 at start, 1 at final) regardless
        # of the sign of delta, so the crossing condition is always ">=".
        idx = np.where(frac_post >= level)[0]
        return float(t_post[idx[0]] - t_step) if len(idx) else float('nan')

    t10 = first_crossing(0.10)
    t90 = first_crossing(0.90)
    rise_time = (t90 - t10) if (not np.isnan(t10) and not np.isnan(t90)) else float('nan')
    effective_delay = t10

    band = SETTLING_BAND * abs(delta)
    within = np.abs(p_delivered - p_final) <= band
    settling_time = float('nan')
    for i in range(len(t) - 1, -1, -1):
        if t[i] < t_step:
            break
        if not within[i]:
            if i + 1 < len(t):
                settling_time = float(t[i + 1] - t_step)
            break
    else:
        settling_time = float(t_post[0] - t_step) if len(t_post) else float('nan')

    if delta > 0:
        overshoot = max(0.0, float(np.max(p_delivered[post])) - p_final)
    else:
        overshoot = max(0.0, p_final - float(np.min(p_delivered[post])))
    overshoot_pct = 100.0 * overshoot / abs(delta)

    return dict(effective_delay_s=effective_delay, rise_time_10_90_s=rise_time,
                settling_time_s=settling_time, steady_state_error_MW=p_final - cmd_final,
                overshoot_pct=overshoot_pct)


def main():
    rows = []
    traces = {}
    print(f"=== P2-E3B: dynamic response characterization (Pmax={PMAX_MW} MW, tstep={TSTEP*1000:.0f}ms) ===")
    for bus in (BESS_BUS_1, BESS_BUS_2):
        for frac in FRACTIONS:
            command_mw = frac * PMAX_MW
            r = run_command_step_response(PMAX_MW, bus, command_mw, tf=TF, tstep=TSTEP, t_step=T_STEP)
            metrics = analyze_step(r['t'], r['p_command_mw'], r['p_delivered_mw'], T_STEP)
            row = dict(bess_bus=bus, frac_of_pmax=frac, command_MW=command_mw,
                       TDS_success=bool(r['tds_success']), **metrics)
            rows.append(row)
            key = f"bus{bus}_frac{frac:+.2f}"
            traces[f"{key}_t"] = r['t']
            traces[f"{key}_p_command"] = r['p_command_mw']
            traces[f"{key}_p_delivered"] = r['p_delivered_mw']
            print(f"  bus={bus} frac={frac:+.2f} cmd={command_mw:+7.1f}MW  "
                  f"delay={metrics['effective_delay_s']*1000:6.1f}ms  "
                  f"rise10-90={metrics['rise_time_10_90_s']*1000:6.1f}ms  "
                  f"settle2%={metrics['settling_time_s']*1000:6.1f}ms  "
                  f"ss_err={metrics['steady_state_error_MW']:+.3f}MW  "
                  f"overshoot={metrics['overshoot_pct']:.2f}%  tds_ok={row['TDS_success']}")

    df = pd.DataFrame(rows)
    out_csv = os.path.join('Paper_2', 'artifacts', 'diagnostics', 'p2_dynamic_response.csv')
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv} ({len(df)} rows)")

    out_npz = os.path.join('Paper_2', 'artifacts', 'trajectories', 'p2e3b_step_traces.npz')
    os.makedirs(os.path.dirname(out_npz), exist_ok=True)
    np.savez(out_npz, **traces)
    print(f"Saved: {out_npz}")

    print("\n--- Summary across all step tests ---")
    print(f"median effective delay   = {df['effective_delay_s'].median()*1000:.1f} ms")
    print(f"median rise time (10-90) = {df['rise_time_10_90_s'].median()*1000:.1f} ms")
    print(f"median settling time(2%) = {df['settling_time_s'].median()*1000:.1f} ms")
    print(f"max |steady-state error| = {df['steady_state_error_MW'].abs().max():.3f} MW")
    print(f"max overshoot            = {df['overshoot_pct'].max():.2f} %")
    print(f"all TDS_success          = {bool(df['TDS_success'].all())}")

    tau_tip_theory_ms = 20.0
    print(f"\nTheoretical reference (ESD1/PVD1 source: Ipout = Lag(Ipcmd_y, T=tip), "
          f"tip default=0.02s): 10-90% rise ~= tip*ln(9) = {tau_tip_theory_ms*np.log(9):.1f} ms, "
          f"settling(2%) ~= 4*tip = {4*tau_tip_theory_ms:.1f} ms, no overshoot (pure 1st-order lag).")

    example = df[(df['bess_bus'] == BESS_BUS_1) & (df['frac_of_pmax'] == 0.5)].iloc[0]
    t = traces[f"bus{BESS_BUS_1}_frac+0.50_t"]
    pcmd = traces[f"bus{BESS_BUS_1}_frac+0.50_p_command"]
    pdel = traces[f"bus{BESS_BUS_1}_frac+0.50_p_delivered"]
    fig, ax = plt.subplots(figsize=(6.0, 3.5))
    ax.plot(t, pcmd, 'k--', label='P_command', linewidth=1.2)
    ax.plot(t, pdel, 'C0-', label='P_delivered', linewidth=1.2)
    ax.axvline(T_STEP, color='gray', linewidth=0.8, linestyle=':')
    ax.set_xlim(T_STEP - 0.05, T_STEP + 0.3)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Power (MW)')
    ax.set_title(f'P2-E3B: command->power step, bus {BESS_BUS_1}, +50% Pmax')
    ax.legend(fontsize=8)
    ax.grid(True, linestyle=':', alpha=0.6)
    fig.tight_layout()
    out_fig = os.path.join('Paper_2', 'artifacts', 'figures', 'p2_dynamic_response_example.png')
    os.makedirs(os.path.dirname(out_fig), exist_ok=True)
    fig.savefig(out_fig, dpi=200)
    print(f"Saved: {out_fig}")


if __name__ == '__main__':
    main()
