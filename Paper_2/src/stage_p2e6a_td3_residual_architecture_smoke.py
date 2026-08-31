#!/usr/bin/env python
"""
P2-E6a -- implementation smoke tests for the revised droop* + TD3 residual
environment (Paper_2/src/p2_env.py). Authorized explicitly by the user.

NO performance evaluation, NO P_RL,max sweep, NO policy selection, NO TD3
training -- only mechanical correctness of the architecture (action ->
command -> ANDES step -> observation), exactly the 8 checks the user
specified:

  1. action=0 reproduces droop* numerically (vs. p2_common.run_physical_
     scenario_tc(controller='physical', k_r=0.0), the already-validated
     droop implementation used to freeze Kd* in DEC-P2-024).
  2. action=+1/-1 produces exactly +/-P_RL,max before the final clip.
  3. total clipping is correct (unit test of combine_command(), synthetic
     values -- does not depend on a live disturbance being large enough).
  4. MW units are correct (P_RL,max = 0.25*Pmax exactly; a=1 with df~=0
     yields P_total~=P_RL,max, not off by a factor of 100).
  5. the two BESS are independent (BESS1's command does not depend on
     BESS2's action, and vice versa).
  6. reset() is correct (repeated resets produce a consistent clean initial
     state).
  7. action timing is exactly Tc=5ms (ctrl_period_steps==1, dae.t advances
     by exactly tstep per step()).
  8. observations and actions are free of NaN/Inf over a full rollout with
     random actions.

Scenario used throughout: gen_severe (kind='gen', gen='GENROU_4', rho=0.90),
same DESIGN scenario used to freeze Kd*/verify F+R (DEC-P2-024/025). Config
frozen per DEC-P2-026 (P2-E6a instruction): buses 16/20, Tc=tstep=5ms,
Pmax=293.4MW, Kd*=4694.4MW/Hz, P_RL,max=0.25*Pmax.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import run_physical_scenario_tc
from p2_env import P2ResidualEnv, combine_command

PMAX_MW = 293.4
KD_STAR = 4694.4
P_RL_MAX_FRAC = 0.25
P_RL_MAX_MW = P_RL_MAX_FRAC * PMAX_MW
TC = TSTEP = 0.005
TF = 6.0
BESS_BUS1, BESS_BUS2 = 16, 20
SCEN = dict(kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00)

results = []


def check(name, ok, detail=''):
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{'  -- ' + detail if detail else ''}")


def make_env(tf=TF):
    return P2ResidualEnv(kind=SCEN['kind'], gen=SCEN['gen'], rho=SCEN['rho'],
                          lambda_L=SCEN['lambda_L'], p_max_bess_mw=PMAX_MW,
                          kd_star_mw_per_hz=KD_STAR, p_rl_max_frac=P_RL_MAX_FRAC,
                          tc=TC, tstep=TSTEP, bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, tf=tf)


def test1_action_zero_matches_droop():
    print("\n=== Test 1: action=0 reproduces droop* numerically ===")
    env = make_env()
    env.reset()
    f1s, f2s, p1s, p2s = [], [], [], []
    tds_ok = True
    for _ in range(env.n_int_steps):
        obs, reward, term, trunc, info = env.step([0.0, 0.0])
        f1s.append(obs[0]); f2s.append(obs[3]); p1s.append(obs[2]); p2s.append(obs[5])
        if term:
            tds_ok = False
            break

    ref = run_physical_scenario_tc(kind=SCEN['kind'], gen=SCEN['gen'], rho=SCEN['rho'],
                                    lambda_L=SCEN['lambda_L'], p_max_bess_mw=PMAX_MW,
                                    k_f=KD_STAR, k_r=0.0, tc=TC, tstep=TSTEP, controller='physical',
                                    bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2, tf=TF)

    n = min(len(f1s), len(ref['f_bess1_hz']))
    f1_diff = np.max(np.abs(np.array(f1s[:n]) - (ref['f_bess1_hz'][:n] - 60.0)))
    f2_diff = np.max(np.abs(np.array(f2s[:n]) - (ref['f_bess2_hz'][:n] - 60.0)))
    p1_diff = np.max(np.abs(np.array(p1s[:n]) - ref['p_delivered1_mw'][:n]))
    p2_diff = np.max(np.abs(np.array(p2s[:n]) - ref['p_delivered2_mw'][:n]))
    tol = 1e-6
    ok = (tds_ok and bool(ref['tds_success']) and len(f1s) == len(ref['f_bess1_hz']) and
          f1_diff < tol and f2_diff < tol and p1_diff < tol and p2_diff < tol)
    check("action=0 == droop* (local freq/power trajectories, both BESS)", ok,
          f"max|df1|={f1_diff:.2e}Hz max|df2|={f2_diff:.2e}Hz "
          f"max|dp1|={p1_diff:.2e}MW max|dp2|={p2_diff:.2e}MW n_steps_env={len(f1s)} "
          f"n_steps_ref={len(ref['f_bess1_hz'])}")
    return ok


def test2_action_pm1_gives_exact_p_rl_max():
    print("\n=== Test 2: action=+1/-1 gives exactly +/-P_RL,max before clip ===")
    env = make_env()
    env.reset()
    _, _, _, _, info_pos = env.step([1.0, 1.0])
    exact_pos = (info_pos['p_rl_mw'][0] == P_RL_MAX_MW and info_pos['p_rl_mw'][1] == P_RL_MAX_MW)
    env.reset()
    _, _, _, _, info_neg = env.step([-1.0, -1.0])
    exact_neg = (info_neg['p_rl_mw'][0] == -P_RL_MAX_MW and info_neg['p_rl_mw'][1] == -P_RL_MAX_MW)
    check("a=+1 -> P_RL == +P_RL,max exactly (both BESS)", exact_pos, f"{info_pos['p_rl_mw']}")
    check("a=-1 -> P_RL == -P_RL,max exactly (both BESS)", exact_neg, f"{info_neg['p_rl_mw']}")
    return exact_pos and exact_neg


def test3_clipping_correct():
    print("\n=== Test 3: total clipping correct (unit test, synthetic values) ===")
    cases = [
        (250.0, 100.0, PMAX_MW, PMAX_MW),      # exceeds +Pmax
        (-250.0, -100.0, PMAX_MW, -PMAX_MW),   # exceeds -Pmax
        (50.0, 50.0, PMAX_MW, 100.0),          # inside range, no clip
        (0.0, P_RL_MAX_MW, PMAX_MW, P_RL_MAX_MW),  # boundary sanity
    ]
    all_ok = True
    for p_droop, p_rl, pmax, expected in cases:
        preclip, total = combine_command(p_droop, p_rl, pmax)
        ok = abs(total - expected) < 1e-9 and abs(preclip - (p_droop + p_rl)) < 1e-9
        all_ok &= ok
        check(f"combine_command(droop={p_droop}, rl={p_rl}, pmax={pmax}) -> {total:.2f} "
              f"(expected {expected:.2f}, preclip={preclip:.2f})", ok)
    return all_ok


def test4_units_correct():
    print("\n=== Test 4: MW units correct ===")
    ok_rlmax = abs(P_RL_MAX_MW - 0.25 * PMAX_MW) < 1e-9 and abs(P_RL_MAX_MW - 73.35) < 1e-6
    check(f"P_RL,max == 0.25*Pmax == 73.35 MW exactly", ok_rlmax, f"P_RL,max={P_RL_MAX_MW}")

    env = make_env()
    obs0 = env.reset()
    # right after reset, pre-disturbance (t=0 < TD=1.0): local df should be ~0
    df1_pre, df2_pre = obs0[0], obs0[3]
    _, _, _, _, info = env.step([1.0, 0.0])
    p_total1_ok = abs(info['p_total_mw'][0] - P_RL_MAX_MW) < 0.5  # droop term ~0 pre-disturbance
    check("a1=1 with df~=0 pre-disturbance -> P_total,1 ~= P_RL,max (not off by 100x)", p_total1_ok,
          f"df1_pre={df1_pre:.4f}Hz P_total,1={info['p_total_mw'][0]:.3f}MW "
          f"P_droop,1={info['p_droop_mw'][0]:.3f}MW")
    return ok_rlmax and p_total1_ok


def test5_bess_independent():
    print("\n=== Test 5: two BESS act independently ===")
    env = make_env()
    env.reset()
    _, _, _, _, info_a = env.step([1.0, 0.0])
    env2 = make_env()
    env2.reset()
    _, _, _, _, info_b = env2.step([1.0, 1.0])
    p_bess1_same = abs(info_a['p_total_mw'][0] - info_b['p_total_mw'][0]) < 1e-6
    p_bess2_differs = abs(info_a['p_total_mw'][1] - info_b['p_total_mw'][1]) > 1e-3
    check("BESS1 command identical regardless of BESS2's action (a2=0 vs a2=1)", p_bess1_same,
          f"case a=(1,0): P1={info_a['p_total_mw'][0]:.3f}  case a=(1,1): P1={info_b['p_total_mw'][0]:.3f}")
    check("BESS2 command responds to its own action (a2=0 vs a2=1 differ)", p_bess2_differs,
          f"case a=(1,0): P2={info_a['p_total_mw'][1]:.3f}  case a=(1,1): P2={info_b['p_total_mw'][1]:.3f}")
    return p_bess1_same and p_bess2_differs


def test6_reset_correct():
    print("\n=== Test 6: reset() produces a consistent clean initial state ===")
    env = make_env()
    obs_a = env.reset()
    obs_b = env.reset()
    diff = np.max(np.abs(obs_a - obs_b))
    ok = diff < 1e-9
    check("repeated reset() gives identical initial observation", ok, f"max|dobs|={diff:.2e}")
    clean = abs(obs_a[0]) < 1e-6 and abs(obs_a[3]) < 1e-6 and abs(obs_a[2]) < 1e-6 and abs(obs_a[5]) < 1e-6
    check("initial state is pre-disturbance (df~=0, P_delivered~=0 both BESS)", clean,
          f"obs={obs_a}")
    return ok and clean


def test7_timing_exact_tc():
    print("\n=== Test 7: action timing exactly Tc=5ms ===")
    env = make_env()
    env.reset()
    ok_period = env.ctrl_period_steps == 1
    check("ctrl_period_steps == 1 (Tc=tstep -> action every integration step)", ok_period,
          f"ctrl_period_steps={env.ctrl_period_steps}")
    t0 = float(env.ss.dae.t)
    env.step([0.0, 0.0])
    t1 = float(env.ss.dae.t)
    dt_ok = abs((t1 - t0) - TSTEP) < 1e-9
    check("dae.t advances by exactly tstep=5ms per step()", dt_ok, f"dt={t1-t0:.6f}s")
    return ok_period and dt_ok


def test8_no_nan_inf():
    print("\n=== Test 8: observations/actions free of NaN/Inf over a full rollout ===")
    rng = np.random.default_rng(0)
    env = make_env()
    obs = env.reset()
    all_finite = np.isfinite(obs).all()
    for _ in range(env.n_int_steps):
        action = rng.uniform(-1.0, 1.0, size=2)
        obs, reward, term, trunc, info = env.step(action)
        if not (np.isfinite(obs).all() and np.isfinite(action).all() and np.isfinite(reward)):
            all_finite = False
            break
        if term or trunc:
            break
    check("all observations/actions/rewards finite over full random-action rollout", bool(all_finite))
    return bool(all_finite)


def main():
    print(f"=== P2-E6a smoke tests: droop*({KD_STAR}MW/Hz) + TD3 residual "
          f"(P_RL,max={P_RL_MAX_MW}MW), buses {BESS_BUS1}/{BESS_BUS2}, Tc=tstep={TC*1000:.0f}ms ===")

    all_pass = True
    all_pass &= test1_action_zero_matches_droop()
    all_pass &= test2_action_pm1_gives_exact_p_rl_max()
    all_pass &= test3_clipping_correct()
    all_pass &= test4_units_correct()
    all_pass &= test5_bess_independent()
    all_pass &= test6_reset_correct()
    all_pass &= test7_timing_exact_tc()
    all_pass &= test8_no_nan_inf()

    print("\n=== SUMMARY ===")
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"\nP_RL,max = {P_RL_MAX_MW} MW (0.25 x Pmax={PMAX_MW}MW)")
    print(f"OVERALL: {'ALL SMOKE TESTS PASS' if all_pass else 'AT LEAST ONE SMOKE TEST FAILED'}")


if __name__ == '__main__':
    main()
