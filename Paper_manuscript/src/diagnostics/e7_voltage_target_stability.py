import numpy as np, andes
andes.config_logger(stream_level=40)
def eig(alpha,mods={}):
    s=andes.load('Paper_manuscript/cases/ieee39_C2_6SG_4GFM.xlsx',setup=False,default_config=True,no_output=True)
    s.PQ.config.p2p,s.PQ.config.p2i,s.PQ.config.p2z=1.,0.,0.; s.PQ.config.q2q,s.PQ.config.q2i,s.PQ.config.q2z=1.,0.,0.
    s.setup()
    for m in ('PV','Slack'):
        d=getattr(s,m); d.v0.v[:]=d.v0.v+alpha*(1.0-d.v0.v)
    s.PFlow.run()
    for k,m in mods.items(): getattr(s.REGF1,k).v[:]*=m
    s.EIG.run(); mu=np.asarray(s.EIG.mu)
    phys=mu[~((np.abs(mu.imag)<1e-9)&(np.abs(mu.real-1)<1e-6))]
    osc=[m for m in phys if m.imag>0 and 8<m.imag<30]
    w=min(osc,key=lambda m:-m.real/abs(m))
    print(mods,f'alpha={alpha:.2f} max_real_phys={phys.real.max():+.3f} least damped osc {w.real:+.2f}{w.imag:+.2f}j zeta={-w.real/abs(w):.3f}',flush=True)
for mods in ({'KPv':1.25},{'KPv':1.5},{'KPv':2.0},{'Qdrp':1.5},{'Qdrp':2.0}):
    for a in (0.0,1.0): eig(a,mods)
