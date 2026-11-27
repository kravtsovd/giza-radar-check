"""Rebuild the public source index, offline, from data/library-sources.json."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'data' / 'library-sources.json'
OUTPUT = ROOT / 'data' / 'library.json'
SCOPE = ('This is the project’s named source set as of the date shown. It covers 72 video entries, including repeats, commentary and one unavailable playlist position. '
         'The audit screened 62 English or Italian caption tracks for technical terms, covering 106,452 cues. One additional recording has a separate publisher transcript. '
         'Eight other videos have metadata only. The 50 statements are attributed paraphrases with source clocks or document locations. '
         'Twelve written source records and seven pinned repositories were reviewed, alongside named articles, measurements, films and code archives. '
         'Book listings cover publisher information only. Source availability and scientific confirmation are separate questions.')


def playback_id(url):
    parsed = urlparse(url)
    if parsed.hostname == 'youtu.be':
        return parsed.path.strip('/')
    if parsed.hostname in {'www.youtube.com', 'youtube.com'}:
        return parse_qs(parsed.query).get('v', [''])[0]
    return ''


def clock(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f'{hours}:{minutes:02}:{seconds:02}'
    return f'{minutes}:{seconds:02}'


def recording(row):
    key = 'video-' + row['id']
    if row['coverage'] == 'unavailable':
        return dict(id=key, group='Recorded sources', title='Unavailable playlist entry', access='Unavailable',
                    description='One position in the organizer’s playlist had no title or recoverable content.', related=['curator-playlist'])
    if row['coverage'] == 'captions':
        language = {'en-orig': 'English', 'it-orig': 'Italian'}[row['track']]
        text = f'{language} captions screened for technical terms.'
    elif row['coverage'] == 'publisher':
        text = 'The separate publisher transcript was screened.'
    else:
        text = 'Only programme metadata was available for this edition.'
    if row.get('source_character'):
        text += ' ' + row['source_character']
    prefix = ', '.join(filter(None, [row.get('publisher'), row.get('upload_date')]))
    out = dict(id=key, group='Recorded sources', title=row['title'], url='https://youtu.be/' + row['id'],
               access='Public recording', description=(prefix + '. ' if prefix else '') + text)
    if row.get('earlier_recording_or_preferred_edition'):
        out['related'] = ['video-' + row['earlier_recording_or_preferred_edition']]
    if row['coverage'] == 'publisher':
        out.setdefault('related', []).append('text-rss')
    return out


def statement(row, destinations):
    segment = re.fullmatch(r'(\d+)-(\d+) seconds', row['location'])
    loc = ' to '.join(clock(n) for n in segment.groups()) if segment else row['location']
    language = {'it': 'Italian', 'en': 'English'}[row['lang']]
    description = f"{row['speaker']}. {row['paraphrase']} {language}. {row['basis'].rstrip('.')}."
    source = row['url']
    item = dict(id=row['id'], group='Attributed statements', title=f"{row['title']} ({loc})", url=source,
                access='Source passage', description=description)
    parent = playback_id(source)
    if parent:
        item['related'] = ['video-' + parent]
    elif source in destinations:
        item['related'] = [destinations[source]]
    return item


def build(data):
    items = list(data['materials'])
    if Counter(x['coverage'] for x in data['recordings']) != {'captions': 62, 'publisher': 1, 'listing': 8, 'unavailable': 1}:
        raise ValueError('Update the scope and audit counts when the source set changes.')
    expected = {'S' + str(n).zfill(2) for n in range(1, 51)}
    if {s['id'] for s in data['statements']} != expected or len(data['repositories']) != 7:
        raise ValueError('Statement or repository source set changed. Review the scope.')
    items.extend(map(recording, data['recordings']))
    destinations = {v['url']: v['id'] for v in items if 'url' in v}
    items.extend(statement(v, destinations) for v in data['statements'])
    for repo in data['repositories']:
        name = repo['name']
        if not re.fullmatch(r'[0-9a-f]{40}', repo['rev']):
            raise ValueError('Expected a pinned commit for ' + name)
        items.append(dict(id='code-' + name.lower().replace('/', '-'), group='Code and model downloads',
                          title=name, url=f"https://github.com/{name}/tree/{repo['rev']}", access='Public source revision',
                          description=repo['scope'] + ' ' + repo['qualification']))
    ids = {i['id'] for i in items}
    if len(ids) != len(items):
        raise ValueError('Duplicate library ID')
    for i in items:
        unknown = set(i.get('related', [])) - ids
        if unknown:
            raise ValueError(f"Unknown source for {i['id']}: {unknown}")
        if 'url' in i:
            p = urlparse(i['url'])
            if p.scheme != 'https' or not p.hostname or p.hostname in {'localhost', 'drive.google.com', 'docs.google.com'} or p.username or p.password:
                raise ValueError('Only public HTTPS source links belong here: ' + i['id'])
    return dict(as_of=data['as_of'], scope=SCOPE, items=items)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify the checked-in output without writing.')
    args = parser.parse_args()
    data = build(json.loads(SOURCES.read_text(encoding='utf-8')))
    rendered = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if OUTPUT.read_text(encoding='utf-8') != rendered:
            raise SystemExit('The library is stale. Run the builder.')
    else:
        OUTPUT.write_text(rendered, encoding='utf-8')
    print(f"Validated {len(data['items'])} public catalogue records.")


if __name__ == '__main__':
    main()
