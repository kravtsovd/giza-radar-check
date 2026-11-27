"""Export named, first-party numerical findings from a supplied research folder."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# References to vendor-hosted inputs are retained. Raw downloads and third-party media stay with their publishers.
REPORTS = {
    "centroid": ["protocol.json", "result.json", "centroid_series.csv"],
    "ground-constraint": ["result.json", "sources.json"],
    "depth-audit": ["result.json", "observations.json", "sources.json"],
    "motion-reference": ["result.json", "complex-test3/result.json", "complex-scene/test2-result.json", "complex-test5/result.json", "complex-multitone/estimates.json"],
    "blind-cavity": ["result.json", "osario/result.json", "teotihuacan/result.json", "giza_transfer.json"],
    "code-audit": ["result.json"],
    "geo-retest": ["results.json", "alignment_results.json", "umbra_results.json"],
    "line-average": ["result.json", "published_result.json", "placebo.json", "border-20240916.json", "border-20241004.json", "border-20250602.json"],
    "method-retest": ["scenes/results.json", "pulse/interpretation.json", "pulse/surface-check.json", "next-measurement.json"],
    "statements": ["sound.json"],
}
PRIVATE = re.compile(r"/Users/|/private/|/tmp/|thread-storage|thr_[a-z0-9]|localhost|127\.0\.0\.1|\.miras/|data_sources/obsidian|@improvado\.io|file://|\.bb/",re.I)

def clean(value):
    if isinstance(value, dict):
        return {k:clean(v) for k,v in value.items() if k.lower() not in {"session","session_id","session_uuid","thread","thread_id"}}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence_folder',type=Path)
    source=parser.parse_args().evidence_folder
    for family,files in REPORTS.items():
        for name in files:
            data=(source/family/name).read_text()
            if name.endswith('.json'):
                data=json.dumps(clean(json.loads(data)),ensure_ascii=False,indent=2)+'\n'
            if PRIVATE.search(data):
                raise ValueError(f"Review required: {family}/{name}")
            destination=ROOT/'data/evidence'/family/name
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_text(data)

if __name__=='__main__':
    main()
