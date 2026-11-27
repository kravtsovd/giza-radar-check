"""Run training-only choice, then evaluate its locked transfer. Inputs are portable measured arrays."""
import argparse
import hashlib
import itertools
import json
import os
from datetime import datetime, timezone
from pathlib import Path

for name in ("OPENBLAS_NUM_THREADS","VECLIB_MAXIMUM_THREADS","OMP_NUM_THREADS"):
    os.environ[name] = "1"

import numpy as np
import scipy
from scipy.linalg import cholesky, solve_triangular

HERE = Path(__file__).resolve().parent
PROTOCOL = "e2515a3d6cfb282c160b1cf292ed27cd93a41c868809b822ea5f70dbbd80bc24"
PAIRS = ("adjacent","lag8","fixed")
GEOMETRY = ("along","elevation")
LAMBDA = (.24,.30,.48)
FILTER = ("ordinary","whitened")
TARGETS = {"King":43.,"Queen":21.,"Subterranean":-30.}
DATES = ("20240916","20241004","20250602")
HEIGHT = np.r_[np.arange(-44.,0.,.5),np.arange(.5,44.01,.5)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path,d):
    path.write_text(json.dumps(d,allow_nan=False,indent=2)+"\n")


def center(a):
    return a-a.mean(axis=0,keepdims=True)


def norm2(a):
    return np.sum(abs(a)**2,axis=0)


def whiten(a,chol):
    return solve_triangular(chol,a,lower=True,check_finite=False) if chol is not None else a


def statistic(a,y):
    return abs(np.sum(a.conj()*y,axis=0))**2 / (norm2(a)*norm2(y))


def rank(values):
    control = values[1:]
    med = np.median(control)
    mad = np.median(abs(control-med))
    return {"beaten":int((control<values[0]).sum()),"ties":int((control==values[0]).sum()),
            "target":float(values[0]),"control_median":float(med),"control_mad":float(mad),
            "standardized_margin":float((values[0]-med)/max(mad,1e-15))}


def key(recipe):
    return "/".join(map(str,recipe))


class PairBank:
    # Noise weights use 32 spatial references only.
    def __init__(self,d,pair):
        v=d[pair+"_shift"]*d["spacing"]
        v-=np.median(v[:,-32:,:],axis=1)[:,None,:]
        self.y=v[...,0]+1j*v[...,1]
        self.rms=np.sqrt(np.mean(abs(self.y)**2,axis=0))
        self.y=center(self.y)
        refs=self.y[:,-32:]
        cov=np.einsum("tr,ur->tu",refs,refs.conj())/refs.shape[1]
        scale=cov.trace().real/len(cov)
        self.chol=cholesky(.75*cov+.25*scale*np.eye(len(cov)),lower=True)
        self.yw=whiten(self.y,self.chol)
        self.geometry={name:d[pair+"_"+name] for name in GEOMETRY}

    def match(self,geo,lam,filt,cols,z):
        a=center(np.exp(1j*self.geometry[geo][:,cols]*np.asarray(z)/lam))
        if filt=="ordinary":
            return statistic(a,self.y[:,cols])
        return statistic(whiten(a,self.chol),self.yw[:,cols])


class Acquisition:
    def __init__(self,date,path):
        src=json.loads((path/(date+"-source.json")).read_text())
        assert sha(path/(date+".npz"))==src["output_sha256"]
        assert src["protocol_sha256"]==PROTOCOL
        with np.load(path/(date+".npz"),allow_pickle=False) as d:
            self.banks={p:PairBank(d,p) for p in PAIRS}
            self.power=d["power"]
            self.diagnostics={}
            for p in PAIRS:
                corr=d[p+"_correlation"]
                coarse=d[p+"_coarse"]
                self.diagnostics[p]=dict(n_pairs=len(corr),whole_sample_shift_fraction=float(np.mean(np.any(coarse!=0,axis=2))),
                    corr_q05_median_q95=np.quantile(corr,[.05,.5,.95]).tolist(),
                    max_abs_coarse_px=int(abs(coarse).max()),
                    max_abs_fine_residual_px=np.max(abs(d[p+"_shift"]-coarse),axis=(0,1)).tolist())

    def positions(self,recipe,name):
        pair,geo,lam,filt=recipe
        i=list(TARGETS).index(name)
        cols=np.arange(33*i,33*(i+1))
        b=self.banks[pair]
        return b.match(geo,lam,filt,cols,TARGETS[name]),b.rms[cols],self.power[cols]

    def profiles(self,recipe):
        pair,geo,lam,filt=recipe
        b=self.banks[pair]
        out={}
        for i,(name,label) in enumerate(TARGETS.items()):
            col=slice(33*i,33*i+1)
            curve=b.match(geo,lam,filt,col,HEIGHT)
            k=b.geometry[geo][:,col]/lam
            atom=center(np.exp(1j*k*label))
            scan=center(np.exp(1j*k*HEIGHT))
            chol=b.chol if filt=="whitened" else None
            psf=statistic(whiten(scan,chol),whiten(atom,chol))
            winner=float(HEIGHT[curve.argmax()])
            out[name]=dict(grid=HEIGHT.tolist(),scores=curve.tolist(),unrestricted_peak=winner,peak_minus_label_m=winner-label,
                max_pair_step_at_label_rad=float(np.max(abs(np.diff(k[:,0])))*abs(label)),
                phase_span_at_label_rad=float(np.ptp(k)*abs(label)),height_of_injected_atom_peak=float(HEIGHT[psf.argmax()]),
                point_response_at_label=float(psf[HEIGHT==label].item()),point_response=psf.tolist())
            assert psf[HEIGHT==label].item()>.999999 and HEIGHT[psf.argmax()]==label
        return out


def recipes():
    return itertools.product(PAIRS,GEOMETRY,LAMBDA,FILTER)


def train(root,out):
    a=Acquisition(DATES[0],root)
    rows=[]
    for recipe in recipes():
        values,*_=a.positions(recipe,"King")
        rows.append(dict(recipe=list(recipe),**rank(values)))
    best=max(rows,key=lambda r:(r["beaten"],r["standardized_margin"]))
    write(out/"training-lock.json",dict(created=utc(),protocol_sha256=PROTOCOL,
        scorer_sha256=sha(Path(__file__)),training_input_sha256=sha(root/(DATES[0]+".npz")),selection="20240916 King alone",
        winner=best,candidates=rows))
    print("Training locked",best)


def evaluate(root,out):
    lock=json.loads((out/"training-lock.json").read_text())
    assert lock["protocol_sha256"]==PROTOCOL and lock["scorer_sha256"]==sha(Path(__file__))
    assert lock["training_input_sha256"]==sha(root/(DATES[0]+".npz"))
    chosen=lock["winner"]["recipe"]
    data={}
    for date in DATES:
        a=Acquisition(date,root)
        grid={}
        for recipe in recipes():
            grid[key(recipe)]={n:rank(a.positions(recipe,n)[0]) for n in TARGETS}
        primary={}
        for name in TARGETS:
            v,r,p=a.positions(chosen,name)
            scores,baseline,bright=map(rank,(v,r,p))
            passes=scores["beaten"]>=31 and scores["beaten"]>max(baseline["beaten"],bright["beaten"])
            primary[name]=dict(focus=scores,rms=baseline,brightness=bright,passes=passes,
                               positions=dict(focus=v.tolist(),rms=r.tolist(),power=p.tolist()))
        data[date]=dict(all_target_gate=all(v["passes"] for v in primary.values()), selected=primary,
                        profiles=a.profiles(chosen),all_candidates=grid,diagnostics=a.diagnostics)
        print(date,[(n,*[primary[n][k]["beaten"] for k in ["focus","rms","brightness"]]) for n in TARGETS])
    result=dict(created=utc(),protocol_sha256=PROTOCOL,scorer_sha256=sha(Path(__file__)),training_lock_sha256=sha(out/"training-lock.json"),
        software={"numpy":np.__version__,"scipy":scipy.__version__},selection=chosen,acquisitions=data)
    write(out/"result.json",result)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=["train","evaluate"])
    parser.add_argument("--inputs",type=Path,default=HERE)
    parser.add_argument("--out",type=Path,default=HERE)
    args=parser.parse_args()
    assert sha(HERE/"protocol.json")==PROTOCOL
    (train if args.stage=="train" else evaluate)(args.inputs,args.out)
