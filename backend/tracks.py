"""Validate the approved 30-track table independently of Figma readiness."""
import re
from collections import Counter
from .storage import read_json
from pathlib import Path

PAIRS = [
('Search','Menu+Button'),('Search','Menu+Status'),('Search','Button+Status'),
('Button','Menu+Status'),('Button','Menu+Search'),('Button','Status+Search'),
('Menu','Button+Status'),('Menu','Status+Search'),('Menu','Button+Search'),('Search','Menu+Button'),
('Search','Menu+Button'),('Search','Menu+Status'),('Search','Button+Status'),
('Status','Menu+Button'),('Status','Menu+Search'),('Status','Button+Search'),
('Button','Menu+Status'),('Button','Menu+Search'),('Button','Status+Search'),('Search','Menu+Button'),
('Search','Menu+Button'),('Search','Menu+Status'),('Search','Button+Status'),
('Status','Menu+Button'),('Status','Menu+Search'),('Status','Button+Search'),
('Menu','Button+Status'),('Menu','Status+Search'),('Menu','Button+Search'),('Search','Menu+Button')]

def validate_tracks(registry=None):
    if registry is None:
        registry=read_json(Path(__file__).resolve().parents[1]/'config/tracks.json')
    errors=[]; tracks=registry.get('tracks',[]); signatures=[]
    if len(tracks)!=30: errors.append('Exactly 30 tracks required')
    if [t.get('track_id') for t in tracks]!=[f'T{i:02d}' for i in range(1,31)]: errors.append('Track IDs/order must be T01..T30')
    if Counter(t.get('group') for t in tracks)!=Counter({'A':10,'B':10,'C':10}): errors.append('Groups must contain ten tracks each')
    for i,t in enumerate(tracks[:30]):
        tid=t.get('track_id'); rounds=t.get('rounds',[])
        if [r.get('test_index') for r in rounds]!=[0,1,2,3] or [r.get('family') for r in rounds]!=['baseline','GB','GG','BB']:
            errors.append(f'{tid}: expected Baseline/GB/GG/BB');continue
        group=i//10; bad=['Status','Menu','Button'][group]
        bb=[['Button','Menu'],['Button','Status'],['Menu','Status']][group]
        good,gg=PAIRS[i]
        expected=[{(good,'Good'),(bad,'Bad')},{(c,'Good') for c in gg.split('+')},{(c,'Bad') for c in bb}]
        parsed=[re.findall(r'(Button|Menu|Search|Status)\((Good|Bad)\)',r.get('variant_label','')) for r in rounds[1:]]
        if [set(p) for p in parsed]!=expected or any(len(p)!=2 for p in parsed): errors.append(f'{tid}: differs from approved table')
        flat=[v for p in parsed for v in p]
        if len(flat)!=len(set(flat)): errors.append(f'{tid}: repeated component-state')
        if t.get('group')!='ABC'[group]: errors.append(f'{tid}: wrong group')
        signatures.append(tuple(tuple(sorted(p)) for p in parsed))
        if rounds[0].get('variant_id')!='baseline': errors.append(f'{tid}: baseline must be shared')
    if len(signatures)==30:
        for duplicate,original in [(9,0),(19,10),(29,20)]:
            if signatures[duplicate]!=signatures[original]:errors.append('Intentional duplicate mismatch')
        if len(set(signatures))!=27:errors.append('Exactly 27 unique configurations required')
    return {'valid':not errors,'errors':errors,'track_count':len(tracks),'unique_configurations':len(set(signatures))}
