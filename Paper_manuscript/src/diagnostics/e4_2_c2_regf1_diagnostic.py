import sys,numpy as np,andes
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from matrix_pencil import matrix_pencil
andes.config_logger(stream_level=40)
CASE='Paper_manuscript/cases/ieee39_C2_6SG_4GFM.xlsx'   # read only
ORDER=None
def build(mods,event=True):
    s=andes.load(CASE,setup=False,default_config=True,no_output=True)
    s.PQ.config.p2p,s.PQ.config.p2i,s.PQ.config.p2z=1.,0.,0.; s.PQ.config.q2q,s.PQ.config.q2i,s.PQ.config.q2z=1.,0.,0.
    if event:
        tgt=[str(i) for i,b in zip(s.PQ.idx.v,s.PQ.bus.v) if int(b)==4][0]
        s.add('Alter',idx='A0',t=5.0,model='PQ',dev=tgt,src='Ppf',attr='v',method='+',amount=0.01*float(np.sum(s.PQ.p0.v)))
    s.setup()
    buses=list(map(int,s.REGF1.bus.v))
    for k,m in mods.items():
        mult=np.array([m.get(b,1.0) if isinstance(m,dict) else m for b in buses],float)
        getattr(s.REGF1,k).v[:]*=mult
    return s,buses
def tds(mods):
    s,buses=build(mods); s.TDS.config.tf=14.0; s.TDS.config.tstep=0.00390625; s.TDS.config.fixt=1; s.TDS.config.no_tqdm=1
    s.PFlow.run(); ok=s.TDS.run(no_summary=True)
    t=np.asarray(s.dae.ts.t); v=np.asarray(s.dae.ts.y[:,s.Bus.v.a]); f=np.asarray(s.dae.ts.y[:,s.BusFreq.f.a])*60; ids=list(s.Bus.idx.v)
    return ok,t,v,f,ids,buses
def report(tag,mods):
    try: ok,t,v,f,ids,buses=tds(mods)
    except Exception as e: print(f'{tag:28s} ERR {str(e)[:50]}',flush=True); return
    if not ok or t[-1]<13.9: print(f'{tag:28s} TDS INCOMPLETE (t_end={t[-1]:.2f}s)',flush=True); return
    w=(t>=5.3)&(t<=6.3); rip=max(np.std(v[w,ids.index(b)]-np.polyval(np.polyfit(t[w],v[w,ids.index(b)],1),t[w])) for b in buses)
    x=v[:,ids.index(36)]; m=(t>=5.15)&(t<=12); y=x[m][::4]; s_,c=matrix_pencil(y,(t[1]-t[0])*4,14)
    rows=[(2*abs(ci),si) for si,ci in zip(s_,c) if si.imag>0 and 0.5<=si.imag/2/np.pi<=6]
    a,si=max(rows,key=lambda r:r[0]); z=-si.real/abs(si)
    print(f'{tag:28s} ripple_std_max={rip:.5f} dom={si.imag/2/np.pi:.2f}Hz zeta={z:.3f} Vmin={v.min():.4f} Vmax={v.max():.4f} df_end={f[-1].mean()-60:+.4f}Hz',flush=True)
def eig(tag,mods):
    s,b=build(mods,event=False); s.PFlow.run(); s.EIG.run(); mu=np.asarray(s.EIG.mu)
    c=[m for m in mu if m.imag>0 and 8<m.imag<30 and -(m.real)/abs(m)<0.5]
    print(f'EIG {tag:24s} lightly damped (zeta<0.5) modes 8-30 rad/s:',[f'{m.real:.2f}{m.imag:+.2f}j(f={m.imag/2/np.pi:.2f},z={-m.real/abs(m):.2f})' for m in c],flush=True)
print('--- baseline'); report('baseline',{}); eig('baseline',{})
print('--- per-unit (only that GFM modified)')
for b in (32,34,36,37):
    report(f'KPv x2 only GFM{b}',{'KPv':{b:2.0}}); report(f'Qdrp x2 only GFM{b}',{'Qdrp':{b:2.0}})
print('--- finer scan, all GFM')
for k,ms in (('KPv',(1.25,1.5,3.0)),('Qdrp',(0.75,1.5,3.0)),('Tpm',(0.75,1.5)),('wdrp',(0.75,1.5))):
    for m in ms: report(f'{k} x{m}',{k:m})
print('--- combinations')
report('KPv x2 + Tpm x0.5',{'KPv':2.0,'Tpm':0.5}); report('KPv x2 + Qdrp x2',{'KPv':2.0,'Qdrp':2.0})
print('--- EIG on variants')
for tag,mods in (('Tpm x0.5',{'Tpm':0.5}),('KPv x2',{'KPv':2.0}),('Qdrp x2',{'Qdrp':2.0}),('wdrp x0.5',{'wdrp':0.5})): eig(tag,mods)
