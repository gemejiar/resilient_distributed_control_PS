#!/usr/bin/env python
"""
Paper_2 shared utilities -- physics/case-construction helpers.

Ported from Paper_1/src/run_ffc_study.py (P2 plan Section 26: these functions
are reusable "as implementation reference", but P2 keeps its own copy and
never imports from Paper_1/). Logic is preserved exactly, including the two
ANDES-API correctness fixes discovered during P1 (Bus.v0 vs Bus.v.v for new
zero-injection devices; M.v/M.vin dual scaling for andes.io.dump()). Only the
case paths and BESS bus/size arguments are parameterized instead of hardcoded
to P1's frozen values.
"""
import re
import time

import numpy as np
import andes

BASE_CASE = "Paper_2/cases/ieee39/base/ieee39_full.xlsx"
VARIANT_CASE = "Paper_2/cases/ieee39/variants/ieee39_low_inertia.xlsx"

# Same measurement layer as Paper_1 (SS14/SS21, SS7.2 Paso A / S-04):
GEN_BUSES = list(range(30, 40))
BESS_ADMISSIBLE_BUSES = list(range(1, 30))
AREA_GENS = [f"GENROU_{i}" for i in range(1, 10)]  # excludes GENROU_10 (bus 39, slack)

# DEC-P2-030/DEC-P2-033: ss.BusFreq gains 2 extra auto-added entries (for
# BESS_BUS_1/2) after add_bess_pair() -- ANDES auto-adds a BusFreq device
# for every new PV(StaticGen) bus. The GEN_BUSES BusFreq entries are always
# added FIRST (before add_bess_pair() runs), so every read of
# ss.BusFreq.f.v below is sliced to [:len(GEN_BUSES)] to exclude the BESS
# POI buses from any "worst-system"/max_i-over-metrics-generators
# computation, matching ss.BusROCOF.Wf_y.v's slicing (which already needed
# this, since BusROCOF is also added for BESS_ADMISSIBLE_BUSES).
# Verified (DEC-P2-030) that this scope creep had ZERO impact on every
# already-frozen df_nadir_hz value checked -- the frequency minimum never
# occurs at the actively-compensated BESS buses.

ROCOF_PARAMS = dict(Tf=0.02, Tw=0.02, Tr=0.05)  # P2 plan Section 8: Tc design must
                                                  # re-examine this against Tc<100ms

K_FROZEN = 0.50  # reused from Paper_1 (same low-inertia physics, verified in P2-E1)
F0_HZ = 60.0
TD = 1.0
TF_INITIAL = 6.0
TF_EXTENDED = 10.0
T_CONTROL_DEFAULT = 0.1  # Tc=100ms, same as Paper_1; P2-E4 investigates 50/20ms (Section 8)

# Reused from Paper_1 DEC-P1-004 (S-01 revision) -- LI-1 criterion 4 thresholds
DF_NADIR_MIN_HZ = 0.040
ROCOF_MIN_HZ_S = 0.5
RHO_LI1 = 0.80

# --- P2-E6 freeze (DEC-P2-018): BESS relocated from the original P2-E1 placement
# (buses 13/12, reused from Paper_1 per DEC-P2-002) after a controllability
# screening (DEC-P2-017, open-loop) and closed-loop F+R validation (DEC-P2-018)
# showed the original pair materially under-uses the physical architecture's
# potential for gen_severe (only +7.7%/+3.7% vs +29.6%/+20.1% at the new pair,
# same Kf/Kr/Tc/Pmax) while load_severe remains at 0%/0% at BOTH pairs (a
# separate, unresolved structural limitation, not fixed by relocation --
# DEC-P2-014/015/016). All P2-E1..E6 results computed before DEC-P2-018 used
# BESS_BUS_1=13, BESS_BUS_2=12 and remain valid as a historical snapshot of
# that placement; they are not retroactively reinterpreted.
BESS_BUS_1 = 16
BESS_BUS_2 = 20

# --- P2-E2 freeze (DEC-P2-003): train/validation/test splits, electrical
# distance (Dijkstra, sum|X|) from BESS_BUS_1/2, methodology mirrors
# Paper_1 SS7.2/Section 7. PQ_5 (bus 12) is co-located with BESS_BUS_2 itself
# (dist=0.0000) and is EXCLUDED from every split -- perturbing a bus that
# hosts an actuator is a degenerate near-field case, not a representative
# disturbance.
G_VALIDATION_P2 = ['GENROU_6']   # bus 35, dist=0.0830 (median of the 9 non-slack gens)
G_TEST_P2 = ['GENROU_9', 'GENROU_3']
# GENROU_9: bus 38, Sn=1684.1 MVA (largest, same as Paper_1's G_A/G_A_PREVIEW),
#           dist=0.1602 (farthest from BESS among all 9) -- hardest case.
# GENROU_3: bus 32, Sn=843.7 MVA, dist=0.0243 (closest to BESS) -- near-field case.
G_TRAIN_P2 = ['GENROU_1', 'GENROU_2', 'GENROU_4', 'GENROU_5', 'GENROU_7', 'GENROU_8']

L_VALIDATION_P2 = ['PQ_10']      # bus 21, P0=274.0 MW, dist=0.0547 (median of the 19 loads)
L_TEST_P2 = ['PQ_1', 'PQ_16']
# PQ_1:  bus 3,  P0=600.0 MW, dist=0.0443 -- large load, close-ish to BESS.
# PQ_16: bus 28, P0=206.0 MW, dist=0.1295 -- far from BESS (2nd-farthest overall).
# Deliberately NOT Paper_1's L_A/L_B (bus 20 / bus 29) -- P2 picks its own test
# loads for maximal independence from P1's specific choices; PQ_9 (bus 20,
# P1's L_A) and PQ_17 (bus 29, P1's L_B) fall into P2's TRAIN pool instead.
L_TRAIN_P2 = ['PQ_2', 'PQ_3', 'PQ_4', 'PQ_6', 'PQ_7', 'PQ_8', 'PQ_9', 'PQ_11',
              'PQ_12', 'PQ_13', 'PQ_14', 'PQ_15', 'PQ_17', 'PQ_18', 'PQ_19']
L_EXCLUDED_P2 = ['PQ_5']  # bus 12 == BESS_BUS_2, co-located, excluded from all splits

# Operating point (lambda_L) splits (Section 11.3 of the P2 plan):
OP_TRAIN_RANGE_P2 = (0.90, 1.10)          # sampled continuously, U(0.90, 1.10)
OP_VALIDATION_P2 = (0.95, 1.00, 1.05)     # discrete, inside training range
OP_TEST_OUTSIDE_P2 = (0.88, 1.12)         # discrete, OUTSIDE training range (P2-T3/4/7/8)


def build_case(base_case=BASE_CASE, k=None, contingency_gen=None, rho=None, quiet=True):
    """Construct the experimental System: BusROCOF at both bus sets, PQ ->
    constant power, preexisting Toggle disabled, optional single-generator
    Alter contingency, optional inertia scaling k on AREA_GENS."""
    ss = andes.load(base_case, setup=False, no_output=quiet, default_config=True)

    for b in GEN_BUSES:
        ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))
    for b in BESS_ADMISSIBLE_BUSES:
        ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))

    alter_idx = None
    if contingency_gen is not None:
        gov_uid = ss.TGOV1N.syn.v.index(contingency_gen)
        gov_idx = ss.TGOV1N.idx.v[gov_uid]
        alter_idx = ss.add('Alter', dict(model='TGOV1N', dev=gov_idx,
                                          src='paux0', t=TD, method='=', amount=0.0))

    ss.setup()

    ss.PQ.config.p2p = 1.0
    ss.PQ.config.p2i = 0.0
    ss.PQ.config.p2z = 0.0
    ss.PQ.config.q2q = 1.0
    ss.PQ.config.q2i = 0.0
    ss.PQ.config.q2z = 0.0
    ss.PQ.config.pq2z = 0

    ss.Toggle.u.v[:] = 0

    if k is not None:
        uids = ss.GENROU.idx2uid(AREA_GENS)
        ss.GENROU.M.v[uids] = ss.GENROU.M.v[uids] * k
        # M has power=True; andes.io.dump() serializes from .vin, not .v --
        # both must be scaled or a dumped variant silently reverts (DEC-P1-005).
        ss.GENROU.M.vin[uids] = ss.GENROU.M.vin[uids] * k

    if contingency_gen is not None and rho is not None:
        gen_uid = ss.GENROU.idx2uid([contingency_gen])[0]
        gen_bus = ss.GENROU.bus.v[gen_uid]
        pv_uid = list(ss.PV.bus.v).index(gen_bus)
        p0 = ss.PV.p0.v[pv_uid]
        alter_uid = ss.Alter.idx2uid([alter_idx])[0]
        ss.Alter.amount.v[alter_uid] = -rho * p0

    ss.TDS.config.tstep = 1 / 60
    ss.TDS.config.fixt = 1
    ss.TDS.config.method = 'trapezoid'
    ss.TDS.config.save_every = 1

    return ss


def h_report(ss):
    M = ss.GENROU.M.v
    H = M / 2.0
    h_map = dict(zip(ss.GENROU.idx.v, H))
    h_total = float(H.sum())
    h_bus39 = float(h_map['GENROU_10'])
    return h_total, h_bus39, h_map


def _find_ordered(plt, pattern, first_n=None):
    """See Paper_1/src/run_ffc_study.py for the full rationale (BusROCOF
    shares FreqMeasurement numbering with pre-existing BusFreq devices)."""
    found_idx, found_names = plt.find(pattern)
    pairs = []
    for i, n in zip(found_idx, found_names):
        m = re.search(r'(\d+)$', n)
        if m:
            pairs.append((int(m.group(1)), i))
    pairs.sort()
    if first_n is not None:
        pairs = pairs[:first_n]
    return [p[1] for p in pairs]


def worst_bus_freq_rocof(ss):
    """Worst-system nadir/RoCoF over GEN_BUSES using BusFreq.f / BusROCOF.Wf_y."""
    t = np.array(ss.TDS.plt.t)
    f_addrs = _find_ordered(ss.TDS.plt, r'^f BusFreq \d+$', first_n=len(GEN_BUSES))
    rocof_addrs = _find_ordered(ss.TDS.plt, r'^Wf_y BusROCOF \d+$', first_n=len(GEN_BUSES))
    assert len(f_addrs) == len(GEN_BUSES), f"expected {len(GEN_BUSES)} BusFreq, got {len(f_addrs)}"
    assert len(rocof_addrs) == len(GEN_BUSES), f"expected {len(GEN_BUSES)} BusROCOF, got {len(rocof_addrs)}"

    f_pu = ss.TDS.plt.get_values(f_addrs)
    rocof_pu = ss.TDS.plt.get_values(rocof_addrs)

    f_hz = f_pu * F0_HZ
    df_hz = f_hz - F0_HZ
    rocof_hz_s = rocof_pu * F0_HZ

    worst_per_t = np.min(f_hz, axis=1)
    i_nadir = int(np.argmin(worst_per_t))
    f_nadir = float(worst_per_t[i_nadir])
    t_nadir = float(t[i_nadir])
    df_nadir = f_nadir - F0_HZ
    rocof_max = float(np.max(np.abs(rocof_hz_s)))
    return dict(t=t, f_hz=f_hz, df_hz=df_hz, rocof_hz_s=rocof_hz_s,
                f_nadir=f_nadir, df_nadir=df_nadir, t_nadir=t_nadir, rocof_max=rocof_max)


def worst_freq_rocof_stepped(ss, tf, dt=1 / 60):
    """Drive TDS manually with itm_step() (Paper_1 DEC-P1-007: TDS.run()'s
    plt/TDSData buffer proved unreliable in this environment -- the
    simulation itself completes correctly (dae.t reaches tf, TDS.run()
    returns True) but ss.TDS.plt intermittently stays None depending on
    invocation context, breaking any post-hoc read of the trajectory. Reading
    BusFreq.f.v / BusROCOF.Wf_y.v LIVE after each itm_step(), exactly as
    Paper_1's run_test_scenario() already did for the T1-T8 test matrix, has
    no such dependency and is the pattern P2 standardizes on throughout."""
    dae = ss.dae
    tds = ss.TDS
    f_nadir = F0_HZ
    rocof_max = 0.0
    t_nadir = 0.0
    n_gen = len(GEN_BUSES)
    tds_failed = False
    n_steps = int(round(tf / dt))
    for step in range(n_steps):
        target_t = min((step + 1) * dt, tf)
        n_inner = 0
        while float(dae.t) < target_t - 1e-9:
            tds.do_switch()
            tds.calc_h()
            if tds.itm_step():
                dae.t += tds.h
            else:
                tds.calc_h()
                if tds.h == 0:
                    tds_failed = True
                    break
            n_inner += 1
            if n_inner > 4000:
                tds_failed = True
                break
        if tds_failed:
            break
        f_gen_hz = np.array([float(v) for v in ss.BusFreq.f.v[:len(GEN_BUSES)]]) * F0_HZ
        rocof_gen_hz_s = np.array([float(v) for v in ss.BusROCOF.Wf_y.v[:n_gen]]) * F0_HZ
        f_min = float(np.min(f_gen_hz))
        if f_min < f_nadir:
            f_nadir = f_min
            t_nadir = float(dae.t)
        rocof_max = max(rocof_max, float(np.max(np.abs(rocof_gen_hz_s))))
    return dict(f_nadir=f_nadir, df_nadir=f_nadir - F0_HZ, t_nadir=t_nadir,
                rocof_max=rocof_max, tds_failed=tds_failed, t_final=float(dae.t))


def verify_li1_gate(k=K_FROZEN, contingency_gen='GENROU_1', rho=RHO_LI1, tf=TF_INITIAL,
                     verbose=True):
    """Re-verify Gate LI-1 (Paper_1 SS5.3 criteria) on P2's OWN case copy, at
    the same frozen configuration already validated in Paper_1 (DEC-P1-002..
    004). This is a consistency check that P2's independently-ported code
    reproduces the same physics -- not a re-litigation of the threshold."""
    result = {'k': k, 'contingency_gen': contingency_gen, 'rho': rho, 'tf': tf}

    ss_base = build_case(k=None, quiet=True)
    ss_base.PFlow.run()
    base_pflow_ok = ss_base.PFlow.converged
    ss_base.TDS.init()
    ss_base.EIG.run()
    base_mu = np.array(ss_base.EIG.mu)
    base_n_pos = int(ss_base.EIG.n_positive)
    base_max_real = float(base_mu.real.max())

    ss = build_case(k=k, contingency_gen=contingency_gen, rho=rho, quiet=True)
    h_total, h_bus39, h_map = h_report(ss)

    ss.PFlow.run()
    result['pflow_converged'] = bool(ss.PFlow.converged)

    ss.TDS.init()
    result['tds_initialized'] = True

    ss.EIG.run()
    var_mu = np.array(ss.EIG.mu)
    var_n_pos = int(ss.EIG.n_positive)
    var_max_real = float(var_mu.real.max())
    result['eig_baseline_n_positive'] = base_n_pos
    result['eig_baseline_max_real'] = base_max_real
    result['eig_variant_n_positive'] = var_n_pos
    result['eig_variant_max_real'] = var_max_real
    result['eig_pass'] = (var_n_pos <= base_n_pos) and (var_max_real <= base_max_real + 1e-6)

    metrics = worst_freq_rocof_stepped(ss, tf=tf, dt=1 / 60)
    result['tds_initialized'] = result['tds_initialized'] and (not metrics['tds_failed'])
    result['f_nadir_hz'] = metrics['f_nadir']
    result['df_nadir_hz'] = metrics['df_nadir']
    result['t_nadir_s'] = metrics['t_nadir']
    result['rocof_max_hz_s'] = metrics['rocof_max']
    result['h_total_s'] = h_total
    result['h_bus39_s'] = h_bus39
    result['h_area_map'] = h_map

    result['criterion4_pass'] = (abs(metrics['df_nadir']) >= DF_NADIR_MIN_HZ and
                                  metrics['rocof_max'] >= ROCOF_MIN_HZ_S)

    still_decreasing_at_tf = metrics['t_nadir'] >= tf - 1e-6
    result['t_nadir_near_end'] = metrics['t_nadir'] > tf - 0.5
    result['still_decreasing_at_tf'] = bool(still_decreasing_at_tf)
    result['needs_horizon_extension'] = bool(result['t_nadir_near_end'] or still_decreasing_at_tf)

    result['gate_pass'] = (result['pflow_converged'] and result['tds_initialized'] and
                            result['eig_pass'] and result['criterion4_pass'])

    if verbose:
        print(f"--- Gate LI-1 (P2 re-verification), k={k}, tf={tf}s ---")
        print(f"PFlow converged: {result['pflow_converged']}")
        print(f"TDS initialized: {result['tds_initialized']}")
        print(f"EIG baseline  n_positive={base_n_pos}, max_real={base_max_real:.4g}")
        print(f"EIG variant   n_positive={var_n_pos}, max_real={var_max_real:.4g}  -> pass={result['eig_pass']}")
        print(f"H_total={h_total:.2f} s (bus39 share={h_bus39/h_total*100:.1f}%)")
        print(f"f_nadir={metrics['f_nadir']:.4f} Hz (df={metrics['df_nadir']:.4f} Hz) at t={metrics['t_nadir']:.3f}s")
        print(f"RoCoF_max={metrics['rocof_max']:.4f} Hz/s")
        print(f"Criterion 4 (|df|>={DF_NADIR_MIN_HZ*1000:.0f}mHz & RoCoF>={ROCOF_MIN_HZ_S}Hz/s): {result['criterion4_pass']}")
        print(f"Needs horizon extension: {result['needs_horizon_extension']}")
        print(f"GATE LI-1 PASS: {result['gate_pass']}")

    return result, ss


def save_variant(k=K_FROZEN, path=VARIANT_CASE, base_case=BASE_CASE):
    """Write the frozen low-inertia variant to disk: base case + BusROCOF
    (both bus sets) + PQ->constant power + Toggle disabled + inertia scaled
    by k on AREA_GENS. No BESS, no per-generator Alter."""
    ss = build_case(base_case=base_case, k=k, contingency_gen=None, quiet=True)
    ok = andes.io.dump(ss, 'xlsx', full_path=path, overwrite=True)
    return ok, ss


def natural_bus_voltages(k=K_FROZEN):
    """Solve PFlow on the low-inertia case WITHOUT any BESS and return the
    per-bus solved voltage magnitude (Bus.v.v, NOT Bus.v0.v -- see
    Paper_1 DEC-P1-006 for the failure mode this avoids)."""
    ss = build_case(k=k, contingency_gen=None, quiet=True)
    ss.PFlow.run()
    return {b: float(ss.Bus.v.v[list(ss.Bus.idx.v).index(b)]) for b in BESS_ADMISSIBLE_BUSES}


def natural_bus_voltages_at_lambda(lambda_L, k=K_FROZEN):
    ss = build_case(k=k, contingency_gen=None, quiet=True)
    ss.PQ.p0.v[:] = ss.PQ.p0.v[:] * lambda_L
    ss.PQ.q0.v[:] = ss.PQ.q0.v[:] * lambda_L
    ss.PV.p0.v[:] = ss.PV.p0.v[:] * lambda_L
    ss.PFlow.run()
    return {b: float(ss.Bus.v.v[list(ss.Bus.idx.v).index(b)]) for b in BESS_ADMISSIBLE_BUSES}


def add_bess_pair(ss, bus1, bus2, p_max_bess_mw, bus_voltages, ddn_pu=0.0, fdbd_hz=-0.017):
    """Add PV(StaticGen)+ESD1 at two buses, pre-setup. `bus_voltages` must
    come from natural_bus_voltages()/natural_bus_voltages_at_lambda().

    DEC-P1-024/DEC-P2-004/DEC-P2-005 correction: ESD1's active-power path
    (Pext0 -> Psum -> Ipul -> Ipout_y -> bus injection `-Ipout_y*v`) has NO
    `Sn` factor anywhere (verified against andes/models/distributed/pvd1.py)
    -- it operates entirely in SYSTEM base (Sb=100 MVA), and the true hard
    ceiling on deliverable power is set by `pmx` (a power-hard-limit
    parameter, also in system-base pu), not by `Sn`. `pmx` MUST therefore be
    set to `p_max_bess_mw/100.0` here (previously hardcoded to a fixed 1.0,
    silently capping every BESS at ~100 MW regardless of the intended
    P_max,BESS -- this was never exercised in Paper_1, which never varied
    P_max,BESS after freezing it once). `Sn` is kept at `p_max_bess_mw` for
    device-rating bookkeeping/labeling only; it does not, by itself, change
    delivered power or the saturation ceiling."""
    created = {}
    p_pu = p_max_bess_mw / 100.0  # system base (100 MVA)
    for bus in (bus1, bus2):
        bus_uid = list(ss.Bus.idx.v).index(bus)
        vn = float(ss.Bus.Vn.v[bus_uid])
        v0 = bus_voltages[bus]
        pv_idx = ss.add('PV', dict(bus=bus, Vn=vn, Sn=max(p_max_bess_mw, 100.0),
                                    p0=0.0, q0=0.0, pmax=p_pu, pmin=0.0,
                                    qmax=0.3, qmin=-0.3, v0=v0, ra=0.0, xs=0.05))
        esd_idx = ss.add('ESD1', dict(bus=bus, gen=pv_idx, Sn=p_max_bess_mw, fn=60.0, xc=1.0,
                                       pqflag=1, pmx=p_pu, qmx=0.33, qmn=-0.33,
                                       v0=0.8, v1=1.1, dqdv=-0.01, fdbd=fdbd_hz, ddn=ddn_pu,
                                       ialim=1.3, vt0=0.88, vt1=0.90, vt2=1.1, vt3=1.2,
                                       ft0=59.5, ft1=59.7, ft2=60.3, ft3=60.5,
                                       gammap=1.0, gammaq=1.0, Tf=1.0,
                                       SOCmin=0.0, SOCmax=1.0, SOCinit=0.5, En=100.0,
                                       EtaC=1.0, EtaD=1.0))
        created[f'bus{bus}'] = dict(pv=pv_idx, esd1=esd_idx)
    return created


def run_command_step_response(p_max_bess_mw, target_bus, command_mw, tf=1.0, tstep=0.005,
                               t_step=0.1, bess_bus1=BESS_BUS_1, bess_bus2=BESS_BUS_2,
                               quiet=True):
    """P2-E3A/P2-E3B shared driver: open-loop actuator step test, NO closed
    frequency loop and NO Alter contingency (system stays at nominal
    frequency throughout) -- isolates the ESD1 command->power path itself
    from any frequency-feedback effect. Only `target_bus`'s Pext0 is driven
    (step from 0 to `command_mw` at t=t_step, held to tf); the other BESS is
    kept at a 0 command the whole time. Uses the mandatory power convention
    (Sb=100 MVA system base, see add_bess_pair()/DEC-P2-004/005/006):
    Pext0_command_pu = command_MW/100.0, P_delivered_MW = Ipout_y*v*100.0.

    Returns the full trajectory (t, p_command_mw, p_delivered_mw,
    bus_voltage, ipout_y) at fixed resolution `tstep` -- used by P2-E3A for
    the steady-state endpoint (calibration) and by P2-E3B for the transient
    (delay/rise/settling/overshoot)."""
    assert target_bus in (bess_bus1, bess_bus2)
    other_bus = bess_bus2 if target_bus == bess_bus1 else bess_bus1

    bus_voltages = natural_bus_voltages_at_lambda(1.00)

    ss = andes.load(BASE_CASE, setup=False, no_output=quiet, default_config=True)
    for b in GEN_BUSES:
        ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))

    created = add_bess_pair(ss, bess_bus1, bess_bus2, p_max_bess_mw, bus_voltages,
                             ddn_pu=0.0, fdbd_hz=-0.017)
    ss.setup()

    ss.PQ.config.p2p = 1.0; ss.PQ.config.p2i = 0.0; ss.PQ.config.p2z = 0.0
    ss.PQ.config.q2q = 1.0; ss.PQ.config.q2i = 0.0; ss.PQ.config.q2z = 0.0
    ss.PQ.config.pq2z = 0
    ss.Toggle.u.v[:] = 0

    ss.TDS.config.tstep = tstep
    ss.TDS.config.fixt = 1
    ss.TDS.config.method = 'trapezoid'
    ss.TDS.config.save_every = 0
    ss.TDS.config.no_tqdm = 1

    ss.PFlow.run()
    pflow_ok = bool(ss.PFlow.converged)
    ss.TDS.init()

    esd1_idx = {bess_bus1: created[f'bus{bess_bus1}']['esd1'],
                bess_bus2: created[f'bus{bess_bus2}']['esd1']}
    target_uid = ss.ESD1.idx2uid([esd1_idx[target_bus]])[0]

    dae = ss.dae
    tds = ss.TDS
    n_steps = int(round(tf / tstep))
    step_onset = int(round(t_step / tstep))

    t_hist, pcmd_hist, pdel_hist, v_hist, ip_hist = [], [], [], [], []
    tds_failed = False
    for step in range(n_steps):
        command_now = command_mw if step >= step_onset else 0.0
        ss.DG.set_paux(ss, esd1_idx[target_bus], command_now / 100.0)
        ss.DG.set_paux(ss, esd1_idx[other_bus], 0.0)

        tds.do_switch()
        tds.calc_h()
        if tds.itm_step():
            dae.t += tds.h
        else:
            tds.calc_h()
            if tds.h == 0:
                tds_failed = True
                break

        v_now = float(ss.ESD1.v.v[target_uid])
        ip_now = float(ss.ESD1.Ipout_y.v[target_uid])
        p_del = ip_now * v_now * 100.0
        t_hist.append(float(dae.t))
        pcmd_hist.append(command_now)
        pdel_hist.append(p_del)
        v_hist.append(v_now)
        ip_hist.append(ip_now)

    return dict(
        t=np.array(t_hist), p_command_mw=np.array(pcmd_hist),
        p_delivered_mw=np.array(pdel_hist), bus_voltage=np.array(v_hist),
        ipout_y=np.array(ip_hist), tds_success=(not tds_failed) and pflow_ok,
        pflow_converged=pflow_ok, p_max_bess_mw=p_max_bess_mw,
        target_bus=target_bus, command_mw=command_mw, t_step=t_step, tf=tf,
    )


def electrical_distance(ss, source_buses):
    """Dijkstra shortest-path distance (sum of |X|, Line.x1) from each bus in
    `source_buses` to every other bus in the network, using andes.Line as the
    graph edges. Returns {source_bus: {target_bus: distance}}. Same
    methodology as Paper_1 SS7.2/Section 7 (placement screening), reused here
    for P2's train/validation/test split design (Section 11/12 of the P2 plan)
    -- Paper_1 itself never persisted this as a function (it lived in an
    ephemeral scratchpad script), so it is written fresh here, not ported."""
    import heapq

    buses = list(ss.Bus.idx.v)
    adj = {b: [] for b in buses}
    bus1 = list(ss.Line.bus1.v)
    bus2 = list(ss.Line.bus2.v)
    x_line = list(ss.Line.x.v)
    for b1, b2, x in zip(bus1, bus2, x_line):
        w = abs(float(x))
        adj[b1].append((b2, w))
        adj[b2].append((b1, w))

    out = {}
    for src in source_buses:
        dist = {b: float('inf') for b in buses}
        dist[src] = 0.0
        pq = [(0.0, src)]
        visited = set()
        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            for v, w in adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        out[src] = dist
    return out


def run_physical_scenario(kind, gen=None, bus=None, rho=None, alpha_L=None, lambda_L=1.00,
                           p_max_bess_mw=None, k_f=None, k_r=None, controller='physical',
                           bess_bus1=BESS_BUS_1, bess_bus2=BESS_BUS_2,
                           tf=TF_INITIAL, dt=T_CONTROL_DEFAULT, quiet=True):
    """P2-E3/E4/E5 design-phase driver: build low-inertia case + BESS pair,
    apply one generation-loss ('gen', Alter on TGOV1N.paux0) or load-increase
    ('load', Alter on PQ.Ppf) contingency, then drive either the physical-only
    controller (P_i = clip(-k_f*df_i - k_r*rocof_i, -p_max_bess_mw,
    +p_max_bess_mw), controller='physical') or no BESS response at all
    (controller='no_ffc', a within-scenario reference for the RAW effect size
    of the BESS, no reward/gate involved) via manual itm_step() stepping
    (same mechanism as verify_li1_gate / Paper_1's run_test_scenario -- see
    DEC-P2-002 for why TDS.run()+TDS.plt is avoided). Not used for TD3 (that
    needs the Gymnasium FFCEnv-equivalent, built later); no test-set access
    here -- `gen`/`bus` must come from G_train_P2/L_train_P2 (or explicit
    DESIGN-only IDs), never G_test_P2/L_test_P2."""
    assert kind in ('gen', 'load')
    assert controller in ('physical', 'no_ffc')
    bus_voltages = natural_bus_voltages_at_lambda(lambda_L)

    # NOTE: cannot use build_case() here -- it calls ss.setup() internally,
    # and the per-scenario Alter/BESS devices must be added BEFORE setup().
    ss = andes.load(BASE_CASE, setup=False, no_output=quiet, default_config=True)
    for b in GEN_BUSES:
        ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))
    for b in BESS_ADMISSIBLE_BUSES:
        ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))

    if kind == 'gen':
        gov_uid = ss.TGOV1N.syn.v.index(gen)
        gov_idx = ss.TGOV1N.idx.v[gov_uid]
        alter_idx = ss.add('Alter', dict(model='TGOV1N', dev=gov_idx, src='paux0',
                                          t=TD, method='=', amount=0.0))
    else:
        pq_idx = ss.PQ.find_idx(keys='bus', values=[bus])[0]
        alter_idx = ss.add('Alter', dict(model='PQ', dev=pq_idx, src='Ppf',
                                          t=TD, method='+', amount=0.0))

    created = add_bess_pair(ss, bess_bus1, bess_bus2, p_max_bess_mw, bus_voltages,
                             ddn_pu=0.0, fdbd_hz=-0.017)
    ss.setup()

    ss.PQ.config.p2p = 1.0; ss.PQ.config.p2i = 0.0; ss.PQ.config.p2z = 0.0
    ss.PQ.config.q2q = 1.0; ss.PQ.config.q2i = 0.0; ss.PQ.config.q2z = 0.0
    ss.PQ.config.pq2z = 0
    ss.Toggle.u.v[:] = 0
    uids = ss.GENROU.idx2uid(AREA_GENS)
    ss.GENROU.M.v[uids] = ss.GENROU.M.v[uids] * K_FROZEN
    ss.GENROU.M.vin[uids] = ss.GENROU.M.vin[uids] * K_FROZEN

    if kind == 'gen':
        gen_uid = ss.GENROU.idx2uid([gen])[0]
        gen_bus = ss.GENROU.bus.v[gen_uid]
        pv_uid_pre = list(ss.PV.bus.v).index(gen_bus)
        p0_nom = float(ss.PV.p0.v[pv_uid_pre])
    else:
        pq_uid_pre = list(ss.PQ.bus.v).index(bus)
        load_p0_nom = float(ss.PQ.p0.v[pq_uid_pre])

    ss.PQ.p0.v[:] = ss.PQ.p0.v[:] * lambda_L
    ss.PQ.q0.v[:] = ss.PQ.q0.v[:] * lambda_L
    ss.PV.p0.v[:] = ss.PV.p0.v[:] * lambda_L

    alter_uid = ss.Alter.idx2uid([alter_idx])[0]
    if kind == 'gen':
        gen_uid = ss.GENROU.idx2uid([gen])[0]
        gen_bus = ss.GENROU.bus.v[gen_uid]
        pv_uid = list(ss.PV.bus.v).index(gen_bus)
        p0 = float(ss.PV.p0.v[pv_uid])
        ss.Alter.amount.v[alter_uid] = -rho * p0
        disturbance_mw = rho * p0 * 100.0
    else:
        ss.Alter.amount.v[alter_uid] = alpha_L * load_p0_nom
        disturbance_mw = alpha_L * load_p0_nom * 100.0

    ss.TDS.config.tstep = 1 / 60
    ss.TDS.config.fixt = 1
    ss.TDS.config.method = 'trapezoid'
    ss.TDS.config.save_every = 0
    ss.TDS.config.no_tqdm = 1

    ss.PFlow.run()
    pflow_ok = bool(ss.PFlow.converged)
    ss.TDS.init()

    esd1_idx = {bess_bus1: created[f'bus{bess_bus1}']['esd1'],
                bess_bus2: created[f'bus{bess_bus2}']['esd1']}
    busrocof_buses = list(ss.BusROCOF.bus.v)

    dae = ss.dae
    tds = ss.TDS
    n_steps = int(round(tf / dt))

    f_nadir = F0_HZ
    rocof_max = 0.0
    p_peak = 0.0
    sat_events = 0
    tds_failed = False

    for step in range(n_steps):
        if controller == 'no_ffc':
            dp1_mw, dp2_mw = 0.0, 0.0
        else:
            f1_hz = float(ss.BusROCOF.f.v[busrocof_buses.index(bess_bus1)]) * F0_HZ
            r1 = float(ss.BusROCOF.Wf_y.v[busrocof_buses.index(bess_bus1)]) * F0_HZ
            f2_hz = float(ss.BusROCOF.f.v[busrocof_buses.index(bess_bus2)]) * F0_HZ
            r2 = float(ss.BusROCOF.Wf_y.v[busrocof_buses.index(bess_bus2)]) * F0_HZ
            dp1_mw = -k_f * (f1_hz - F0_HZ) - k_r * r1
            dp2_mw = -k_f * (f2_hz - F0_HZ) - k_r * r2
            dp1_mw = max(-p_max_bess_mw, min(p_max_bess_mw, dp1_mw))
            dp2_mw = max(-p_max_bess_mw, min(p_max_bess_mw, dp2_mw))

        if abs(dp1_mw) >= p_max_bess_mw - 1e-6:
            sat_events += 1
        if abs(dp2_mw) >= p_max_bess_mw - 1e-6:
            sat_events += 1

        # DEC-P1-024/DEC-P2-004/DEC-P2-005: Pext0 is in SYSTEM base (Sb=100MVA),
        # not device base -- see add_bess_pair()'s docstring for the full trace.
        ss.DG.set_paux(ss, esd1_idx[bess_bus1], dp1_mw / 100.0)
        ss.DG.set_paux(ss, esd1_idx[bess_bus2], dp2_mw / 100.0)

        target_t = min((step + 1) * dt, tf)
        n_inner = 0
        while float(dae.t) < target_t - 1e-9:
            tds.do_switch()
            tds.calc_h()
            if tds.itm_step():
                dae.t += tds.h
            else:
                tds.calc_h()
                if tds.h == 0:
                    tds_failed = True
                    break
            n_inner += 1
            if n_inner > 2000:
                tds_failed = True
                break
        if tds_failed:
            break

        f_gen_hz = np.array([float(v) for v in ss.BusFreq.f.v[:len(GEN_BUSES)]]) * F0_HZ
        rocof_gen_hz_s = np.array([float(v) for v in ss.BusROCOF.Wf_y.v[:len(GEN_BUSES)]]) * F0_HZ
        f_nadir = min(f_nadir, float(np.min(f_gen_hz)))
        rocof_max = max(rocof_max, float(np.max(np.abs(rocof_gen_hz_s))))

        esd1_uid1 = ss.ESD1.idx2uid([esd1_idx[bess_bus1]])[0]
        esd1_uid2 = ss.ESD1.idx2uid([esd1_idx[bess_bus2]])[0]
        # DEC-P1-024: true delivered power is Ipout_y*v*Sb (system base, 100 MVA),
        # not Ipout_y*v*Sn -- see add_bess_pair()'s docstring.
        p1_act = float(ss.ESD1.Ipout_y.v[esd1_uid1]) * float(ss.ESD1.v.v[esd1_uid1]) * 100.0
        p2_act = float(ss.ESD1.Ipout_y.v[esd1_uid2]) * float(ss.ESD1.v.v[esd1_uid2]) * 100.0
        p_peak = max(p_peak, abs(p1_act) + abs(p2_act))

    saturation_fraction = sat_events / (2 * n_steps)
    return dict(
        kind=kind, gen=gen, bus=bus, rho=rho, alpha_L=alpha_L, lambda_L=lambda_L,
        controller=controller, p_max_bess_mw=p_max_bess_mw, k_f=k_f, k_r=k_r,
        disturbance_mw=disturbance_mw,
        f_nadir_hz=f_nadir, df_nadir_hz=f_nadir - F0_HZ, rocof_max_hz_s=rocof_max,
        p_peak_mw=p_peak, saturation_fraction=saturation_fraction,
        tds_success=(not tds_failed) and pflow_ok, pflow_converged=pflow_ok,
    )
    return out


def run_physical_scenario_tc(kind, gen=None, bus=None, rho=None, alpha_L=None, lambda_L=1.00,
                              p_max_bess_mw=None, k_f=None, k_r=None, tc=T_CONTROL_DEFAULT,
                              tstep=0.005, controller='physical', feedback='local',
                              open_loop_command_mw=None,
                              bess_bus1=BESS_BUS_1, bess_bus2=BESS_BUS_2,
                              tf=TF_INITIAL, quiet=True):
    """P2-E4 Tc-design driver. Identical case construction, contingency
    mechanism, BESS pair and physical control law as run_physical_scenario(),
    but DECOUPLES the fixed integration/logging resolution (`tstep`, kept
    IDENTICAL across every Tc tested) from the control-update period (`tc`,
    the true independent variable of this experiment): BusROCOF/BusFreq are
    sampled and a new Pext0 command is computed and applied only every `tc`
    seconds (zero-order hold in between); the physical integration and the
    frequency/RoCoF/command/delivered-power trajectory are recorded at every
    `tstep`, regardless of `tc`. This is required so that RoCoF_max/nadir are
    always read off the SAME integration-level trajectory for every Tc (P2
    plan Section 7-bis/P2-E4 Section 7 -- never derive them from
    controller-rate samples alone, or a Tc effect could be confounded with an
    undersampling/aliasing artifact of the metric itself).

    `feedback` (P2-E5 observability diagnostic, DEC-P2-014/015): 'local'
    (default, unchanged from every prior P2-E4/E5 run) feeds each BESS its
    OWN bus's BusROCOF.f/Wf_y into the control law, as before. 'global' feeds
    BOTH BESS units the worst-system frequency/RoCoF (min BusFreq.f / max
    |BusROCOF.Wf_y| over GEN_BUSES, the same quantity already logged as
    f_worst_hz/rocof_worst_hz_s) instead of their local bus reading -- a
    proxy for a wide-area/COI-style observation using only signals already
    computed elsewhere in this function (no new model/weighting added). Kf,
    Kr, Pmax, Tc, tip, BusROCOF/Tf/Tw/Tr, and BESS location are all
    unaffected by this switch -- only which frequency/RoCoF reading feeds the
    SAME control law.

    Returns full trajectories (t, f_worst_hz, rocof_worst_hz_s,
    p_command1_mw, p_command2_mw, p_delivered1_mw, p_delivered2_mw) plus
    timing-verification fields (action_count, action_times, dae_t_final,
    max_step_gap_s) and wall-clock runtime_seconds."""
    assert kind in ('gen', 'load')
    assert controller in ('physical', 'no_ffc', 'open_loop_fixed')
    assert feedback in ('local', 'global')
    if controller == 'open_loop_fixed':
        assert open_loop_command_mw is not None
    bus_voltages = natural_bus_voltages_at_lambda(lambda_L)

    ss = andes.load(BASE_CASE, setup=False, no_output=quiet, default_config=True)
    for b in GEN_BUSES:
        ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))
    for b in BESS_ADMISSIBLE_BUSES:
        ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))

    if kind == 'gen':
        gov_uid = ss.TGOV1N.syn.v.index(gen)
        gov_idx = ss.TGOV1N.idx.v[gov_uid]
        alter_idx = ss.add('Alter', dict(model='TGOV1N', dev=gov_idx, src='paux0',
                                          t=TD, method='=', amount=0.0))
    else:
        pq_idx = ss.PQ.find_idx(keys='bus', values=[bus])[0]
        alter_idx = ss.add('Alter', dict(model='PQ', dev=pq_idx, src='Ppf',
                                          t=TD, method='+', amount=0.0))

    created = add_bess_pair(ss, bess_bus1, bess_bus2, p_max_bess_mw, bus_voltages,
                             ddn_pu=0.0, fdbd_hz=-0.017)
    ss.setup()

    ss.PQ.config.p2p = 1.0; ss.PQ.config.p2i = 0.0; ss.PQ.config.p2z = 0.0
    ss.PQ.config.q2q = 1.0; ss.PQ.config.q2i = 0.0; ss.PQ.config.q2z = 0.0
    ss.PQ.config.pq2z = 0
    ss.Toggle.u.v[:] = 0
    uids = ss.GENROU.idx2uid(AREA_GENS)
    ss.GENROU.M.v[uids] = ss.GENROU.M.v[uids] * K_FROZEN
    ss.GENROU.M.vin[uids] = ss.GENROU.M.vin[uids] * K_FROZEN

    if kind == 'gen':
        gen_uid = ss.GENROU.idx2uid([gen])[0]
        gen_bus = ss.GENROU.bus.v[gen_uid]
        pv_uid_pre = list(ss.PV.bus.v).index(gen_bus)
        p0_nom = float(ss.PV.p0.v[pv_uid_pre])
    else:
        pq_uid_pre = list(ss.PQ.bus.v).index(bus)
        load_p0_nom = float(ss.PQ.p0.v[pq_uid_pre])

    ss.PQ.p0.v[:] = ss.PQ.p0.v[:] * lambda_L
    ss.PQ.q0.v[:] = ss.PQ.q0.v[:] * lambda_L
    ss.PV.p0.v[:] = ss.PV.p0.v[:] * lambda_L

    alter_uid = ss.Alter.idx2uid([alter_idx])[0]
    if kind == 'gen':
        gen_uid = ss.GENROU.idx2uid([gen])[0]
        gen_bus = ss.GENROU.bus.v[gen_uid]
        pv_uid = list(ss.PV.bus.v).index(gen_bus)
        p0 = float(ss.PV.p0.v[pv_uid])
        ss.Alter.amount.v[alter_uid] = -rho * p0
        disturbance_mw = rho * p0 * 100.0
    else:
        ss.Alter.amount.v[alter_uid] = alpha_L * load_p0_nom
        disturbance_mw = alpha_L * load_p0_nom * 100.0

    ss.TDS.config.tstep = tstep
    ss.TDS.config.fixt = 1
    ss.TDS.config.method = 'trapezoid'
    ss.TDS.config.save_every = 0
    ss.TDS.config.no_tqdm = 1

    ss.PFlow.run()
    pflow_ok = bool(ss.PFlow.converged)
    ss.TDS.init()

    esd1_idx = {bess_bus1: created[f'bus{bess_bus1}']['esd1'],
                bess_bus2: created[f'bus{bess_bus2}']['esd1']}
    esd1_uid1 = ss.ESD1.idx2uid([esd1_idx[bess_bus1]])[0]
    esd1_uid2 = ss.ESD1.idx2uid([esd1_idx[bess_bus2]])[0]
    busrocof_buses = list(ss.BusROCOF.bus.v)
    all_bus_idx = list(ss.Bus.idx.v)
    bess1_bus_uid = all_bus_idx.index(bess_bus1)
    bess2_bus_uid = all_bus_idx.index(bess_bus2)

    dae = ss.dae
    tds = ss.TDS
    n_int_steps = int(round(tf / tstep))
    ctrl_period_steps = max(1, int(round(tc / tstep)))
    expected_actions = (len(range(0, n_int_steps, ctrl_period_steps))
                         if controller not in ('no_ffc', 'open_loop_fixed') else 0)
    open_loop_onset_step = int(round(TD / tstep))

    dp1_mw = dp2_mw = 0.0
    action_count = 0
    action_times = []
    action_step_indices = []
    sat_events = 0
    tds_failed = False

    t_hist, f_hist, rocof_hist, f_coi_hist = [], [], [], []
    pcmd1_hist, pcmd2_hist, pdel1_hist, pdel2_hist = [], [], [], []
    # Full-resolution LOCAL BESS-bus freq/RoCoF (P2-E5 Section 12 diagnostic:
    # compare local RoCoF at the BESS buses against the worst-system RoCoF --
    # pure additional instrumentation, does not change the control law, Tc,
    # Pmax, tip, BusROCOF/Tf/Tw/Tr, or BESS location).
    f_bess1_hist, rocof_bess1_hist, f_bess2_hist, rocof_bess2_hist = [], [], [], []
    bess1_rocof_uid = busrocof_buses.index(bess_bus1)
    bess2_rocof_uid = busrocof_buses.index(bess_bus2)
    # Figure-package instrumentation (voltage magnitude pu, angle rad) at the
    # two BESS POI buses AND at every bus in the system (for the "worst
    # voltage/phase excursion bus" supplementary figure) -- pure additional
    # readout of existing state variables, no model/physics change.
    v_bess1_hist, theta_bess1_hist, v_bess2_hist, theta_bess2_hist = [], [], [], []
    v_all_hist, theta_all_hist = [], []
    f_gen_all_hist, rocof_gen_all_hist = [], []  # per-GEN_BUS arrays (for "which bus" post-hoc analysis)

    t_start = time.perf_counter()
    dae_t_prev = float(dae.t)
    max_step_gap = 0.0

    for step in range(n_int_steps):
        if controller == 'open_loop_fixed':
            command_now = open_loop_command_mw if step >= open_loop_onset_step else 0.0
            dp1_mw = dp2_mw = command_now
            ss.DG.set_paux(ss, esd1_idx[bess_bus1], dp1_mw / 100.0)
            ss.DG.set_paux(ss, esd1_idx[bess_bus2], dp2_mw / 100.0)
        elif controller == 'physical' and step % ctrl_period_steps == 0:
            if feedback == 'global':
                f_gen_now = np.array([float(v) for v in ss.BusFreq.f.v[:len(GEN_BUSES)]]) * F0_HZ
                rocof_gen_now = np.array([float(v) for v in ss.BusROCOF.Wf_y.v[:len(GEN_BUSES)]]) * F0_HZ
                f1_hz = f2_hz = float(np.min(f_gen_now))
                r1 = r2 = float(np.max(np.abs(rocof_gen_now)))
            else:
                f1_hz = float(ss.BusROCOF.f.v[busrocof_buses.index(bess_bus1)]) * F0_HZ
                r1 = float(ss.BusROCOF.Wf_y.v[busrocof_buses.index(bess_bus1)]) * F0_HZ
                f2_hz = float(ss.BusROCOF.f.v[busrocof_buses.index(bess_bus2)]) * F0_HZ
                r2 = float(ss.BusROCOF.Wf_y.v[busrocof_buses.index(bess_bus2)]) * F0_HZ
            dp1_mw = max(-p_max_bess_mw, min(p_max_bess_mw, -k_f * (f1_hz - F0_HZ) - k_r * r1))
            dp2_mw = max(-p_max_bess_mw, min(p_max_bess_mw, -k_f * (f2_hz - F0_HZ) - k_r * r2))
            if abs(dp1_mw) >= p_max_bess_mw - 1e-6:
                sat_events += 1
            if abs(dp2_mw) >= p_max_bess_mw - 1e-6:
                sat_events += 1
            ss.DG.set_paux(ss, esd1_idx[bess_bus1], dp1_mw / 100.0)
            ss.DG.set_paux(ss, esd1_idx[bess_bus2], dp2_mw / 100.0)
            action_count += 1
            action_times.append(step * tstep)
            action_step_indices.append(step)

        tds.do_switch()
        tds.calc_h()
        if tds.itm_step():
            dae.t += tds.h
        else:
            tds.calc_h()
            if tds.h == 0:
                tds_failed = True
                break
        gap = float(dae.t) - dae_t_prev
        max_step_gap = max(max_step_gap, gap)
        dae_t_prev = float(dae.t)

        f_gen_hz = np.array([float(v) for v in ss.BusFreq.f.v[:len(GEN_BUSES)]]) * F0_HZ
        rocof_gen_hz_s = np.array([float(v) for v in ss.BusROCOF.Wf_y.v[:len(GEN_BUSES)]]) * F0_HZ
        f_worst = float(np.min(f_gen_hz))
        rocof_worst = float(np.max(np.abs(rocof_gen_hz_s)))
        # Simple (UNWEIGHTED) mean frequency across GEN_BUSES -- a COI proxy.
        # True H-weighted COI is NOT implemented (no model change made for it);
        # this is an honest, clearly-labeled substitute using only the
        # per-generator-bus frequencies already read above.
        f_coi = float(np.mean(f_gen_hz))

        p1_act = float(ss.ESD1.Ipout_y.v[esd1_uid1]) * float(ss.ESD1.v.v[esd1_uid1]) * 100.0
        p2_act = float(ss.ESD1.Ipout_y.v[esd1_uid2]) * float(ss.ESD1.v.v[esd1_uid2]) * 100.0

        t_hist.append(float(dae.t))
        f_hist.append(f_worst)
        rocof_hist.append(rocof_worst)
        f_coi_hist.append(f_coi)
        f_gen_all_hist.append(f_gen_hz)
        rocof_gen_all_hist.append(rocof_gen_hz_s)
        pcmd1_hist.append(dp1_mw)
        pcmd2_hist.append(dp2_mw)
        pdel1_hist.append(p1_act)
        pdel2_hist.append(p2_act)

        f_bess1_hist.append(float(ss.BusROCOF.f.v[bess1_rocof_uid]) * F0_HZ)
        rocof_bess1_hist.append(float(ss.BusROCOF.Wf_y.v[bess1_rocof_uid]) * F0_HZ)
        f_bess2_hist.append(float(ss.BusROCOF.f.v[bess2_rocof_uid]) * F0_HZ)
        rocof_bess2_hist.append(float(ss.BusROCOF.Wf_y.v[bess2_rocof_uid]) * F0_HZ)

        v_all_now = np.array([float(v) for v in ss.Bus.v.v])
        theta_all_now = np.array([float(v) for v in ss.Bus.a.v])
        v_all_hist.append(v_all_now)
        theta_all_hist.append(theta_all_now)
        v_bess1_hist.append(float(v_all_now[bess1_bus_uid]))
        theta_bess1_hist.append(float(theta_all_now[bess1_bus_uid]))
        v_bess2_hist.append(float(v_all_now[bess2_bus_uid]))
        theta_bess2_hist.append(float(theta_all_now[bess2_bus_uid]))

    runtime_seconds = time.perf_counter() - t_start

    t_arr = np.array(t_hist)
    f_arr = np.array(f_hist)
    rocof_arr = np.array(rocof_hist)
    f_coi_arr = np.array(f_coi_hist)
    pcmd1_arr = np.array(pcmd1_hist)
    pcmd2_arr = np.array(pcmd2_hist)
    pdel1_arr = np.array(pdel1_hist)
    pdel2_arr = np.array(pdel2_hist)

    if len(f_arr):
        i_nadir = int(np.argmin(f_arr))
        f_nadir = float(f_arr[i_nadir])
        t_nadir = float(t_arr[i_nadir])
        rocof_max = float(np.max(rocof_arr))
        p_peak = float(np.max(np.abs(pdel1_arr) + np.abs(pdel2_arr)))
        err1 = pdel1_arr - pcmd1_arr
        err2 = pdel2_arr - pcmd2_arr
        cmd_del_max_err = float(max(np.max(np.abs(err1)), np.max(np.abs(err2))))
        cmd_del_rms_err = float(np.sqrt(np.mean(np.concatenate([err1, err2]) ** 2)))
        f_final = float(f_arr[-1])
        band = 0.02  # Hz, +/-20 mHz settling band
        within = np.abs(f_arr - f_final) <= band
        settling_time = float('nan')
        post_td = t_arr >= TD
        for i in range(len(t_arr) - 1, -1, -1):
            if t_arr[i] < TD:
                break
            if not within[i]:
                settling_time = float(t_arr[i + 1] - TD) if i + 1 < len(t_arr) else float('nan')
                break
        else:
            settling_time = float(t_arr[post_td][0] - TD) if np.any(post_td) else float('nan')
    else:
        f_nadir = F0_HZ
        t_nadir = 0.0
        rocof_max = 0.0
        p_peak = 0.0
        cmd_del_max_err = float('nan')
        cmd_del_rms_err = float('nan')
        settling_time = float('nan')

    saturation_fraction = (sat_events / (2 * action_count)) if action_count else 0.0

    return dict(
        kind=kind, gen=gen, bus=bus, rho=rho, alpha_L=alpha_L, lambda_L=lambda_L,
        controller=controller, feedback=feedback, p_max_bess_mw=p_max_bess_mw, k_f=k_f, k_r=k_r,
        tc=tc, tstep=tstep, disturbance_mw=disturbance_mw,
        f_nadir_hz=f_nadir, df_nadir_hz=f_nadir - F0_HZ, t_nadir_s=t_nadir, rocof_max_hz_s=rocof_max,
        settling_time_s=settling_time, p_peak_mw=p_peak, saturation_fraction=saturation_fraction,
        command_delivered_max_error_mw=cmd_del_max_err, command_delivered_rms_error_mw=cmd_del_rms_err,
        tds_success=(not tds_failed) and pflow_ok, pflow_converged=pflow_ok,
        expected_actions=expected_actions, actual_actions=action_count,
        first_action_time_s=(action_times[0] if action_times else float('nan')),
        last_action_time_s=(action_times[-1] if action_times else float('nan')),
        dae_t_final=float(dae.t), max_step_gap_s=max_step_gap, runtime_seconds=runtime_seconds,
        t=t_arr, f_worst_hz=f_arr, rocof_worst_hz_s=rocof_arr, f_coi_hz=f_coi_arr,
        p_command1_mw=pcmd1_arr, p_command2_mw=pcmd2_arr,
        p_delivered1_mw=pdel1_arr, p_delivered2_mw=pdel2_arr,
        action_step_indices=np.array(action_step_indices, dtype=int),
        f_bess1_hz=np.array(f_bess1_hist), rocof_bess1_hz_s=np.array(rocof_bess1_hist),
        f_bess2_hz=np.array(f_bess2_hist), rocof_bess2_hz_s=np.array(rocof_bess2_hist),
        v_bess1_pu=np.array(v_bess1_hist), theta_bess1_rad=np.array(theta_bess1_hist),
        v_bess2_pu=np.array(v_bess2_hist), theta_bess2_rad=np.array(theta_bess2_hist),
        v_all_pu=np.array(v_all_hist), theta_all_rad=np.array(theta_all_hist),
        all_bus_idx=np.array(all_bus_idx, dtype=int),
        f_gen_all_hz=np.array(f_gen_all_hist), rocof_gen_all_hz_s=np.array(rocof_gen_all_hist),
        gen_buses=np.array(GEN_BUSES, dtype=int),
    )


def add_single_bess(ss, bus, p_max_bess_mw, bus_voltage, ddn_pu=0.0, fdbd_hz=-0.017):
    """Single-bus variant of add_bess_pair() -- identical per-bus device
    construction (same PV/ESD1 params, same Sb=100MVA power convention), used
    only by the P2-E5 spatial-controllability probe (run_spatial_
    controllability_probe()) to test open-loop injection at ONE candidate bus
    at a time without requiring a second paired location."""
    bus_uid = list(ss.Bus.idx.v).index(bus)
    vn = float(ss.Bus.Vn.v[bus_uid])
    p_pu = p_max_bess_mw / 100.0
    pv_idx = ss.add('PV', dict(bus=bus, Vn=vn, Sn=max(p_max_bess_mw, 100.0),
                                p0=0.0, q0=0.0, pmax=p_pu, pmin=0.0,
                                qmax=0.3, qmin=-0.3, v0=bus_voltage, ra=0.0, xs=0.05))
    esd_idx = ss.add('ESD1', dict(bus=bus, gen=pv_idx, Sn=p_max_bess_mw, fn=60.0, xc=1.0,
                                   pqflag=1, pmx=p_pu, qmx=0.33, qmn=-0.33,
                                   v0=0.8, v1=1.1, dqdv=-0.01, fdbd=fdbd_hz, ddn=ddn_pu,
                                   ialim=1.3, vt0=0.88, vt1=0.90, vt2=1.1, vt3=1.2,
                                   ft0=59.5, ft1=59.7, ft2=60.3, ft3=60.5,
                                   gammap=1.0, gammaq=1.0, Tf=1.0,
                                   SOCmin=0.0, SOCmax=1.0, SOCinit=0.5, En=100.0,
                                   EtaC=1.0, EtaD=1.0))
    return dict(pv=pv_idx, esd1=esd_idx)


def run_spatial_controllability_probe(kind, gen=None, bus=None, rho=None, alpha_L=None, lambda_L=1.00,
                                       test_bus=None, command_mw=None, p_max_bess_mw=None,
                                       t_step=TD, tstep=0.005, tf=TF_INITIAL, quiet=True):
    """P2-E5 spatial-controllability diagnostic. Open-loop (NOT feedback --
    no Kf/Kr, no control law): a single BESS-sized device at `test_bus`
    receives a FIXED, prescribed power step `command_mw` at t=t_step (default
    TD, the disturbance instant) held constant through tf -- a best-case
    upper bound on what any feedback law at that location could ever achieve.
    Isolates pure electrical controllability (does power injected HERE move
    df_nadir/RoCoF_max at all) from observability and control-law tuning,
    which were already ruled out separately (DEC-P2-014/015).

    Same disturbance mechanism, same low-inertia case, same Sb=100MVA power
    convention as every other P2 driver. Does NOT touch Kf/Kr/Pmax total/Tc/
    tip/BusROCOF or the frozen BESS pair -- this is a standalone single-device
    probe, not a replacement for the paper's BESS pair."""
    assert kind in ('gen', 'load')
    bus_voltages = natural_bus_voltages_at_lambda(lambda_L)

    ss = andes.load(BASE_CASE, setup=False, no_output=quiet, default_config=True)
    for b in GEN_BUSES:
        ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))

    if kind == 'gen':
        gov_uid = ss.TGOV1N.syn.v.index(gen)
        gov_idx = ss.TGOV1N.idx.v[gov_uid]
        alter_idx = ss.add('Alter', dict(model='TGOV1N', dev=gov_idx, src='paux0',
                                          t=TD, method='=', amount=0.0))
    else:
        pq_idx = ss.PQ.find_idx(keys='bus', values=[bus])[0]
        alter_idx = ss.add('Alter', dict(model='PQ', dev=pq_idx, src='Ppf',
                                          t=TD, method='+', amount=0.0))

    created = add_single_bess(ss, test_bus, p_max_bess_mw, bus_voltages[test_bus])
    ss.setup()

    ss.PQ.config.p2p = 1.0; ss.PQ.config.p2i = 0.0; ss.PQ.config.p2z = 0.0
    ss.PQ.config.q2q = 1.0; ss.PQ.config.q2i = 0.0; ss.PQ.config.q2z = 0.0
    ss.PQ.config.pq2z = 0
    ss.Toggle.u.v[:] = 0
    uids = ss.GENROU.idx2uid(AREA_GENS)
    ss.GENROU.M.v[uids] = ss.GENROU.M.v[uids] * K_FROZEN
    ss.GENROU.M.vin[uids] = ss.GENROU.M.vin[uids] * K_FROZEN

    if kind == 'gen':
        gen_uid = ss.GENROU.idx2uid([gen])[0]
        gen_bus = ss.GENROU.bus.v[gen_uid]
        pv_uid_pre = list(ss.PV.bus.v).index(gen_bus)
        p0_nom = float(ss.PV.p0.v[pv_uid_pre])
    else:
        pq_uid_pre = list(ss.PQ.bus.v).index(bus)
        load_p0_nom = float(ss.PQ.p0.v[pq_uid_pre])

    ss.PQ.p0.v[:] = ss.PQ.p0.v[:] * lambda_L
    ss.PQ.q0.v[:] = ss.PQ.q0.v[:] * lambda_L
    ss.PV.p0.v[:] = ss.PV.p0.v[:] * lambda_L

    alter_uid = ss.Alter.idx2uid([alter_idx])[0]
    if kind == 'gen':
        gen_uid = ss.GENROU.idx2uid([gen])[0]
        gen_bus = ss.GENROU.bus.v[gen_uid]
        pv_uid = list(ss.PV.bus.v).index(gen_bus)
        p0 = float(ss.PV.p0.v[pv_uid])
        ss.Alter.amount.v[alter_uid] = -rho * p0
    else:
        ss.Alter.amount.v[alter_uid] = alpha_L * load_p0_nom

    ss.TDS.config.tstep = tstep
    ss.TDS.config.fixt = 1
    ss.TDS.config.method = 'trapezoid'
    ss.TDS.config.save_every = 0
    ss.TDS.config.no_tqdm = 1

    ss.PFlow.run()
    pflow_ok = bool(ss.PFlow.converged)
    ss.TDS.init()

    esd1_uid = ss.ESD1.idx2uid([created['esd1']])[0]
    dae = ss.dae
    tds = ss.TDS
    n_steps = int(round(tf / tstep))
    step_onset = int(round(t_step / tstep))

    f_nadir = F0_HZ
    rocof_max = 0.0
    p_peak = 0.0
    tds_failed = False

    for step in range(n_steps):
        command_now = command_mw if step >= step_onset else 0.0
        ss.DG.set_paux(ss, created['esd1'], command_now / 100.0)

        tds.do_switch()
        tds.calc_h()
        if tds.itm_step():
            dae.t += tds.h
        else:
            tds.calc_h()
            if tds.h == 0:
                tds_failed = True
                break

        f_gen_hz = np.array([float(v) for v in ss.BusFreq.f.v[:len(GEN_BUSES)]]) * F0_HZ
        rocof_gen_hz_s = np.array([float(v) for v in ss.BusROCOF.Wf_y.v[:len(GEN_BUSES)]]) * F0_HZ
        f_nadir = min(f_nadir, float(np.min(f_gen_hz)))
        rocof_max = max(rocof_max, float(np.max(np.abs(rocof_gen_hz_s))))

        p_act = float(ss.ESD1.Ipout_y.v[esd1_uid]) * float(ss.ESD1.v.v[esd1_uid]) * 100.0
        p_peak = max(p_peak, abs(p_act))

    return dict(
        kind=kind, gen=gen, bus=bus, rho=rho, alpha_L=alpha_L, lambda_L=lambda_L,
        test_bus=test_bus, command_mw=command_mw, p_max_bess_mw=p_max_bess_mw,
        f_nadir_hz=f_nadir, df_nadir_hz=f_nadir - F0_HZ, rocof_max_hz_s=rocof_max,
        p_peak_mw=p_peak, tds_success=(not tds_failed) and pflow_ok, pflow_converged=pflow_ok,
    )


def run_spatial_controllability_probe_multi(kind, gen=None, bus=None, rho=None, alpha_L=None,
                                             lambda_L=1.00, test_buses=None, command_mw=None,
                                             p_max_bess_mw=None, t_step=TD, tstep=0.005,
                                             tf=TF_INITIAL, quiet=True):
    """P2-E6 BESS relocation screening (Section 7 diagnostic, list-of-buses
    generalization of run_spatial_controllability_probe()). Adds ONE
    BESS-sized device per bus in `test_buses` (1 for single-bus screening, 2
    for pair verification), each independently receiving the SAME fixed
    open-loop step `command_mw` at t=t_step (no Kf/Kr, no feedback) -- used to
    directly compare a candidate PAIR's joint effect against the frozen
    BESS_BUS_1/BESS_BUS_2 pair using an identical, apples-to-apples
    methodology. Same disturbance mechanism, low-inertia case, Sb=100MVA
    convention as every other P2 driver."""
    assert kind in ('gen', 'load')
    assert len(test_buses) >= 1
    bus_voltages = natural_bus_voltages_at_lambda(lambda_L)

    ss = andes.load(BASE_CASE, setup=False, no_output=quiet, default_config=True)
    for b in GEN_BUSES:
        ss.add('BusROCOF', dict(bus=b, **ROCOF_PARAMS))

    if kind == 'gen':
        gov_uid = ss.TGOV1N.syn.v.index(gen)
        gov_idx = ss.TGOV1N.idx.v[gov_uid]
        alter_idx = ss.add('Alter', dict(model='TGOV1N', dev=gov_idx, src='paux0',
                                          t=TD, method='=', amount=0.0))
    else:
        pq_idx = ss.PQ.find_idx(keys='bus', values=[bus])[0]
        alter_idx = ss.add('Alter', dict(model='PQ', dev=pq_idx, src='Ppf',
                                          t=TD, method='+', amount=0.0))

    created = {tb: add_single_bess(ss, tb, p_max_bess_mw, bus_voltages[tb]) for tb in test_buses}
    ss.setup()

    ss.PQ.config.p2p = 1.0; ss.PQ.config.p2i = 0.0; ss.PQ.config.p2z = 0.0
    ss.PQ.config.q2q = 1.0; ss.PQ.config.q2i = 0.0; ss.PQ.config.q2z = 0.0
    ss.PQ.config.pq2z = 0
    ss.Toggle.u.v[:] = 0
    uids = ss.GENROU.idx2uid(AREA_GENS)
    ss.GENROU.M.v[uids] = ss.GENROU.M.v[uids] * K_FROZEN
    ss.GENROU.M.vin[uids] = ss.GENROU.M.vin[uids] * K_FROZEN

    if kind == 'gen':
        gen_uid = ss.GENROU.idx2uid([gen])[0]
        gen_bus = ss.GENROU.bus.v[gen_uid]
        pv_uid_pre = list(ss.PV.bus.v).index(gen_bus)
        p0_nom = float(ss.PV.p0.v[pv_uid_pre])
    else:
        pq_uid_pre = list(ss.PQ.bus.v).index(bus)
        load_p0_nom = float(ss.PQ.p0.v[pq_uid_pre])

    ss.PQ.p0.v[:] = ss.PQ.p0.v[:] * lambda_L
    ss.PQ.q0.v[:] = ss.PQ.q0.v[:] * lambda_L
    ss.PV.p0.v[:] = ss.PV.p0.v[:] * lambda_L

    alter_uid = ss.Alter.idx2uid([alter_idx])[0]
    if kind == 'gen':
        gen_uid = ss.GENROU.idx2uid([gen])[0]
        gen_bus = ss.GENROU.bus.v[gen_uid]
        pv_uid = list(ss.PV.bus.v).index(gen_bus)
        p0 = float(ss.PV.p0.v[pv_uid])
        ss.Alter.amount.v[alter_uid] = -rho * p0
    else:
        ss.Alter.amount.v[alter_uid] = alpha_L * load_p0_nom

    ss.TDS.config.tstep = tstep
    ss.TDS.config.fixt = 1
    ss.TDS.config.method = 'trapezoid'
    ss.TDS.config.save_every = 0
    ss.TDS.config.no_tqdm = 1

    ss.PFlow.run()
    pflow_ok = bool(ss.PFlow.converged)
    ss.TDS.init()

    esd1_uids = {tb: ss.ESD1.idx2uid([created[tb]['esd1']])[0] for tb in test_buses}
    dae = ss.dae
    tds = ss.TDS
    n_steps = int(round(tf / tstep))
    step_onset = int(round(t_step / tstep))

    f_nadir = F0_HZ
    rocof_max = 0.0
    p_peak = 0.0
    tds_failed = False

    for step in range(n_steps):
        command_now = command_mw if step >= step_onset else 0.0
        for tb in test_buses:
            ss.DG.set_paux(ss, created[tb]['esd1'], command_now / 100.0)

        tds.do_switch()
        tds.calc_h()
        if tds.itm_step():
            dae.t += tds.h
        else:
            tds.calc_h()
            if tds.h == 0:
                tds_failed = True
                break

        f_gen_hz = np.array([float(v) for v in ss.BusFreq.f.v[:len(GEN_BUSES)]]) * F0_HZ
        rocof_gen_hz_s = np.array([float(v) for v in ss.BusROCOF.Wf_y.v[:len(GEN_BUSES)]]) * F0_HZ
        f_nadir = min(f_nadir, float(np.min(f_gen_hz)))
        rocof_max = max(rocof_max, float(np.max(np.abs(rocof_gen_hz_s))))

        p_now = sum(abs(float(ss.ESD1.Ipout_y.v[esd1_uids[tb]]) * float(ss.ESD1.v.v[esd1_uids[tb]]) * 100.0)
                    for tb in test_buses)
        p_peak = max(p_peak, p_now)

    return dict(
        kind=kind, gen=gen, bus=bus, rho=rho, alpha_L=alpha_L, lambda_L=lambda_L,
        test_buses=list(test_buses), command_mw=command_mw, p_max_bess_mw=p_max_bess_mw,
        f_nadir_hz=f_nadir, df_nadir_hz=f_nadir - F0_HZ, rocof_max_hz_s=rocof_max,
        p_peak_mw=p_peak, tds_success=(not tds_failed) and pflow_ok, pflow_converged=pflow_ok,
    )
