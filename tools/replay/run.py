"""Reproduce 36 training choices and six transfer rows from measured image-offset series."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from score import Acquisition, DATES, HERE, TARGETS, evaluate, train
from umbra import DATES as UMBRA_DATES, FrozenAcquisition


def run(out,inputs):
    out.mkdir(exist_ok=True, parents=True)
    with (HERE/"expected.json").open() as stream:
        expected=json.load(stream)
    train(inputs,out)
    evaluate(inputs,out)
    result=json.loads((out/"result.json").read_text())
    assert result["selection"]==expected["selected"]
    checked={}
    for day in DATES:
        grid=result["acquisitions"][day]["all_candidates"]
        ranks={k:{name:s["beaten"] for name,s in v.items()} for k,v in grid.items()}
        assert len(ranks)==36 and ranks==expected["acquisitions"][day]["scores"]
    for day in (*DATES,*UMBRA_DATES):
        obj=Acquisition(day,inputs) if day in DATES else FrozenAcquisition(day,inputs)
        rows={}
        peaks=obj.profiles(result["selection"])
        for site in TARGETS:
            values=obj.positions(result["selection"],site)
            observed=[int(sum(v[0]>v[1:])) for v in values]
            assert observed==expected["acquisitions"][day]["ranks"][site]
            assert peaks[site]["unrestricted_peak"]==expected["acquisitions"][day]["peaks"][site]
            rows[site]={"focus_rms_power_ranks":observed,"free_height_peak_m":peaks[site]["unrestricted_peak"]}
        checked[day]=rows
    summary={"verified":True,"candidate_count":36,"selection":result["selection"],"tests":checked}
    (out/"six-scenes.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("Verified 36 candidate ranks at three sites on three dates, plus the locked recipe on all six scenes.")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs",type=Path,default=HERE,help="Use bundled arrays or a newly measured set")
    parser.add_argument("--out",type=Path,help="Keep numerical results here. Default checks without writing into this checkout.")
    args=parser.parse_args()
    if args.out:
        run(args.out,args.inputs)
    else:
        with TemporaryDirectory() as work:
            run(Path(work),args.inputs)
