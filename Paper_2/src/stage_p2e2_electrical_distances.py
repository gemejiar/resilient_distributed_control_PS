# -*- coding: utf-8 -*-
"""P2-E2: compute electrical distances from the frozen BESS buses (13, 12) to
every non-slack generator and every PQ load, to inform G/L train/validation/
test split design (P2 plan Section 11/12)."""
import sys, logging, json
sys.path.insert(0, "Paper_2/src")
logging.getLogger('andes').setLevel(logging.WARNING)
import p2_common as m

ss = m.build_case(k=m.K_FROZEN, contingency_gen=None, quiet=True)
ss.PFlow.run()

BESS_BUS_1, BESS_BUS_2 = 13, 12
dist = m.electrical_distance(ss, [BESS_BUS_1, BESS_BUS_2])


def combined_dist(bus):
    return min(dist[BESS_BUS_1][bus], dist[BESS_BUS_2][bus])


# --- generators ---
gen_rows = []
for gidx in ss.GENROU.idx.v:
    if gidx == 'GENROU_10':  # bus 39, slack -- excluded from AREA_GENS/split pool
        continue
    uid = ss.GENROU.idx2uid([gidx])[0]
    bus = ss.GENROU.bus.v[uid]
    sn = float(ss.GENROU.Sn.v[uid])
    gen_rows.append(dict(idx=gidx, bus=int(bus), Sn_MVA=sn, dist=combined_dist(bus)))

gen_rows.sort(key=lambda r: -r['Sn_MVA'])
print("=== Generators (non-slack), sorted by Sn descending ===")
for r in gen_rows:
    print(f"{r['idx']:>10}  bus={r['bus']:2d}  Sn={r['Sn_MVA']:8.1f} MVA  dist(BESS)={r['dist']:.4f}")

# --- loads ---
load_rows = []
for lidx in ss.PQ.idx.v:
    uid = ss.PQ.idx2uid([lidx])[0]
    bus = ss.PQ.bus.v[uid]
    p0_pu = float(ss.PQ.p0.v[uid])
    load_rows.append(dict(idx=lidx, bus=int(bus), P0_MW=p0_pu * 100.0, dist=combined_dist(bus)))

load_rows.sort(key=lambda r: -r['P0_MW'])
print("\n=== Loads (PQ), sorted by P0 descending ===")
for r in load_rows:
    print(f"{r['idx']:>6}  bus={r['bus']:2d}  P0={r['P0_MW']:7.1f} MW  dist(BESS)={r['dist']:.4f}")

json.dump(dict(generators=gen_rows, loads=load_rows),
          open("Paper_2/artifacts/diagnostics/p2e2_electrical_distances.json", "w"), indent=2)
print("\nWrote Paper_2/artifacts/diagnostics/p2e2_electrical_distances.json")
