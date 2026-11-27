"""Measure two-stage registration from native SLCs. Numerical analysis is separate."""
import argparse
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

for name in ("OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[name] = "1"
import numpy as np
from scipy import fft, signal

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
import slc_core as core
import geography as geo
import iceye as ice

PROTOCOL = "e2515a3d6cfb282c160b1cf292ed27cd93a41c868809b822ea5f70dbbd80bc24"
NLOOK = 193
MASTER = NLOOK // 2
HASHES = {**geo.EXPECTED_TIFF, "20250602":"4b714856f1e64aa316d20c814121362cab14fc4ec36ab26012d58c5068e1cf11"}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def model_inputs(scene, iceye, pts):
    rc = scene.rpc(pts)
    # Internally both products use azimuth first.
    guard = np.array([660,148])
    if iceye:
        guard = guard[::-1]
    lo = np.floor(rc.min(0)).astype(int) - guard
    hi = np.ceil(rc.max(0)).astype(int) + guard
    shape = tuple(fft.next_fast_len(int(k)) for k in hi-lo)
    img = scene.read(lo, shape)
    centers = np.floor(rc).astype(int) + 1 - lo
    if iceye:
        img = np.ascontiguousarray(img.T)
        centers = centers[:, ::-1]
        taper = signal.windows.tukey(img.shape[0], .075)[:, None].astype("f")
        spectrum = fft.fft(img*taper, axis=0, workers=2)
        freq = fft.fftfreq(img.shape[0])[:, None]
        tau = np.where(abs(freq) <= scene.fraction/2, scene.T*(.5+freq/scene.fraction), np.nan)
        inverse = lambda x: fft.ifft(x, axis=0, workers=2)
        spacing = scene.spacing[::-1]
    else:
        taper = signal.windows.tukey(shape[0], .075)[:, None] * signal.windows.tukey(shape[1], .12)[None, :]
        spectrum = fft.fft2(img*taper.astype("f"), workers=2)
        tau, _, _ = core.support(scene, shape)
        inverse = lambda x: fft.ifft2(x, workers=2)
        spacing = np.array([scene.g["col_sample_spacing"], scene.g["row_sample_spacing"]])
    times = np.nan_to_num(tau, nan=-scene.T*2)
    az, rg = centers.T
    coarse = (az[:,None,None]+np.arange(-64,64)[None,:,None], rg[:,None,None]+np.arange(-64,64)[None,None,:])
    fine = (az[:,None,None]+np.arange(-12,12)[None,:,None], rg[:,None,None]+np.arange(-16,16)[None,None,:])
    def look(t):
        rel = (times-t)/(scene.T/4)
        weight = np.where(abs(rel)<=1, .54+.46*np.cos(np.pi*rel), 0).astype("f")
        return inverse(spectrum*weight)
    return rc, spacing, coarse, fine, look, np.median(abs(img[fine])**2, axis=(1,2))


def angular_geometry(scene, t, pts):
    xyz, up = core.ecef(pts)
    mid = core.orbit(scene, [scene.T/2])[0]
    los = mid-xyz
    los /= np.linalg.norm(los, axis=1)[:,None]
    cosine = (up*los).sum(1)
    sine = np.sqrt(1-cosine**2)
    elev = (up-cosine[:,None]*los)/sine[:,None]
    orbit = core.orbit(scene,t)
    ranges = np.linalg.norm(orbit[:,None,:]-xyz[None,:,:], axis=2)
    perpendicular = np.einsum("tc,nc->tn", orbit-mid, elev)
    return core.steering(scene,t,pts), 4*np.pi*perpendicular/(ranges*sine)


def pair(previous, current_img, current_transform, fine):
    previous_transform, previous_patch = previous
    corr = fft.ifft2(current_transform*previous_transform.conj(), axes=(1,2), workers=2)
    peak = np.argmax(abs(corr).reshape(len(corr),-1),axis=1)
    offset = (np.stack(np.unravel_index(peak, (128,128)),axis=1)+64) % 128 - 64
    shifted = (fine[0]+offset[:,0,None,None], fine[1]+offset[:,1,None,None])
    # Coarse registration moves the OFF patch center. The fine residual stays in the same axes.
    residual, phase, quality = core.register(previous_patch, current_img[shifted])
    return offset+residual, quality, offset, phase


def measure(folder, date, out):
    started = utc()
    assert sha(HERE/"protocol.json") == PROTOCOL
    iceye = date == "20250602"
    if iceye:
        folder = folder/"ICEYE"
        path = folder/(ice.STEM+".tif")
        metadata = path.with_suffix(".json")
    else:
        path, = folder.glob(f"*SLC_HH_{date}*.tif")
        metadata = path.with_name(path.stem+"_extended.json")
    assert sha(path) == HASHES[date]
    scene = ice.Iceye(folder) if iceye else core.Scene(path)
    offsets = np.vstack(([0.,0.],geo.ring((8,16,24,32),8)))
    en = np.vstack([*[offsets+[e,n] for e,n,_ in geo.SITES.values()],geo.ring((48,),32)])
    pts = geo.geographic(en,geo.PAVEMENT)
    rc,spacing,coarse,fine,look,power = model_inputs(scene,iceye,pts)
    times = np.linspace(.25,.75,NLOOK)*scene.T
    def prepare(img):
        return fft.fft2(img[coarse],axes=(1,2),workers=2), img[fine]
    fixed = prepare(look(times[MASTER]))
    results = {name:[] for name in ("adjacent","lag8","fixed")}
    cache = {}
    for i,t in enumerate(times):
        img = look(t)
        state = prepare(img)
        pairs = [(name, j, previous) for name, j, previous in
                 (("adjacent", i-1, cache.get(i-1)), ("lag8", i-8, cache.get(i-8)),
                  ("fixed", MASTER, fixed if i!=MASTER else None)) if previous is not None]
        for name,j,previous in pairs:
            measured = pair(previous,img,state[0],fine)
            results[name].append(((times[j]+t)*.5,*measured))
        cache[i] = state
        cache.pop(i-8,None)
        if i%32==0:
            print(utc(),date,i,"/",NLOOK-1,flush=True)
    payload = dict(spacing=spacing, power=power, lat_lon_hae=pts, native_row_col=rc, east_north=en, look_times=times)
    for name,series in results.items():
        mid,shift,quality,offset,phase = map(np.asarray, zip(*series))
        along,elev = angular_geometry(scene,mid,pts)
        payload.update({name+"_"+k:v for k,v in dict(times=mid, shift=shift, correlation=quality, coarse=offset,
                                                      phase=phase, along=along, elevation=elev).items()})
    assert all(np.isfinite(v).all() for v in payload.values())
    output=out/(date+".npz")
    np.savez_compressed(output,**payload)
    scene.f.close()
    (out/(date+"-source.json")).write_text(json.dumps(dict(start=started,end=utc(),product=path.name,input_sha256=HASHES[date],
        input_bytes=path.stat().st_size,metadata=metadata.name,metadata_sha256=sha(metadata),protocol_sha256=PROTOCOL,
        output_sha256=sha(output),code_sha256={p.name:sha(p) for p in [Path(__file__),Path(geo.__file__),Path(core.__file__),Path(ice.__file__)]}),indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("date", choices=HASHES)
    parser.add_argument("--out", type=Path, default=HERE)
    args = parser.parse_args()
    args.out.mkdir(exist_ok=True,parents=True)
    measure(args.data,args.date,args.out)
