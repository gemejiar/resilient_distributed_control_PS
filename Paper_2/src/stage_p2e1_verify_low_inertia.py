# -*- coding: utf-8 -*-
"""P2-E1: verify Gate LI-1 on P2's own case copy, then freeze the low-inertia variant."""
import sys, logging
sys.path.insert(0, "Paper_2/src")
logging.getLogger('andes').setLevel(logging.WARNING)
import p2_common as m

result, ss = m.verify_li1_gate(k=m.K_FROZEN, rho=m.RHO_LI1, tf=m.TF_INITIAL, verbose=True)

assert result['gate_pass'], "Gate LI-1 did NOT reproduce on P2's own case copy -- STOP, escalate."

ok, variant_ss = m.save_variant(k=m.K_FROZEN)
print(f"\nVariant saved to {m.VARIANT_CASE}: {ok}")

import filecmp
same_as_p1 = filecmp.cmp("Paper_1/cases/ieee39/variants/ieee39_low_inertia.xlsx",
                          m.VARIANT_CASE, shallow=False)
print(f"Byte-identical to Paper_1's frozen variant: {same_as_p1}")
