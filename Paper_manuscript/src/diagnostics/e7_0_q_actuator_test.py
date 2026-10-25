import sys, numpy as np, andes
andes.config_logger(stream_level=40)
CASE='Paper_manuscript/cases/ieee39_C2_6SG_4GFM.xlsx'
def run(kind, amt, kc=0.05):
    s=andes.load(CASE,setup=False,default_config=True,no_output=True)
    s.PQ.config.p2p,s.PQ.config.p2i,s.PQ.config.p2z=1.,0.,0.; s.PQ.config.q2q,s.PQ.config.q2i,s.PQ.config.q2z=1.,0.,0.
    s.setup(); s.PFlow.run()
    s.TDS.config.tf=30.0; s.TDS.config.tstep=0.00390625; s.TDS.config.fixt=1; s.TDS.config.no_tqdm=1
    st={}
    sg_idx=list(s.GENROU.bus.v).index(31)
    def pert(t,sys_):
        t=float(t); r=min(max((t-2.0)/5.0,0.0),1.0)*amt
        if 'y0' not in st:
            st['y0']=float(sys_.dae.y[sys_.REGF1.PIqlim_y.a[0]]); st['v0']=float(sys_.REGF1.vref.v[0]); st['e0']=float(sys_.IEEEX1.vref0.v[sg_idx])
        if kind=='gfm_qaux':
            sys_.REGF1.Qaux0.v[0]=kc*(st['y0']+r-float(sys_.dae.y[sys_.REGF1.PIqlim_y.a[0]]))
        elif kind=='gfm_vref':
            sys_.REGF1.vref.v[0]=st['v0']+r
        elif kind=='sg_vref':
            sys_.IEEEX1.vref0.v[sg_idx]=st['e0']+r
    s.TDS.callpert=pert
    s.TDS.init(); ok=s.TDS.run(no_summary=True)
    t=np.asarray(s.dae.ts.t); y=s.dae.ts.y
    i=lambda tt:min(int(np.searchsorted(t,tt)),len(t)-1)
    if kind.startswith('gfm'):
        q=y[:,s.REGF1.Qe.a[0]]; p=y[:,s.REGF1.Pe.a[0]]; v=y[:,s.REGF1.v.a[0]]
    else:
        q=y[:,s.GENROU.Qe.a[sg_idx]]; p=y[:,s.GENROU.Pe.a[sg_idx]]; v=y[:,s.Bus.v.a[list(s.Bus.idx.v).index(31)]]
    f=y[:,s.BusFreq.f.a].mean(1)*60
    print(kind,amt,'ok',ok,'t_end',round(t[-1],1),'dQ(t=1.9->29.9)=%.4f dV=%.4f dP=%.4f df=%.4f'%(q[i(29.9)]-q[i(1.9)],v[i(29.9)]-v[i(1.9)],p[i(29.9)]-p[i(1.9)],f[i(29.9)]-60),flush=True)
for k,a in (('gfm_qaux',0.2),('gfm_qaux',-0.2),('gfm_vref',0.01),('sg_vref',0.01),('sg_vref',-0.01)):
    try: run(k,a)
    except Exception as e: print(k,a,'ERR',str(e)[:80],flush=True)
