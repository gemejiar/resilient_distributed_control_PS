import numpy as np
def matrix_pencil(y,dt,order,L=None):
    N=len(y); L=L or N//3
    Y=np.array([y[i:i+L+1] for i in range(N-L)])
    U,S,Vt=np.linalg.svd(Y,full_matrices=False)
    V=Vt[:order].conj().T
    z=np.linalg.eigvals(np.linalg.pinv(V[:-1])@V[1:])
    s=np.log(z)/dt
    # amplitudes by LS
    n=np.arange(N); Z=np.vander(z,N,increasing=True).T
    c=np.linalg.lstsq(Z,y,rcond=None)[0]
    return s,c
def report(tag,t,x,t0,t1,order=14,dec=4):
    m=(t>=t0)&(t<=t1); tt=t[m][::dec]; y=x[m][::dec]; dt=tt[1]-tt[0]
    y=y-y[-1]*0  # keep offset as mode ~0
    s,c=matrix_pencil(y,dt,order)
    res=np.linalg.norm(y-np.real(np.vander(np.exp(s*dt),len(y),increasing=True).T@c))/np.linalg.norm(y)
    print(tag,f'(rel.fit err {res:.3f})')
    rows=[(abs(ci),si) for si,ci in zip(s,c) if si.imag>=0 and abs(si.imag)/2/np.pi<20]
    for a,si in sorted(rows,key=lambda r:-r[0])[:7]:
        f=si.imag/2/np.pi; z=-si.real/abs(si) if abs(si)>0 else 1
        print(f'   amp {2*a:.5f}  f={f:5.2f}Hz sigma={si.real:7.2f} zeta={z:.3f}')
if __name__=='__main__':
    for tag,fn,pre,bus in [('C2 P+ bus36','IEEE39_E4_2_C2_timeseries.npz','P+',36),('C2 P+ bus32','IEEE39_E4_2_C2_timeseries.npz','P+',32),('C2 P+ bus39','IEEE39_E4_2_C2_timeseries.npz','P+',39),('C2 Q+ bus36','IEEE39_E4_2_C2_timeseries.npz','Q+',36),('C1a P+ bus34','IEEE39_E4_1_C1a_timeseries.npz','P+',34),('C1a P+ bus39','IEEE39_E4_1_C1a_timeseries.npz','P+',39)]:
        z=np.load(fn); t=z[pre+'_time_s']; ids=list(z[pre+'_bus_ids']); v=z[pre+'_bus_voltage_pu'][:,ids.index(bus)]
        report(tag,t,v,5.15,12.0)
