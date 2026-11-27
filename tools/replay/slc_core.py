import json
import struct
import zlib
import numpy as np
from scipy import fft, signal

C = 299792458.0


# Original scene.py SHA-256 e4980fadd41a611c715098438b61a94e15cd40c960743fde29db3ccae50b42d7


class Scene:
    # BigTIFF tile layout follows the parent lane's verified reader, implemented here for standalone replay.
    def __init__(self,p):
        self.p=p
        self.f=f=p.open('rb')
        assert f.read(8)==b'II+\x00\x08\x00\x00\x00'
        f.seek(struct.unpack('<Q',f.read(8))[0])
        count=struct.unpack('<Q',f.read(8))[0]
        entries=[struct.unpack('<HHQ8s',f.read(20)) for _ in range(count)]
        tags={}
        for k,t,n,raw in entries:
            dtype={3:'<u2',4:'<u4',12:'<f8',16:'<u8'}.get(t)
            if dtype is None: continue
            size=n*np.dtype(dtype).itemsize
            if size>8:
                f.seek(struct.unpack('<Q',raw)[0]); raw=f.read(size)
            tags[k]=np.frombuffer(raw[:size],dtype=dtype)
        self.tags=tags
        self.meta=p.with_name(p.stem+'_extended.json')
        self.collect=json.loads(self.meta.read_text())['collect']
        self.im=self.collect['image']; self.g=self.im['image_geometry']
        self.T=float((np.datetime64(self.collect['stop_timestamp'][:-1])-np.datetime64(self.collect['start_timestamp'][:-1]))/np.timedelta64(1,'s'))
        assert all(tags[k].item()==v for k,v in {256:self.im['columns'],257:self.im['rows'],258:32,259:8,277:1,317:1,322:512,323:512,339:5}.items())

    def rpc(self, points):
        lat,lon,h=np.asarray(points).T
        d=self.tags[50844]
        x,y,z=(lon-d[5])/d[10],(lat-d[4])/d[9],(h-d[6])/d[11]
        v=np.array([np.ones_like(x),x,y,z,x*y,x*z,y*z,x*x,y*y,z*z,x*y*z,x**3,x*y*y,x*z*z,x*x*y,y**3,y*z*z,x*x*z,y*y*z,z**3])
        f=lambda i:np.einsum('i,in->n',d[i:i+20],v)
        return np.column_stack((d[2]+d[7]*f(12)/f(32),d[3]+d[8]*f(52)/f(72)))

    def read(self,origin,shape):
        r,c=origin
        h,w=shape
        assert r>=0 and c>=0 and r+h<=self.im['rows'] and c+w<=self.im['columns']
        out=np.empty((h,w),np.complex64)
        for y in range(r//512,(r+h-1)//512+1):
            for x in range(c//512,(c+w-1)//512+1):
                i=y*((self.im['columns']+511)//512)+x
                self.f.seek(int(self.tags[324][i]))
                raw=zlib.decompress(self.f.read(int(self.tags[325][i])))
                tile=np.frombuffer(raw,'<i2').reshape(512,512,2)
                y0,y1=max(y*512,r),min((y+1)*512,r+h)
                x0,x1=max(x*512,c),min((x+1)*512,c+w)
                t=tile[y0-y*512:y1-y*512,x0-x*512:x1-x*512]
                out[y0-r:y1-r,x0-c:x1-c]=t[:,:,0]+1j*t[:,:,1]
        return out


def support(scene,shape,polarity=1):
    # Candidate 2D spatial-frequency mapping on the nominal slant PFA grid.
    # Row corresponds to metadata col direction. Time comes from the polar angle polynomial.
    g=scene.g
    a=fft.fftfreq(shape[0],g['col_sample_spacing'])[:,None]
    r=fft.fftfreq(shape[1],g['row_sample_spacing'])[None,:]
    carrier=2*scene.collect['radar']['center_frequency']/C
    radial=np.hypot(carrier+r,a)
    angle=polarity*np.arctan2(a,carrier+r)
    times=np.linspace(0,scene.T,2049)
    angles=np.polynomial.polynomial.polyval(times,g['polar_angle_polynomial']['coefficients'])
    assert np.all(np.diff(angles)>0) or np.all(np.diff(angles)<0)
    if angles[-1]<angles[0]: angles,times=angles[::-1],times[::-1]
    time=np.interp(angle,angles,times,left=np.nan,right=np.nan).astype('f')
    # Processed bandwidth is treated as a rectangular range-spatial-frequency passband.
    # On an already resampled Cartesian PFA product this need not be the original polar footprint.
    keep=np.abs(r)<=scene.im['processed_range_bandwidth']/C
    time=np.where(keep,time,np.nan)
    return time,radial,angle


def register(a,b):
    """Complex patch correlation. One upsampled DFT near the coarse peak, evaluated by Newton."""
    cross=fft.fft2(b,axes=(-2,-1))*fft.fft2(a,axes=(-2,-1)).conj()
    n,h,w=a.shape
    ip=np.abs(fft.ifft2(cross,axes=(-2,-1))).reshape(n,-1).argmax(1)
    rc=np.column_stack(np.unravel_index(ip,(h,w))).astype(float)
    rc=(rc+np.array([h,w])/2)%[h,w]-np.array([h,w])/2
    u=2j*np.pi*fft.fftfreq(h);v=2j*np.pi*fft.fftfreq(w)
    terms=np.array([np.ones((h,w)),np.broadcast_to(u[:,None],(h,w)),np.broadcast_to(v,(h,w)),
                    np.broadcast_to(u[:,None]**2,(h,w)),u[:,None]*v,np.broadcast_to(v**2,(h,w))]).reshape(6,-1).T.copy()
    # The sampled integer maximum can lie outside the concave neighbourhood of the DFT peak.
    # Bracket it explicitly before Newton refinement, especially on narrowband real image patches.
    offsets=np.linspace(-1,1,11)
    centered=cross*np.exp(rc[:,0,None]*u)[:,:,None]*np.exp(rc[:,1,None]*v)[:,None,:]
    ey=np.exp(offsets[:,None]*u); ex=np.exp(v[:,None]*offsets)
    with np.errstate(all='ignore'):
        local=np.abs((ey@centered)@ex)
    assert np.isfinite(local).all()
    ii,jj=np.unravel_index(local.reshape(n,-1).argmax(1),(11,11))
    rc+=np.column_stack([offsets[ii],offsets[jj]])
    for _ in range(5):
        p=cross*np.exp(rc[:,0,None]*u)[:,:,None]*np.exp(rc[:,1,None]*v)[:,None,:]
        with np.errstate(all='ignore'):  # Accelerate may raise stale IEEE status flags after finite complex GEMM.
            sums=p.reshape(n,-1)@terms
        assert np.isfinite(sums).all() and np.allclose(sums[0],np.einsum('j,jk->k',p[0].ravel(),terms),rtol=1e-8,atol=1e-6)
        f,fy,fx,fyy,fyx,fxx=sums.T
        re=lambda a,b:(a.conj()*b).real
        gy,gx=re(f,fy),re(f,fx)
        yy,xx,yx=re(f,fyy)+abs(fy)**2,re(f,fxx)+abs(fx)**2,re(f,fyx)+re(fy,fx)
        det=yy*xx-yx*yx
        good=(det>0)&(yy<0)
        dy=np.divide(xx*gy-yx*gx,det,out=np.zeros(n),where=good)
        dx=np.divide(yy*gx-yx*gy,det,out=np.zeros(n),where=good)
        step=np.clip(np.stack([dy,dx],axis=1),-.45,.45)
        rc-=step
        if abs(step).max()<1e-5: break
    p=cross*np.exp(rc[:,0,None]*u)[:,:,None]*np.exp(rc[:,1,None]*v)[:,None,:]
    f=p.sum((1,2))/(h*w)
    qual=abs(f)/np.sqrt((abs(a)**2).sum((1,2))*(abs(b)**2).sum((1,2)))
    return rc,np.angle(f),qual


def ecef(pts):
    lat,lon=np.deg2rad(pts[:,:2]).T
    h=pts[:,2]
    e2=6.6943799901413165e-3
    N=6378137./np.sqrt(1-e2*np.sin(lat)**2)
    up=np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])
    xyz=up*(N+h)[:,None]
    xyz[:,2]-=N*e2*np.sin(lat)
    return xyz,up


def orbit(scene,ts):
    from scipy.interpolate import CubicHermiteSpline
    if not hasattr(scene,'_ecef_spline'):
        vec=scene.collect['state']['state_vectors']
        start=np.datetime64(scene.collect['start_timestamp'][:-1])
        t=np.array([(np.datetime64(v['time'][:-1])-start)/np.timedelta64(1,'s') for v in vec])
        scene._ecef_spline=CubicHermiteSpline(t,[v['position'] for v in vec],[v['velocity'] for v in vec])
    return scene._ecef_spline(ts)


def steering(scene,t,pts):
    xyz,up=ecef(pts)
    def pos(ts):return orbit(scene,ts)
    t0=scene.T/2
    los=pos([t0])-xyz
    los/=np.linalg.norm(los,axis=1)[:,None]
    v=(pos([t0+.05])-pos([t0-.05]))[0]/.1
    axis=v-los*np.sum(v*los,axis=1)[:,None]
    axis/=np.linalg.norm(axis,axis=1)[:,None]
    b=np.einsum('kc,nc->kn',pos(t)-pos([t0]),axis)
    ranges=np.linalg.norm(pos(t)[:,None,:]-xyz,axis=2)
    return 4*np.pi*b/(ranges*np.sqrt(1-(los*up).sum(1)**2))


