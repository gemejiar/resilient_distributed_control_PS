#!/usr/bin/env python
"""
P2-E6b -- Gymnasium-compatible training environment for the observation
ablation (OBS-A/B/C), droop*+TD3-residual architecture (P_RL,max=0.25*Pmax,
DEC-P2-028).

Kept SEPARATE from Paper_2/src/p2_env.py (the P2-E6a smoke-tested module,
fixed 8-signal observation, deterministic scenario) so that module's smoke
tests remain untouched/valid -- this file reuses the same low-level ANDES
case-construction/itm_step() mechanics but adds: (a) three selectable
observation modes, (b) randomized episode reset per the frozen P2 training
distribution (plan Section 10), (c) the SS6 reward (max over the 10 metrics
generators + terminal penalty + I_fail/I_unsafe, reused unweighted from
Paper_1's compute_reward mechanism per the plan's explicit "mismo mecanismo
que P1 SS15" instruction), (d) full Gymnasium reset()/step() API for
stable-baselines3 compatibility.

f_COI/RoCoF_COI (frozen this stage, DEC-P2-029): UNWEIGHTED mean over the 10
GEN_BUSES metrics generators -- the same proxy already used and declared
throughout this campaign (DEC-P2-019/021 etc.); no H-weighted COI is
implemented.

Normalization (frozen this stage, identical across OBS-A/B/C): every
Delta_f channel divided by F_REF_HZ=0.5, every RoCoF channel by
R_REF_HZ_S=1.0 (same reference scales as the SS6 reward -- reused, not
re-derived), every P_BESS channel by Pmax=293.4MW.

Observation modes:
  OBS-A (6): [df_16, RoCoF_16, P_BESS1, df_20, RoCoF_20, P_BESS2]           (all normalized)
  OBS-B (8): OBS-A + [df_COI, RoCoF_COI]
  OBS-C (22): [df_i, RoCoF_i for i in the 10 GEN_BUSES] + [P_BESS1, P_BESS2]

No future/leakage: every signal is read from ANDES state AT the current
integration step, immediately after stepping the physics and before any
subsequent action -- there is no lookahead into future disturbance timing
or future state.
"""
import numpy as np
import andes
import gymnasium
from gymnasium import spaces

from p2_common import (BASE_CASE, ROCOF_PARAMS, GEN_BUSES, BESS_ADMISSIBLE_BUSES,
                        AREA_GENS, K_FROZEN, F0_HZ, TD, TF_INITIAL,
                        add_bess_pair, natural_bus_voltages_at_lambda,
                        G_TRAIN_P2, L_TRAIN_P2, G_VALIDATION_P2, L_VALIDATION_P2,
                        OP_TRAIN_RANGE_P2, OP_VALIDATION_P2)
from p2_env import combine_command

F_REF_HZ = 0.5
R_REF_HZ_S = 1.0
I_UNSAFE_DF_HZ = 0.5
I_UNSAFE_ROCOF_HZ_S = 1.0
I_UNSAFE_WEIGHT = 10.0   # reused unweighted from Paper_1 compute_reward (SS15), not re-derived
I_FAIL_WEIGHT = 100.0    # idem
TERMINAL_WEIGHT = 2.0    # plan Section 6, r_terminal

OBS_DIMS = {'OBS-A': 6, 'OBS-B': 8, 'OBS-C': 22}

# Validation scenario set used for J_val_P2 in this ablation (DEC-P2-029):
# G_VALIDATION_P2/L_VALIDATION_P2 x OP_VALIDATION_P2, disturbance magnitude
# fixed at the midpoint of the training range (rho=0.60 for U(0.30,0.90),
# alpha_L=0.30 for U(0.10,0.50)) -- the plan freezes WHICH generator/load/
# operating-points are validation (DEC-P2-003), but not a specific rho/
# alpha_L for them; the midpoint choice is made explicit here, not hidden.
VALIDATION_RHO = 0.60
VALIDATION_ALPHA_L = 0.30


def _build_validation_scenarios():
    scens = []
    for gen in G_VALIDATION_P2:
        for op in OP_VALIDATION_P2:
            scens.append(dict(kind='gen', gen=gen, rho=VALIDATION_RHO, lambda_L=op))
    for load in L_VALIDATION_P2:
        for op in OP_VALIDATION_P2:
            scens.append(dict(kind='load', pq_idx=load, alpha_L=VALIDATION_ALPHA_L, lambda_L=op))
    return scens


VALIDATION_SCENARIOS = _build_validation_scenarios()


class P2ResidualTrainEnv(gymnasium.Env):
    metadata = {}

    def __init__(self, obs_mode, p_max_bess_mw=293.4, kd_star_mw_per_hz=4694.4,
                 p_rl_max_mw=73.35, tc=0.005, tstep=0.005, bess_bus1=16, bess_bus2=20,
                 tf=TF_INITIAL, scenario_pool='train', fixed_scenario=None, seed=None,
                 action_smoothness_weight=0.0):
        super().__init__()
        assert obs_mode in OBS_DIMS
        assert abs(tc - tstep) < 1e-12
        assert scenario_pool in ('train', 'validation')
        self.obs_mode = obs_mode
        self.p_max_bess_mw = p_max_bess_mw
        self.kd_star = kd_star_mw_per_hz
        self.p_rl_max_mw = p_rl_max_mw
        self.tc, self.tstep, self.tf = tc, tstep, tf
        self.bess_bus1, self.bess_bus2 = bess_bus1, bess_bus2
        self.scenario_pool = scenario_pool
        self.fixed_scenario = fixed_scenario
        self._val_idx = 0
        self.n_int_steps = int(round(tf / tstep))
        self.ctrl_period_steps = max(1, int(round(tc / tstep)))  # always 1 given the assert above
        self.rng = np.random.default_rng(seed)
        # seed66 (DEC-P2-041 pending): action-rate smoothness penalty, OFF by default
        # (weight=0.0 reproduces the exact reward used by seeds 11-55 -- additive, backward
        # compatible, not a redefinition of the SS6 reward).
        self.action_smoothness_weight = action_smoothness_weight
        self._prev_action = np.zeros(2, dtype=np.float64)

        obs_dim = OBS_DIMS[obs_mode]
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)

        self.ss = None

    def _sample_train_scenario(self):
        lambda_L = float(self.rng.uniform(*OP_TRAIN_RANGE_P2))
        if self.rng.random() < 0.5:
            gen = self.rng.choice(G_TRAIN_P2)
            rho = float(self.rng.uniform(0.30, 0.90))
            return dict(kind='gen', gen=gen, rho=rho, lambda_L=lambda_L)
        else:
            pq_idx = self.rng.choice(L_TRAIN_P2)
            alpha_L = float(self.rng.uniform(0.10, 0.50))
            return dict(kind='load', pq_idx=pq_idx, alpha_L=alpha_L, lambda_L=lambda_L)

    def _next_scenario(self):
        if self.fixed_scenario is not None:
            return self.fixed_scenario
        if self.scenario_pool == 'validation':
            scen = VALIDATION_SCENARIOS[self._val_idx % len(VALIDATION_SCENARIOS)]
            self._val_idx += 1
            return scen
        return self._sample_train_scenario()

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        scen = self._next_scenario()
        self._scen = scen
        bus_voltages = natural_bus_voltages_at_lambda(scen['lambda_L'])
        ss = andes.load(BASE_CASE, setup=False, no_output=True, default_config=True)
        for b in GEN_BUSES:
            ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))
        for b in BESS_ADMISSIBLE_BUSES:
            ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))

        if scen['kind'] == 'gen':
            gov_uid = ss.TGOV1N.syn.v.index(scen['gen'])
            gov_idx = ss.TGOV1N.idx.v[gov_uid]
            alter_idx = ss.add('Alter', dict(model='TGOV1N', dev=gov_idx, src='paux0',
                                              t=TD, method='=', amount=0.0))
        else:
            pq_bus_uid = ss.PQ.idx2uid([scen['pq_idx']])[0]
            bus_num = ss.PQ.bus.v[pq_bus_uid]
            pq_idx_lookup = ss.PQ.find_idx(keys='bus', values=[bus_num])[0]
            alter_idx = ss.add('Alter', dict(model='PQ', dev=pq_idx_lookup, src='Ppf',
                                              t=TD, method='+', amount=0.0))

        created = add_bess_pair(ss, self.bess_bus1, self.bess_bus2, self.p_max_bess_mw,
                                 bus_voltages, ddn_pu=0.0, fdbd_hz=-0.017)
        ss.setup()

        ss.PQ.config.p2p = 1.0; ss.PQ.config.p2i = 0.0; ss.PQ.config.p2z = 0.0
        ss.PQ.config.q2q = 1.0; ss.PQ.config.q2i = 0.0; ss.PQ.config.q2z = 0.0
        ss.PQ.config.pq2z = 0
        ss.Toggle.u.v[:] = 0
        uids = ss.GENROU.idx2uid(AREA_GENS)
        ss.GENROU.M.v[uids] = ss.GENROU.M.v[uids] * K_FROZEN
        ss.GENROU.M.vin[uids] = ss.GENROU.M.vin[uids] * K_FROZEN

        if scen['kind'] == 'gen':
            gen_uid = ss.GENROU.idx2uid([scen['gen']])[0]
            gen_bus = ss.GENROU.bus.v[gen_uid]
            pv_uid_pre = list(ss.PV.bus.v).index(gen_bus)
            p0_nom = float(ss.PV.p0.v[pv_uid_pre])
        else:
            pq_uid_pre = ss.PQ.idx2uid([scen['pq_idx']])[0]
            load_p0_nom = float(ss.PQ.p0.v[pq_uid_pre])

        ss.PQ.p0.v[:] = ss.PQ.p0.v[:] * scen['lambda_L']
        ss.PQ.q0.v[:] = ss.PQ.q0.v[:] * scen['lambda_L']
        ss.PV.p0.v[:] = ss.PV.p0.v[:] * scen['lambda_L']

        alter_uid = ss.Alter.idx2uid([alter_idx])[0]
        if scen['kind'] == 'gen':
            gen_uid = ss.GENROU.idx2uid([scen['gen']])[0]
            gen_bus = ss.GENROU.bus.v[gen_uid]
            pv_uid = list(ss.PV.bus.v).index(gen_bus)
            p0 = float(ss.PV.p0.v[pv_uid])
            ss.Alter.amount.v[alter_uid] = -scen['rho'] * p0
        else:
            ss.Alter.amount.v[alter_uid] = scen['alpha_L'] * load_p0_nom

        ss.TDS.config.tstep = self.tstep
        ss.TDS.config.fixt = 1
        ss.TDS.config.method = 'trapezoid'
        ss.TDS.config.save_every = 0
        ss.TDS.config.no_tqdm = 1

        ss.PFlow.run()
        pflow_ok = bool(ss.PFlow.converged)
        ss.TDS.init()

        esd1_idx = {self.bess_bus1: created[f'bus{self.bess_bus1}']['esd1'],
                    self.bess_bus2: created[f'bus{self.bess_bus2}']['esd1']}
        self.esd1_idx = esd1_idx
        self.esd1_uid1 = ss.ESD1.idx2uid([esd1_idx[self.bess_bus1]])[0]
        self.esd1_uid2 = ss.ESD1.idx2uid([esd1_idx[self.bess_bus2]])[0]
        self.busrocof_buses = list(ss.BusROCOF.bus.v)
        self.bess1_rocof_uid = self.busrocof_buses.index(self.bess_bus1)
        self.bess2_rocof_uid = self.busrocof_buses.index(self.bess_bus2)

        self.ss = ss
        self.tds_failed = not pflow_ok
        self._step_idx = 0
        self._df_peak = 0.0
        self._rocof_peak = 0.0
        self._prev_action = np.zeros(2, dtype=np.float64)
        obs = self._get_obs()
        return obs.astype(np.float32), dict(scenario=scen)

    def _gen_bus_arrays(self):
        # NOTE (found during P2-E6b implementation): ss.BusFreq.bus.v gains 2
        # extra entries (for BESS_BUS_1/2) after add_bess_pair() -- ANDES
        # auto-adds BusFreq for the new PV buses. Slice to the first
        # len(GEN_BUSES) entries (GEN_BUSES are added first, before
        # add_bess_pair() -- verified their order is preserved) so this
        # array is exactly the 10 metrics generators per plan Section 6, not
        # 10 generators + 2 BESS POI buses. p2_common.py had the same latent
        # scope-creep -- fixed there too, DEC-P2-033 (verified empirically
        # to have ZERO impact on any already-frozen df_nadir_hz value
        # beforehand, DEC-P2-030).
        ss = self.ss
        f_gen_hz = np.array([float(v) for v in ss.BusFreq.f.v[:len(GEN_BUSES)]]) * F0_HZ
        rocof_gen_hz_s = np.array([float(v) for v in ss.BusROCOF.Wf_y.v[:len(GEN_BUSES)]]) * F0_HZ
        return f_gen_hz, rocof_gen_hz_s

    def _bess_power_mw(self):
        ss = self.ss
        p1 = float(ss.ESD1.Ipout_y.v[self.esd1_uid1]) * float(ss.ESD1.v.v[self.esd1_uid1]) * 100.0
        p2 = float(ss.ESD1.Ipout_y.v[self.esd1_uid2]) * float(ss.ESD1.v.v[self.esd1_uid2]) * 100.0
        return p1, p2

    def _get_obs(self):
        ss = self.ss
        f1 = float(ss.BusROCOF.f.v[self.bess1_rocof_uid]) * F0_HZ
        r1 = float(ss.BusROCOF.Wf_y.v[self.bess1_rocof_uid]) * F0_HZ
        f2 = float(ss.BusROCOF.f.v[self.bess2_rocof_uid]) * F0_HZ
        r2 = float(ss.BusROCOF.Wf_y.v[self.bess2_rocof_uid]) * F0_HZ
        p1, p2 = self._bess_power_mw()
        f_gen_hz, rocof_gen_hz_s = self._gen_bus_arrays()

        df1n, df2n = (f1 - F0_HZ) / F_REF_HZ, (f2 - F0_HZ) / F_REF_HZ
        r1n, r2n = r1 / R_REF_HZ_S, r2 / R_REF_HZ_S
        p1n, p2n = p1 / self.p_max_bess_mw, p2 / self.p_max_bess_mw

        if self.obs_mode == 'OBS-A':
            return np.array([df1n, r1n, p1n, df2n, r2n, p2n], dtype=np.float64)
        if self.obs_mode == 'OBS-B':
            f_coi = float(np.mean(f_gen_hz))
            rocof_coi = float(np.mean(rocof_gen_hz_s))
            return np.array([df1n, r1n, p1n, df2n, r2n, p2n,
                              (f_coi - F0_HZ) / F_REF_HZ, rocof_coi / R_REF_HZ_S], dtype=np.float64)
        # OBS-C: global
        dfn_all = (f_gen_hz - F0_HZ) / F_REF_HZ
        rn_all = rocof_gen_hz_s / R_REF_HZ_S
        interleaved = np.empty(2 * len(GEN_BUSES), dtype=np.float64)
        interleaved[0::2] = dfn_all
        interleaved[1::2] = rn_all
        return np.concatenate([interleaved, [p1n, p2n]])

    def get_raw_signals(self):
        """Non-normalized signal readout, for raw-vs-normalized logging only
        (Section 5 of the P2-E6b instruction) -- not used by reset()/step()."""
        ss = self.ss
        f1 = float(ss.BusROCOF.f.v[self.bess1_rocof_uid]) * F0_HZ
        r1 = float(ss.BusROCOF.Wf_y.v[self.bess1_rocof_uid]) * F0_HZ
        f2 = float(ss.BusROCOF.f.v[self.bess2_rocof_uid]) * F0_HZ
        r2 = float(ss.BusROCOF.Wf_y.v[self.bess2_rocof_uid]) * F0_HZ
        p1, p2 = self._bess_power_mw()
        f_gen_hz, rocof_gen_hz_s = self._gen_bus_arrays()
        f_coi = float(np.mean(f_gen_hz))
        rocof_coi = float(np.mean(rocof_gen_hz_s))
        return dict(f1_hz=f1, rocof1_hz_s=r1, p1_mw=p1, f2_hz=f2, rocof2_hz_s=r2, p2_mw=p2,
                    f_coi_hz=f_coi, rocof_coi_hz_s=rocof_coi,
                    f_gen_all_hz=f_gen_hz.copy(), rocof_gen_all_hz_s=rocof_gen_hz_s.copy())

    def _compute_reward(self, tds_failed_this_step):
        f_gen_hz, rocof_gen_hz_s = self._gen_bus_arrays()
        df_gen = f_gen_hz - F0_HZ
        e_f = float(np.max(np.abs(df_gen))) / F_REF_HZ
        e_r = float(np.max(np.abs(rocof_gen_hz_s))) / R_REF_HZ_S
        i_unsafe = 1.0 if (np.max(np.abs(df_gen)) > I_UNSAFE_DF_HZ or
                            np.max(np.abs(rocof_gen_hz_s)) > I_UNSAFE_ROCOF_HZ_S) else 0.0
        i_fail = 1.0 if tds_failed_this_step else 0.0
        r = -(e_f ** 2 + e_r ** 2 + 2.0 * max(e_f, e_r) ** 2) - I_UNSAFE_WEIGHT * i_unsafe - I_FAIL_WEIGHT * i_fail
        self._df_peak = max(self._df_peak, float(np.max(np.abs(df_gen))))
        self._rocof_peak = max(self._rocof_peak, float(np.max(np.abs(rocof_gen_hz_s))))
        return r, dict(e_f=e_f, e_r=e_r, i_unsafe=i_unsafe, i_fail=i_fail)

    def step(self, action):
        assert self.ss is not None, "call reset() first"
        a1, a2 = float(np.clip(action[0], -1.0, 1.0)), float(np.clip(action[1], -1.0, 1.0))
        ss, tds, dae = self.ss, self.ss.TDS, self.ss.dae

        f1 = float(ss.BusROCOF.f.v[self.bess1_rocof_uid]) * F0_HZ
        f2 = float(ss.BusROCOF.f.v[self.bess2_rocof_uid]) * F0_HZ
        p_droop1 = -self.kd_star * (f1 - F0_HZ)
        p_droop2 = -self.kd_star * (f2 - F0_HZ)
        p_rl1 = a1 * self.p_rl_max_mw
        p_rl2 = a2 * self.p_rl_max_mw
        p_total1_preclip, p_total1 = combine_command(p_droop1, p_rl1, self.p_max_bess_mw)
        p_total2_preclip, p_total2 = combine_command(p_droop2, p_rl2, self.p_max_bess_mw)

        ss.DG.set_paux(ss, self.esd1_idx[self.bess_bus1], p_total1 / 100.0)
        ss.DG.set_paux(ss, self.esd1_idx[self.bess_bus2], p_total2 / 100.0)

        step_failed = False
        tds.do_switch()
        tds.calc_h()
        if tds.itm_step():
            dae.t += tds.h
        else:
            tds.calc_h()
            if tds.h == 0:
                step_failed = True
                self.tds_failed = True

        self._step_idx += 1
        obs = self._get_obs()
        reward, reward_terms = self._compute_reward(step_failed)

        # seed66 (DEC-P2-041 pending): action-rate smoothness penalty, OFF by default
        # (weight=0.0 -> smooth_penalty=0.0 always, reward identical to seeds 11-55).
        cur_action = np.array([a1, a2], dtype=np.float64)
        smooth_penalty = self.action_smoothness_weight * float(np.sum((cur_action - self._prev_action) ** 2))
        reward -= smooth_penalty
        self._prev_action = cur_action

        terminated = bool(self.tds_failed)
        truncated = (not terminated) and (self._step_idx >= self.n_int_steps)

        if terminated or truncated:
            r_terminal = -TERMINAL_WEIGHT * ((self._df_peak / F_REF_HZ) ** 2 +
                                              (self._rocof_peak / R_REF_HZ_S) ** 2)
            reward += r_terminal
        else:
            r_terminal = 0.0

        info = dict(t=float(dae.t), p_total_mw=(p_total1, p_total2), tds_success=(not self.tds_failed),
                    df_peak=self._df_peak, rocof_peak=self._rocof_peak, r_terminal=r_terminal,
                    p_droop_mw=(p_droop1, p_droop2), p_rl_mw=(p_rl1, p_rl2),
                    p_total_preclip_mw=(p_total1_preclip, p_total2_preclip),
                    smooth_penalty=smooth_penalty,
                    **reward_terms)
        return obs.astype(np.float32), float(reward), terminated, truncated, info
