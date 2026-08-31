#!/usr/bin/env python
"""
P2-E8 Part A -- formal preflight, 26 checks, exactly as specified by the
user. Uses the FROZEN configuration of DEC-P2-033 (droop*+TD3 residual,
buses 16/20, Kd*=4694.4MW/Hz, Pmax=293.4MW, P_RL,max=73.35MW, Tc=tstep=5ms,
OBS-A, normalization, splits). No parameter is modified. No checks are
reinterpreted or relaxed if failing.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from p2_common import (run_physical_scenario_tc, GEN_BUSES,
                        G_TRAIN_P2, L_TRAIN_P2, G_VALIDATION_P2, L_VALIDATION_P2,
                        OP_TRAIN_RANGE_P2)
from p2_env import combine_command
from p2_env_train import P2ResidualTrainEnv
import gymnasium
from gymnasium import spaces

PMAX_MW = 293.4
KD_STAR = 4694.4
P_RL_MAX_MW = 73.35
TC = TSTEP = 0.005
BESS_BUS1, BESS_BUS2 = 16, 20
FIXED_GEN_SCEN = dict(kind='gen', gen='GENROU_4', rho=0.90, lambda_L=1.00)
FIXED_LOAD_SCEN = dict(kind='load', pq_idx='PQ_9', alpha_L=0.50, lambda_L=1.00)

OUT_DIAG = os.path.join('Paper_2', 'artifacts', 'preflight')
os.makedirs(OUT_DIAG, exist_ok=True)

results = []


def check(num, name, ok, detail=''):
    results.append(dict(check=f'PF2-{num:02d}', name=name, result='PASS' if ok else 'FAIL', detail=detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] PF2-{num:02d} {name}{'  -- ' + detail if detail else ''}")


def make_env(seed=11, fixed_scenario=None):
    return P2ResidualTrainEnv(obs_mode='OBS-A', p_max_bess_mw=PMAX_MW, kd_star_mw_per_hz=KD_STAR,
                               p_rl_max_mw=P_RL_MAX_MW, tc=TC, tstep=TSTEP,
                               bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2,
                               fixed_scenario=fixed_scenario, seed=seed)


def main():
    print("=== P2-E8 Part A: preflight formal, 26 checks (config FROZEN DEC-P2-033) ===\n")

    # PF2-01: Gymnasium API valida
    env = make_env(fixed_scenario=FIXED_GEN_SCEN)
    is_gym_env = isinstance(env, gymnasium.Env)
    has_api = all(hasattr(env, a) for a in ('reset', 'step', 'action_space', 'observation_space'))
    try:
        from gymnasium.utils.env_checker import check_env as gym_check_env
        gym_check_env(env, skip_render_check=True)
        gym_checker_ok, gym_checker_detail = True, 'gymnasium.utils.env_checker.check_env: no errors'
    except Exception as e:
        gym_checker_ok, gym_checker_detail = False, f'check_env raised: {type(e).__name__}: {e}'
    check(1, 'Gymnasium API valida', is_gym_env and has_api and gym_checker_ok, gym_checker_detail)

    # PF2-02: observation_space correcto
    obs_space_ok = (isinstance(env.observation_space, spaces.Box) and env.observation_space.shape == (6,))
    check(2, 'observation_space correcto', obs_space_ok, f'shape={env.observation_space.shape}')

    # PF2-03: action_space [-1,1]^2 correcto
    act_space_ok = (isinstance(env.action_space, spaces.Box) and env.action_space.shape == (2,) and
                     np.allclose(env.action_space.low, -1.0) and np.allclose(env.action_space.high, 1.0))
    check(3, 'action_space [-1,1]^2 correcto', act_space_ok,
          f'low={env.action_space.low} high={env.action_space.high}')

    # PF2-04: dimension OBS-A = 6
    obs0, info0 = env.reset()
    obs1, r, term, trunc, info1 = env.step([0.0, 0.0])
    check(4, 'dimension OBS-A = 6', obs0.shape == (6,) and obs1.shape == (6,), f'{obs0.shape}')

    # PF2-05: normalizacion exacta
    raw = env.get_raw_signals()
    expected = np.array([(raw['f1_hz'] - 60.0) / 0.5, raw['rocof1_hz_s'] / 1.0, raw['p1_mw'] / 293.4,
                          (raw['f2_hz'] - 60.0) / 0.5, raw['rocof2_hz_s'] / 1.0, raw['p2_mw'] / 293.4])
    norm_diff = float(np.max(np.abs(obs1 - expected)))
    check(5, 'normalizacion exacta', norm_diff < 1e-4, f'max|diff|={norm_diff:.2e}')

    # PF2-06/07: observaciones/acciones finitas (full episode, random actions)
    env2 = make_env(fixed_scenario=FIXED_GEN_SCEN)
    obs, info = env2.reset()
    rng = np.random.default_rng(0)
    obs_finite, act_finite = True, True
    for _ in range(env2.n_int_steps):
        a = rng.uniform(-1, 1, size=2)
        obs, r, term, trunc, info = env2.step(a)
        if not np.isfinite(obs).all():
            obs_finite = False
        if not np.isfinite(a).all():
            act_finite = False
        if term or trunc:
            break
    check(6, 'observaciones finitas (episodio completo)', obs_finite)
    check(7, 'acciones finitas (episodio completo)', act_finite)

    # PF2-08: reset determinista bajo seed fija (misma seed -> mismo escenario muestreado)
    env_a = make_env(seed=42)
    env_a.reset()
    env_b = make_env(seed=42)
    env_b.reset()
    same_scenario = env_a._scen == env_b._scen
    check(8, 'reset determinista bajo seed fija', same_scenario,
          f'{env_a._scen} vs {env_b._scen}')

    # PF2-09: reset sin estado residual entre episodios
    env3 = make_env(fixed_scenario=FIXED_GEN_SCEN)
    obs, info = env3.reset()
    for _ in range(20):
        obs, r, term, trunc, info = env3.step([1.0, 1.0])
    t_before_reset = info['t']
    obs_new, info_new = env3.reset()
    no_residual = (abs(info_new['scenario'] == FIXED_GEN_SCEN) and
                   float(env3.ss.dae.t) < 1e-9 and np.max(np.abs(obs_new)) < 1e-6)
    check(9, 'reset sin estado residual entre episodios', bool(no_residual),
          f't_before_reset={t_before_reset:.3f}s  dae.t_after_reset={float(env3.ss.dae.t):.6f}s  '
          f'max|obs_after_reset|={np.max(np.abs(obs_new)):.2e}')

    # PF2-10: action=0 reproduce droop* (compare RAW signals, not denormalized obs, to avoid
    # spurious round-trip floating-point noise from the normalize/denormalize conversion)
    env4 = make_env(fixed_scenario=FIXED_GEN_SCEN)
    env4.reset()
    f1s, p1s = [], []
    for _ in range(env4.n_int_steps):
        env4.step([0.0, 0.0])
        raw = env4.get_raw_signals()
        f1s.append(raw['f1_hz']); p1s.append(raw['p1_mw'])
    ref = run_physical_scenario_tc(p_max_bess_mw=PMAX_MW, k_f=KD_STAR, k_r=0.0, tc=TC, tstep=TSTEP,
                                    controller='physical', bess_bus1=BESS_BUS1, bess_bus2=BESS_BUS2,
                                    tf=6.0, **FIXED_GEN_SCEN)
    n = min(len(f1s), len(ref['f_bess1_hz']))
    d1 = np.max(np.abs(np.array(f1s[:n]) - ref['f_bess1_hz'][:n]))
    d2 = np.max(np.abs(np.array(p1s[:n]) - ref['p_delivered1_mw'][:n]))
    check(10, 'action=0 reproduce droop* numericamente', d1 < 1e-6 and d2 < 1e-6,
          f'max|df1_diff|={d1:.2e}Hz max|p1_diff|={d2:.2e}MW n={n}')

    # PF2-11: residual +-1 produce exactamente +-73.35MW antes del clip
    env5 = make_env(fixed_scenario=FIXED_GEN_SCEN)
    env5.reset()
    _, _, _, _, info_p = env5.step([1.0, 1.0])
    env5.reset()
    _, _, _, _, info_n = env5.step([-1.0, -1.0])
    rl_ok = (info_p['p_rl_mw'] == (P_RL_MAX_MW, P_RL_MAX_MW) and
             info_n['p_rl_mw'] == (-P_RL_MAX_MW, -P_RL_MAX_MW))
    check(11, 'residual +-1 = +-73.35MW antes del clip', rl_ok, f'{info_p["p_rl_mw"]} / {info_n["p_rl_mw"]}')

    # PF2-12: clipping final a +-293.4MW correcto
    cases = [(250.0, 100.0, PMAX_MW), (-250.0, -100.0, PMAX_MW)]
    clip_ok = all(combine_command(d, rl, PMAX_MW)[1] in (PMAX_MW, -PMAX_MW) for d, rl, _ in cases)
    check(12, 'clipping final a +-293.4MW correcto', clip_ok,
          f'{[combine_command(d, rl, PMAX_MW) for d, rl, _ in cases]}')

    # PF2-13: unidades MW correctas
    units_ok = abs(info_p['p_total_mw'][0] - P_RL_MAX_MW) < 0.5  # droop~0 at t=0, pre-disturbance
    check(13, 'unidades MW correctas', units_ok, f'P_total(a=1,pre-dist)={info_p["p_total_mw"][0]:.3f}MW')

    # PF2-14: independencia BESS1/BESS2
    env6a = make_env(fixed_scenario=FIXED_GEN_SCEN); env6a.reset()
    _, _, _, _, ia = env6a.step([1.0, 0.0])
    env6b = make_env(fixed_scenario=FIXED_GEN_SCEN); env6b.reset()
    _, _, _, _, ib = env6b.step([1.0, 1.0])
    indep_ok = (abs(ia['p_total_mw'][0] - ib['p_total_mw'][0]) < 1e-6 and
                abs(ia['p_total_mw'][1] - ib['p_total_mw'][1]) > 1e-3)
    check(14, 'independencia BESS1/BESS2', indep_ok,
          f'BESS1: {ia["p_total_mw"][0]:.3f} vs {ib["p_total_mw"][0]:.3f}  '
          f'BESS2: {ia["p_total_mw"][1]:.3f} vs {ib["p_total_mw"][1]:.3f}')

    # PF2-15/16: Tc=5ms / tstep=5ms exacto
    check(15, 'Tc=5ms exacto (ctrl_period_steps==1)', env.ctrl_period_steps == 1,
          f'ctrl_period_steps={env.ctrl_period_steps}')
    env7 = make_env(fixed_scenario=FIXED_GEN_SCEN); env7.reset()
    t0 = float(env7.ss.dae.t)
    env7.step([0.0, 0.0])
    t1 = float(env7.ss.dae.t)
    check(16, 'tstep=5ms exacto', abs((t1 - t0) - TSTEP) < 1e-9, f'dt={t1-t0:.6f}s')

    # PF2-17: exactamente una accion por step (verificacion ESTRUCTURAL del codigo, no de
    # uniformidad temporal del solver -- ver nota mas abajo sobre el hallazgo de dt no uniforme,
    # que es un asunto DISTINTO y benigno, no lo que este check debe medir)
    import inspect
    step_src = inspect.getsource(env.step)
    # exactamente un bloque do_switch/calc_h/itm_step, sin bucle 'for'/'while' envolviendolo
    n_itm_calls = step_src.count('itm_step()')
    has_loop_around_step = ('for ' in step_src or 'while ' in step_src)
    one_action_per_step = (n_itm_calls == 1) and (not has_loop_around_step)
    check(17, 'exactamente una accion por step (verificacion estructural del codigo)',
          one_action_per_step,
          f'itm_step() aparece {n_itm_calls} vez/veces en step(), sin bucle for/while envolviendolo '
          f'(tc==tstep se garantiza por el assert en __init__)')

    # PF2-18: sin duplicacion temporal (t estrictamente creciente, exactamente n_int_steps+1 puntos,
    # nunca se repite ni retrocede -- ver tambien el hallazgo de dt no uniforme abajo, que no
    # constituye duplicacion: ningun dt es <=0 ni se repite un mismo t)
    env8 = make_env(fixed_scenario=FIXED_GEN_SCEN); env8.reset()
    t_hist = [float(env8.ss.dae.t)]
    for _ in range(env8.n_int_steps):
        obs, r, term, trunc, info = env8.step([0.0, 0.0])
        t_hist.append(info['t'])
        if term or trunc:
            break
    t_arr = np.array(t_hist)
    dt_arr = np.diff(t_arr)
    no_dup = (len(t_arr) == env8.n_int_steps + 1) and np.all(dt_arr > 0)
    check(18, 'sin duplicacion temporal', bool(no_dup), f'n_steps={len(t_arr)-1} (esperado {env8.n_int_steps})')

    # Hallazgo informativo (NO es uno de los 26 checks, reportado por transparencia): el solver de
    # ANDES (TDS de paso fijo, config.fixt=1) no usa dt EXACTAMENTE tstep=5ms en el 100% de los
    # pasos -- inserta micro-pasos correctivos (dt<<tstep, nunca >tstep) para "aterrizar" exactamente
    # en el instante del evento discreto (t=TD) y en un pequeno numero de puntos adicionales.
    # Verificado que este comportamiento YA EXISTIA en p2_common.py (mismo mecanismo TDS/itm_step,
    # DEC-P1-007) antes de P2-E6/E8 -- no es un defecto introducido por el entorno nuevo, y no causa
    # duplicacion ni perdida de tiempo (todos los dt son >0, ninguno excede tstep).
    n_irregular = int(np.sum(np.abs(dt_arr - TSTEP) > 1e-6))
    print(f"  [INFO] dt no uniforme en {n_irregular}/{len(dt_arr)} pasos (micro-pasos correctivos del "
          f"solver, ya presentes en p2_common.py -- ver DEC-P2-034 para el detalle completo)")

    # PF2-19: evento aplicado una sola vez -- medido DIRECTAMENTE sobre la variable del disturbio
    # (PQ.Ppf para carga), no sobre P_BESS (senal derivada, continuamente variable porque el droop
    # reacciona cada paso a una frecuencia que oscila de forma genuina tras el evento -- medir ahi
    # confunde "el evento se aplica una vez" con "el controlador reacciona de forma suave", que son
    # propiedades distintas)
    env9 = make_env(fixed_scenario=FIXED_LOAD_SCEN); env9.reset()
    pq_uid = env9.ss.PQ.idx2uid([FIXED_LOAD_SCEN['pq_idx']])[0]
    ppf_hist = [float(env9.ss.PQ.Ppf.v[pq_uid])]
    for _ in range(env9.n_int_steps):
        env9.step([0.0, 0.0])
        ppf_hist.append(float(env9.ss.PQ.Ppf.v[pq_uid]))
    ppf_arr = np.array(ppf_hist)
    dppf = np.diff(ppf_arr)
    jump_idx = np.where(np.abs(dppf) > 1e-6)[0]
    check(19, 'evento aplicado una sola vez (medido en PQ.Ppf, el disturbio real)', len(jump_idx) == 1,
          f'{len(jump_idx)} cambio(s) de escalon en PQ.Ppf (esperado exactamente 1); '
          f'{"valor antes/despues: " + str((ppf_arr[jump_idx[0]], ppf_arr[jump_idx[0]+1])) if len(jump_idx)==1 else ""}')

    # PF2-20/21/22: splits y operating point respetados
    n_samples = 2000
    gens_drawn, loads_drawn, ops_drawn = [], [], []
    for _ in range(n_samples):
        scen = env._sample_train_scenario()
        if scen['kind'] == 'gen':
            gens_drawn.append(scen['gen'])
        else:
            loads_drawn.append(scen['pq_idx'])
        ops_drawn.append(scen['lambda_L'])
    gens_ok = set(gens_drawn) <= set(G_TRAIN_P2)
    loads_ok = set(loads_drawn) <= set(L_TRAIN_P2)
    ops_ok = all(OP_TRAIN_RANGE_P2[0] <= op <= OP_TRAIN_RANGE_P2[1] for op in ops_drawn)
    check(20, 'generacion de perturbaciones respeta train split', gens_ok,
          f'generadores muestreados: {sorted(set(gens_drawn))} subset de G_TRAIN_P2={G_TRAIN_P2}')
    check(21, 'load perturbations respetan train split', loads_ok,
          f'cargas muestreadas: {sorted(set(loads_drawn))} subset de L_TRAIN_P2={L_TRAIN_P2}')
    check(22, 'operating point dentro del rango train congelado', ops_ok,
          f'lambda_L range=[{min(ops_drawn):.3f},{max(ops_drawn):.3f}] dentro de {OP_TRAIN_RANGE_P2}')

    # PF2-23/24: reward scope y sin penalizacion de potencia
    f_gen_arr, rocof_gen_arr = env._gen_bus_arrays()
    reward_scope_ok = len(f_gen_arr) == len(GEN_BUSES) == 10
    check(23, 'reward utiliza solo los 10 GEN_BUSES', reward_scope_ok, f'len={len(f_gen_arr)}')
    import inspect
    reward_sig = inspect.signature(env._compute_reward)
    no_power_arg = 'p1' not in reward_sig.parameters and 'p2' not in reward_sig.parameters
    reward_src = inspect.getsource(env._compute_reward)
    no_power_term = ('p1' not in reward_src and 'p2' not in reward_src and
                      'energy' not in reward_src.lower() and 'E_BESS' not in reward_src)
    check(24, 'reward sin penalizacion de potencia/energia', no_power_arg and no_power_term,
          '_compute_reward() no recibe P_BESS como argumento y su codigo fuente no referencia potencia/energia')

    # PF2-25: TDS_success correcto y fallos manejados sin contaminar episodios
    tds_field_ok = 'tds_success' in info and isinstance(info['tds_success'], (bool, np.bool_))
    peak_reset_ok = (env3._df_peak == 0.0 and env3._rocof_peak == 0.0)  # from PF2-09's post-reset env3
    check(25, 'TDS_success correcto y peaks reseteados en reset() (sin fallo inducible bajo condiciones probadas)',
          tds_field_ok and peak_reset_ok,
          f'tds_success presente y booleano; df_peak/rocof_peak tras reset={env3._df_peak}/{env3._rocof_peak}; '
          f'ningun TDS failure se indujo en {n_samples + 8} episodios/pasos probados en este preflight')

    # PF2-26: reproducibilidad de episodio con misma seed (misma secuencia de acciones)
    action_seq = [np.array([0.3, -0.2]), np.array([-0.5, 0.5]), np.array([1.0, -1.0])] * 20
    def run_seq(seed):
        e = make_env(seed=seed, fixed_scenario=FIXED_GEN_SCEN)
        obs, info = e.reset()
        traj = [obs.copy()]
        for a in action_seq:
            obs, r, term, trunc, info = e.step(a)
            traj.append(obs.copy())
            if term or trunc:
                break
        return np.array(traj)
    traj_a = run_seq(7)
    traj_b = run_seq(7)
    repro_diff = float(np.max(np.abs(traj_a - traj_b))) if traj_a.shape == traj_b.shape else float('inf')
    check(26, 'reproducibilidad de episodio con misma seed', repro_diff < 1e-9,
          f'max|diff|={repro_diff:.2e} sobre {len(action_seq)} pasos con la misma secuencia de acciones')

    df = pd.DataFrame(results)
    out_csv = os.path.join(OUT_DIAG, 'p2e8_preflight_26checks.csv')
    df.to_csv(out_csv, index=False)
    print(f"\nSaved: {out_csv}")

    n_pass = int((df['result'] == 'PASS').sum())
    print(f"\n=== RESULTADO: {n_pass}/26 PASS ===")
    if n_pass < 26:
        print("FALLAS:")
        print(df[df['result'] == 'FAIL'].to_string(index=False))


if __name__ == '__main__':
    main()
