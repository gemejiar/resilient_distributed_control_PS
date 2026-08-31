#!/usr/bin/env python
"""
P2-E6a -- revised TD3-residual environment: droop* + TD3 residual.

P_total,i = clip(P_droop,i + P_RL,i, -Pmax, +Pmax)
P_droop,i = -Kd* * df_i,local              (Kd* = 4694.4 MW/Hz, frozen DEC-P2-024)
P_RL,i    = a_i * P_RL,max,   a_i in [-1,1] (P_RL,max = 0.25*Pmax, frozen this stage)

Replaces the discarded `F+R + TD3 residual` architecture (DEC-P2-025/026) --
`K_f`/`K_r` are NOT used here. Frozen config (unchanged, DEC-P2-018/020/022/
024/026): BESS buses 16/20, Tc=tstep=5ms, Pmax=293.4MW, tip/BusROCOF
unchanged, low-inertia case.

This module implements ONLY the architecture mechanics (action -> command ->
ANDES step -> observation), reusing the exact same case-construction and
itm_step()-based integration loop already validated in
p2_common.run_physical_scenario_tc() (Section 26 of the plan: reuse P1's
itm_step pattern, do not reinvent it). It is deliberately NOT wired for
training yet (no seeding/vectorization/termination tuning) -- P2-E6a is a
smoke-test-only stage (see stage_p2e6a_td3_residual_architecture_smoke.py),
not P2-E10 (training).

Observation (8 signals, POI+COI style, OBS-B candidate per plan Section 9,
adapted from legacy buses 13/12 to the frozen buses 16/20 -- NOT the final
ablation-selected observation, P2-E7 has not run; provided only so the
smoke tests can check "observations well-formed, no NaN/Inf"):

    [ df_bus16, RoCoF_bus16, P_BESS1,
      df_bus20, RoCoF_bus20, P_BESS2,
      df_COI,   RoCoF_COI ]

f_COI/RoCoF_COI use the same UNWEIGHTED-mean proxy already declared
explicitly throughout this campaign (true H-weighted COI not implemented).

Reward uses the already-frozen Section 6 formula of the plan (no new
tuning decision -- included only so step() returns a well-formed value,
NOT evaluated or used for any decision in this stage).
"""
import numpy as np
import andes

from p2_common import (BASE_CASE, ROCOF_PARAMS, GEN_BUSES, BESS_ADMISSIBLE_BUSES,
                        AREA_GENS, K_FROZEN, F0_HZ, TD, TF_INITIAL,
                        add_bess_pair, natural_bus_voltages_at_lambda)

F_REF_HZ = 0.5
R_REF_HZ_S = 1.0


def combine_command(p_droop_mw, p_rl_mw, p_max_bess_mw):
    """Pure function form of P_total = clip(P_droop + P_RL, -Pmax, +Pmax) --
    exposed standalone so the clipping arithmetic can be unit-tested with
    synthetic values, independent of whether a live ANDES disturbance
    happens to be large enough to saturate."""
    preclip = p_droop_mw + p_rl_mw
    return preclip, max(-p_max_bess_mw, min(p_max_bess_mw, preclip))


class P2ResidualEnv:
    def __init__(self, kind, gen=None, rho=None, bus=None, alpha_L=None, lambda_L=1.00,
                 p_max_bess_mw=293.4, kd_star_mw_per_hz=4694.4, p_rl_max_frac=0.25,
                 tc=0.005, tstep=0.005, bess_bus1=16, bess_bus2=20, tf=TF_INITIAL,
                 quiet=True):
        assert kind in ('gen', 'load')
        assert abs(tc - tstep) < 1e-12, "P2-E6a freezes Tc=tstep=5ms -- action every integration step"
        self.kind, self.gen, self.rho = kind, gen, rho
        self.bus, self.alpha_L, self.lambda_L = bus, alpha_L, lambda_L
        self.p_max_bess_mw = p_max_bess_mw
        self.kd_star = kd_star_mw_per_hz
        self.p_rl_max_mw = p_rl_max_frac * p_max_bess_mw
        self.tc, self.tstep, self.tf = tc, tstep, tf
        self.bess_bus1, self.bess_bus2 = bess_bus1, bess_bus2
        self.quiet = quiet
        self.action_dim = 2
        self.obs_dim = 8
        self.n_int_steps = int(round(tf / tstep))
        self.ctrl_period_steps = max(1, int(round(tc / tstep)))
        self._step_idx = 0
        self.ss = None

    def reset(self):
        bus_voltages = natural_bus_voltages_at_lambda(self.lambda_L)
        ss = andes.load(BASE_CASE, setup=False, no_output=self.quiet, default_config=True)
        for b in GEN_BUSES:
            ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))
        for b in BESS_ADMISSIBLE_BUSES:
            ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))

        if self.kind == 'gen':
            gov_uid = ss.TGOV1N.syn.v.index(self.gen)
            gov_idx = ss.TGOV1N.idx.v[gov_uid]
            alter_idx = ss.add('Alter', dict(model='TGOV1N', dev=gov_idx, src='paux0',
                                              t=TD, method='=', amount=0.0))
        else:
            pq_idx = ss.PQ.find_idx(keys='bus', values=[self.bus])[0]
            alter_idx = ss.add('Alter', dict(model='PQ', dev=pq_idx, src='Ppf',
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

        if self.kind == 'gen':
            gen_uid = ss.GENROU.idx2uid([self.gen])[0]
            gen_bus = ss.GENROU.bus.v[gen_uid]
            pv_uid_pre = list(ss.PV.bus.v).index(gen_bus)
            p0_nom = float(ss.PV.p0.v[pv_uid_pre])
        else:
            pq_uid_pre = list(ss.PQ.bus.v).index(self.bus)
            load_p0_nom = float(ss.PQ.p0.v[pq_uid_pre])

        ss.PQ.p0.v[:] = ss.PQ.p0.v[:] * self.lambda_L
        ss.PQ.q0.v[:] = ss.PQ.q0.v[:] * self.lambda_L
        ss.PV.p0.v[:] = ss.PV.p0.v[:] * self.lambda_L

        alter_uid = ss.Alter.idx2uid([alter_idx])[0]
        if self.kind == 'gen':
            gen_uid = ss.GENROU.idx2uid([self.gen])[0]
            gen_bus = ss.GENROU.bus.v[gen_uid]
            pv_uid = list(ss.PV.bus.v).index(gen_bus)
            p0 = float(ss.PV.p0.v[pv_uid])
            ss.Alter.amount.v[alter_uid] = -self.rho * p0
        else:
            ss.Alter.amount.v[alter_uid] = self.alpha_L * load_p0_nom

        ss.TDS.config.tstep = self.tstep
        ss.TDS.config.fixt = 1
        ss.TDS.config.method = 'trapezoid'
        ss.TDS.config.save_every = 0
        ss.TDS.config.no_tqdm = 1

        ss.PFlow.run()
        self.pflow_ok = bool(ss.PFlow.converged)
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
        self.tds_failed = False
        self._step_idx = 0
        return self._get_obs()

    def _get_obs(self):
        ss = self.ss
        f1 = float(ss.BusROCOF.f.v[self.bess1_rocof_uid]) * F0_HZ
        r1 = float(ss.BusROCOF.Wf_y.v[self.bess1_rocof_uid]) * F0_HZ
        f2 = float(ss.BusROCOF.f.v[self.bess2_rocof_uid]) * F0_HZ
        r2 = float(ss.BusROCOF.Wf_y.v[self.bess2_rocof_uid]) * F0_HZ
        p1 = float(ss.ESD1.Ipout_y.v[self.esd1_uid1]) * float(ss.ESD1.v.v[self.esd1_uid1]) * 100.0
        p2 = float(ss.ESD1.Ipout_y.v[self.esd1_uid2]) * float(ss.ESD1.v.v[self.esd1_uid2]) * 100.0
        f_gen_hz = np.array([float(v) for v in ss.BusFreq.f.v]) * F0_HZ
        rocof_gen_hz_s = np.array([float(v) for v in ss.BusROCOF.Wf_y.v[:len(GEN_BUSES)]]) * F0_HZ
        f_coi = float(np.mean(f_gen_hz))
        rocof_coi = float(np.mean(rocof_gen_hz_s))
        obs = np.array([f1 - F0_HZ, r1, p1,
                         f2 - F0_HZ, r2, p2,
                         f_coi - F0_HZ, rocof_coi], dtype=np.float64)
        return obs

    def _compute_reward(self, obs):
        # Section 6 of the plan, already frozen -- included for completeness
        # only, NOT evaluated/used for any decision in P2-E6a.
        e_f = max(abs(obs[0]), abs(obs[3]), abs(obs[6])) / F_REF_HZ
        e_r = max(abs(obs[1]), abs(obs[4]), abs(obs[7])) / R_REF_HZ_S
        return -(e_f ** 2 + e_r ** 2 + 2.0 * max(e_f, e_r) ** 2)

    def step(self, action):
        assert self.ss is not None, "call reset() first"
        a1, a2 = float(action[0]), float(action[1])
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

        for _ in range(self.ctrl_period_steps):
            tds.do_switch()
            tds.calc_h()
            if tds.itm_step():
                dae.t += tds.h
            else:
                tds.calc_h()
                if tds.h == 0:
                    self.tds_failed = True
                    break

        self._step_idx += 1
        obs = self._get_obs()
        reward = self._compute_reward(obs)
        terminated = self.tds_failed
        truncated = self._step_idx >= self.n_int_steps
        info = dict(
            p_droop_mw=(p_droop1, p_droop2), p_rl_mw=(p_rl1, p_rl2),
            p_total_preclip_mw=(p_total1_preclip, p_total2_preclip),
            p_total_mw=(p_total1, p_total2),
            tds_success=(not self.tds_failed), t=float(dae.t),
        )
        return obs, reward, terminated, truncated, info
