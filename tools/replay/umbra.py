"""Frozen transfer to the three local public SICD products. Sarpy is needed only for measure."""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode=True
import measure as m
import score as s
import json
import numpy as np
from scipy import fft,signal

HERE=Path(__file__).resolve().parent
PROTOCOL="35c3c08d9e774a8326da8b7b53654df6b42a4d62c95c363db0db024fa9511a8b"
DATES=("2023-02-07","2023-02-08","2023-03-08")
HASHES=("a0a54f0fbb91b97c2b1dda4ba4a795f5dbfecbd9dad9271ffe0c3af5088b8160",
        "b3735514639b0543b3c1b88ef01e19995b0e268000860b38f3aab53afc7e93f0",
        "4aa372d7485c999e8a2155cacce942a6671f5c48ada068b003b62bfd1f8f89d4")


class Umbra:
    def __init__(self,path):
        from sarpy.io.complex.converter import open_complex
        self.reader=open_complex(str(path))
        self.sicd,=self.reader.get_sicds_as_tuple()
        s=self.sicd
        assert s.ImageFormation.ImageFormAlgo=="PFA" and s.Grid.Type=="RGAZIM"
        assert s.Grid.Row.Sgn==s.Grid.Col.Sgn==-1
        assert s.ImageData.FirstRow==s.ImageData.FirstCol==0
        self.im=dict(pixel_spacing_row=s.Grid.Row.SS,pixel_spacing_column=s.Grid.Col.SS,scale_factor=1.)
        self.t0,self.t1=s.ImageFormation.TStartProc,s.ImageFormation.TEndProc

    def rpc(self,pts):
        pixels,res,iterations=self.sicd.project_ground_to_image_geo(pts)
        assert np.isfinite(pixels).all()
        return pixels

    def read(self,origin,shape):
        r,c=map(int,origin)
        h,w=map(int,shape)
        nr,nc=self.reader.get_data_size_as_tuple()[0]
        assert 0<=r<r+h<=nr and 0<=c<c+w<=nc
        return np.asarray(self.reader[r:r+h,c:c+w])


def orbit_geometry(scene,t,pts):
    xyz,up=m.core.ecef(pts)
    poly=scene.sicd.Position.ARPPoly
    middle=(scene.t0+scene.t1)/2
    center=poly(middle)
    los=center-xyz
    los /= np.linalg.norm(los,axis=1)[:,None]
    vel=poly.derivative_eval(middle)
    tangent=vel-los*np.sum(los*vel,axis=1)[:,None]
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    orbit=poly(t)
    dot=np.einsum("tc,nc->tn",orbit-center,tangent)
    ranges=np.linalg.norm(orbit[:,None,:]-xyz,axis=2)
    sin=np.sqrt(1-np.sum(los*up,axis=1)**2)
    elevation_axis=(up-np.sum(up*los,axis=1)[:,None]*los)/sin[:,None]
    vertical_dot=np.einsum("tc,nc->tn",orbit-center,elevation_axis)
    return 4*np.pi*dot/(ranges*sin), 4*np.pi*vertical_dot/(ranges*sin)


def run(folder,date,out):
    import sarpy
    stamp=m.utc()
    path,=folder.glob(date+"*SICD.nitf")
    digest=m.sha(path)
    assert digest==HASHES[DATES.index(date)]
    scene=Umbra(path)
    meta=scene.sicd
    with np.load(HERE/"20240916.npz",allow_pickle=False) as reference:
        pts=reference["lat_lon_hae"]
        en=reference["east_north"]
    rc=scene.rpc(pts)
    lo=np.floor(rc.min(0)).astype(int)-[148,660]
    hi=np.ceil(rc.max(0)).astype(int)+[148,660]
    shape=tuple(fft.next_fast_len(int(n)) for n in hi-lo)
    img=scene.read(lo,shape).T.copy()
    centers=(np.floor(rc).astype(int)+1-lo)[:,::-1]
    az,rg=centers.T
    coarse=(az[:,None,None]+np.arange(-64,64)[None,:,None],rg[:,None,None]+np.arange(-64,64)[None,None,:])
    fine=(az[:,None,None]+np.arange(-12,12)[None,:,None],rg[:,None,None]+np.arange(-16,16)[None,None,:])
    spacing=np.array([meta.Grid.Col.SS,meta.Grid.Row.SS])
    taper=signal.windows.tukey(img.shape[0],.075)[:,None]*signal.windows.tukey(img.shape[1],.12)[None,:]
    sp=fft.fft2(img*taper.astype("f"),workers=2)
    kaz=meta.Grid.Col.KCtr+fft.fftfreq(img.shape[0],spacing[0])[:,None]
    krg=meta.Grid.Row.KCtr+fft.fftfreq(img.shape[1],spacing[1])[None,:]
    pfa=meta.PFA
    keep=(kaz>=pfa.Kaz1)&(kaz<=pfa.Kaz2)&(krg>=pfa.Krg1)&(krg<=pfa.Krg2)
    sampled_t=np.linspace(scene.t0,scene.t1,4097)
    angles=pfa.PolarAngPoly(sampled_t)
    if angles[0]>angles[-1]:
        angles,sampled_t=angles[::-1],sampled_t[::-1]
    assert np.all(np.diff(angles)>0)
    tau=np.interp(np.arctan2(kaz,krg),angles,sampled_t,left=np.nan,right=np.nan)
    keep &= np.isfinite(tau)
    T=scene.t1-scene.t0
    times=scene.t0+np.linspace(.25,.75,m.NLOOK)*T
    prev=None
    result=[]
    for t in times:
        rel=(tau-t)/(T*.25)
        wt=np.where(keep&(abs(rel)<=1), .54+.46*np.cos(np.pi*rel),0).astype("f")
        look=fft.ifft2(sp*wt,workers=2)
        state=(fft.fft2(look[coarse],axes=(1,2),workers=2),look[fine])
        if prev is not None:
            result.append(m.pair(prev,look,state[0],fine))
        prev=state
    shift,qual,off,phase=map(np.asarray,zip(*result))
    mid=(times[:-1]+times[1:])/2
    along,elevation=orbit_geometry(scene,mid,pts)
    proj,zinit,_=meta.project_ground_to_image_geo(pts)
    powers=abs(sp)**2
    primary_surface=m.geo.surface(scene,m.geo.PAVEMENT)
    numeric=out/(date+"-umbra.npz")
    np.savez_compressed(numeric,spacing=spacing,power=np.median(abs(img[fine])**2,axis=(1,2)),east_north=en,native_row_col=rc,
        lat_lon_hae=pts,adjacent_times=mid,adjacent_shift=shift,adjacent_correlation=qual,adjacent_phase=phase,
        adjacent_coarse=off,adjacent_along=along,adjacent_elevation=elevation)
    s.write(out/(date+"-umbra-source.json"),dict(start=stamp,end=m.utc(),product=path.name,sha256=digest,bytes=path.stat().st_size,
        protocol_sha256=PROTOCOL,code_sha256=m.sha(Path(__file__)),core_sha256=m.sha(Path(m.core.__file__)),measure_sha256=m.sha(Path(m.__file__)),
        compact_sha256=m.sha(numeric),sarpy_version=sarpy.__version__,side_of_track=meta.SCPCOA.SideOfTrack,polarization=meta.ImageFormation.TxRcvPolarizationProc,
        collect_duration=meta.Timeline.CollectDuration,processed_interval=[scene.t0,scene.t1],polar_angles_rad=[angles[0],angles[-1]],
        spectral_power_fraction_on_support=float(powers[keep].sum(dtype=float)/powers.sum(dtype=float)),
        projection_max_residual_m=float(np.max(zinit)),roi_origin_rc=lo.tolist(),roi_shape_rc=shape,n_positions=len(pts),in_bounds=True,
        coarse_patch_az_rg_m=(128*spacing).tolist(),fine_patch_az_rg_m=(np.array([24,32])*spacing).tolist(),surface=primary_surface))
    scene.reader.close()


class FrozenAcquisition(s.Acquisition):
    def __init__(self,date,folder=HERE):
        src=json.loads((folder/(date+"-umbra-source.json")).read_text())
        f=folder/(date+"-umbra.npz")
        assert m.sha(f)==src["compact_sha256"] and src["protocol_sha256"]==PROTOCOL
        with np.load(f,allow_pickle=False) as inp:
            arrays={k:inp[k] for k in inp.files}
            self.banks={"adjacent":s.PairBank(arrays,"adjacent")}
            self.power=arrays["power"]
            self.corr_quantiles=np.quantile(arrays["adjacent_correlation"],[.05,.5,.95]).tolist()


def evaluate():
    recipe=tuple(json.loads((HERE/"training-lock.json").read_text())["winner"]["recipe"])
    assert recipe==("adjacent","along",.48,"whitened")
    out={}
    for date in DATES:
        obj=FrozenAcquisition(date)
        p=obj.profiles(recipe)
        primary={}
        for name in s.TARGETS:
            vals=obj.positions(recipe,name)
            ranks=[s.rank(v)["beaten"] for v in vals]
            primary[name]=dict(positions=[v.tolist() for v in vals],ranks_focus_rms_brightness=ranks,
                               passes=ranks[0]>=31 and ranks[0]>max(ranks[1:]))
        src=json.loads((HERE/(date+"-umbra-source.json")).read_text())
        out[date]=dict(ranks=primary,profiles=p,all_three_pass=all(v["passes"] for v in primary.values()),corr_quantiles=obj.corr_quantiles,
                       surface_rank=src["surface"]["beaten"])
        print(date,out[date]["surface_rank"],{n:v["ranks_focus_rms_brightness"] for n,v in primary.items()},
              [p[n]["unrestricted_peak"] for n in primary])
    s.write(HERE/"umbra-result.json",dict(protocol_sha256=PROTOCOL,recipe=recipe,dates=out))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data",type=Path)
    parser.add_argument("--date",choices=DATES)
    parser.add_argument("--out",type=Path,default=HERE,help="Destination for measured arrays")
    args=parser.parse_args()
    assert m.sha(HERE/"umbra-protocol.json")==PROTOCOL
    if args.date:
        args.out.mkdir(exist_ok=True,parents=True)
        run(args.data,args.date,args.out)
    else:
        evaluate()
