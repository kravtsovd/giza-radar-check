"""Compile the public project index and its linked evidence graph from reviewed records."""
import argparse
import base64
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote, urljoin

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = 'https://dkravt.ai/giza-radar-check/'
PAGES = 'https://kravtsovd.github.io/giza-radar-check/'
REPO = 'https://github.com/kravtsovd/giza-radar-check/'
def load(name):
    return json.loads((ROOT/'data'/f'{name}.json').read_text())
def dump(data):
    return json.dumps(data,ensure_ascii=False,separators=(',',':'))
def record(page,key):
    return CANONICAL+'#'+page+'/'+quote(key,safe='')
def ref(iri):
    return {'@id':iri}
def unique(items):
    ids=[x['id'] for x in items]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate identifiers: '+str([x for x in set(ids) if ids.count(x)>1]))
    return set(ids)
def public_files(names_from=None):
    # A private file sitting beside a public checkout must never enter the public index.
    raw = (names_from.read_bytes() if names_from else
           subprocess.check_output(['git','ls-files','--cached','-z'],cwd=ROOT))
    names={p.decode() for p in raw.split(b'\0') if p and not any(x.startswith('.') or x=='__pycache__' for x in Path(p.decode()).parts)}
    names.update(['data/ontology.json','index.html'])
    return [{'path':p} for p in sorted(names)]
def graph(snapshot):
    research=snapshot['research']; datasets=snapshot['datasets']['items']; library=snapshot['library']['items']
    ds=unique(datasets); stages=unique(research['stages']);unique(research['tests']);unique(library)
    evidence={e['id']:e for e in research['independent_evidence']}
    nodes=[{'@id':CANONICAL,'@type':'ResearchProject','name':'Giza Radar Check','url':CANONICAL,'identifier':'add4fed0-03eb-4a3e-ab7d-061eb69ad14d','subjectOf':ref(PAGES+'data/ontology.json'),'mainEntityOfPage':ref(CANONICAL)}]
    def add(page,r,kind,extra=None):
        n={'@id':record(page,r['id']),'@type':kind,'name':r['title'],'isPartOf':ref(CANONICAL)}
        if r.get('url'):n['url']=urljoin(PAGES,r['url'])
        if r.get('description'):n['description']=r['description']
        n.update(extra or {});nodes.append(n)
    for r in datasets:
        props={'additionalType':r['group'],'conditionsOfAccess':r['access'],'measurementTechnique':r['product']}
        if r.get('date'):props['temporalCoverage']=r['date']
        if r.get('rights_url'):props['license']=r['rights_url']
        add('datasets',r,'Dataset',props)
    for r in library:add('library',r,'CreativeWork',{'genre':r['group'],'conditionsOfAccess':r['access']})
    for s in research['stages']:add('method',s,'HowToStep',{'text':s['known'],'description':s['unknown']})
    for t in research['tests']:
        unknown=set(t['scene_ids'])-ds|set(t['stage_ids'])-stages|set(t.get('evidence_ids',[]))-evidence.keys()
        if unknown:raise ValueError(f"Broken links in {t['id']}: {unknown}")
        base=record('tests',t['id'])
        citations=[ref(urljoin(PAGES,s)) for s in t.get('sources',[]) if isinstance(s,str)]
        inputs=[ref(record('datasets',x)) for x in t['scene_ids']]+[ref(evidence[x]['url']) for x in t.get('evidence_ids',[])]
        add('tests',t,'AssessAction',{'object':ref(base+'/claim'),'usesMethod':[ref(record('method',x)) for x in t['stage_ids']],'usesDataset':inputs,'result':ref(base+'/observation'),'supportsDecision':ref(base+'/decision')})
        nodes.extend([{'@id':base+'/claim','@type':'Claim','text':t['claim'],'citation':citations},
                      {'@id':base+'/observation','@type':'Observation','description':t['result'],'isBasedOn':inputs,'subjectOf':ref(base)},
                      {'@id':base+'/decision','@type':'CreativeWork','text':t['decision'],'isBasedOn':ref(base+'/observation'),'nextTest':t['next_test']}])
    for v in research['candidate_family']['variants']:
        nodes.append({'@id':record('method','variant-'+v['id']),'@type':'HowTo','name':v['id'],'isPartOf':ref(CANONICAL),'isBasedOn':ref(record('tests','six-scene-location')),'description':f"Pairing {v['pairing']}, geometry {v['geometry']}, wavelength {v['wavelength_m']} m, estimator {v['estimator']}."})
    for f in snapshot['files']:
        nodes.append({'@id':record('library','file-'+f['path']),'@type':'DigitalDocument','name':f['path'],'url':REPO+'blob/main/'+quote(f['path']),'isPartOf':ref(CANONICAL)})
    return {'@context':{'@vocab':'https://schema.org/','method':CANONICAL+'vocab/','usesMethod':{'@id':'method:usesMethod','@type':'@id'},'usesDataset':{'@id':'method:usesDataset','@type':'@id'},'supportsDecision':{'@id':'method:supportsDecision','@type':'@id'},'nextTest':'method:nextTest'},'@graph':nodes}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site-output',type=Path,help='Canonical website HTML destination')
    parser.add_argument('--files-from',type=Path,help='NUL-delimited git ls-files output for a checkout with external Git metadata')
    args=parser.parse_args()
    data={key:load(key) for key in ('research','datasets','library')}
    data.update(as_of=max(data[k].get('as_of','') for k in data),files=public_files(args.files_from))
    (ROOT/'data/ontology.json').write_text(dump(graph(data))+'\n')
    template=(ROOT/'tools/hub.html').read_text()
    cover=base64.b64encode((ROOT/'assets/plateau-crop.jpg').read_bytes()).decode('ascii')
    output=template.replace('__COVER__','data:image/jpeg;base64,'+cover).replace('__SNAPSHOT__',dump(data).replace('<','\\u003c')).replace('__APP__',(ROOT/'tools/hub.js').read_text())
    if re.search(r'(?:/Users/[^\s"<>]+|thread-storage|localhost|fileScope=vault|thr_[a-z0-9]{8,}|[\w.-]+@improvado\.io)',output,re.I):raise ValueError('Non-public reference in compiled index')
    if args.site_output:args.site_output.write_text(output)
    print(f"{len(data['library']['items'])} library records, {len(data['datasets']['items'])} datasets and access records, {len(data['research']['tests'])} tests, {len(data['files'])} repository files.")

if __name__=='__main__':
    main()
