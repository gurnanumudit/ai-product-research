"""Verify saved Part 2 results offline. No model calls and no file writes."""
from pathlib import Path
import collections
import hashlib
import json
import math
import statistics as st
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent/'code'))
from game import CONTRACTS, gains
from mirror import mirror
from analysis_contract import summarize
from subgroup_uncertainty import compute
ROOT=Path(__file__).resolve().parent

def load(name): return json.loads((ROOT/name).read_text())
def equal(actual,expected,label='value'):
    if isinstance(expected,dict):
        assert actual.keys()==expected.keys(),label
        for k in expected:equal(actual[k],expected[k],label+'.'+k)
    elif isinstance(expected,list):
        assert len(actual)==len(expected),label
        for a,b in zip(actual,expected):equal(a,b,label)
    elif isinstance(expected,(float,int)) and not isinstance(expected,bool):
        assert math.isclose(actual,expected,rel_tol=1e-11,abs_tol=1e-11),(label,actual,expected)
    else: assert actual==expected,(label,actual,expected)

def dist(xs):
    return dict(n=len(xs),mean=st.mean(xs) if xs else None,median=st.median(xs) if xs else None,min=min(xs) if xs else None,max=max(xs) if xs else None,frequency=dict(sorted(collections.Counter(xs).items())))
def summary(rows):
    obs=[r for r in rows if r['outcome'] is not None];out=[r['outcome'] for r in obs];n=len(obs)
    h=sum(o['any_deal'] and (o['buyer_harm'] or o['seller_harm']) for o in out);deals=sum(o['any_deal'] for o in out)
    return dict(assigned=len(rows),completed=n,unknown=len(rows)-n,observed_only_not_primary=True,agreements=deals,agreement_rate_among_completed=deals/n if n else None,harmful_agreements=h,harmful_agreement_rate_among_completed=h/n if n else None,harmful_agreement_rate_among_agreements=h/deals if deals else None,terminal_reasons=dict(collections.Counter(o['terminal_reason'] for o in out)),buyer_gain=dist([o['buyer_gain'] for o in out]),seller_gain=dist([o['seller_gain'] for o in out]),buyer_minus_seller_gap=dist([r['gap'] for r in obs]),slots=dist([o['slot_count'] for o in out]))
def canonical(x):return json.loads(json.dumps(x))

def main():
    if not __debug__:raise RuntimeError('Do not use -O: assertions are verification checks.')
    for name,expected in load('MANIFEST.json')['sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,('file hash',name)
    scenarios={s['scenario_id']:s for s in load('data/scenarios.json')};schedule=load('data/schedule.json');rows=load('data/outcomes.json')
    assert len(scenarios)==160 and len(schedule)==len(rows)==960
    assert [r['episode_id'] for r in rows]==[c['episode_id'] for c in schedule]
    assert len({r['episode_id'] for r in rows})==960
    for fid in sorted({s['family_id'] for s in scenarios.values()}):
        a=scenarios[fid+'-original'];b=scenarios[fid+'-mirror'];reflected=mirror(a)
        assert all(reflected[k]==b[k] for k in ['buyer','seller'])
        for i,c in enumerate(CONTRACTS):
            # Reversed price and all three complemented terms: C_i maps to C_(167-i).
            x=gains(a,c['contract_id']);y=gains(b,CONTRACTS[167-i]['contract_id'])
            assert (x['buyer_gain'],x['seller_gain'])==(y['seller_gain'],y['buyer_gain'])
    for row,cell in zip(rows,schedule):
        assert all(row[k]==cell[k] for k in ['episode_id','family_id','orientation','first_mover','repetition'])
        assert row['category']==cell['family_category']
        s=scenarios[cell['scenario_id']];menu=[gains(s,c['contract_id']) for c in CONTRACTS]
        gaps=[g['buyer_gain']-g['seller_gain'] for g in menu]+[0]
        assert (row['lo'],row['hi'])==(min(gaps),max(gaps))
        if row['status']!='completed':
            assert row['status']=='infrastructure_failure' and row['outcome'] is row['gap'] is row['executed_contract_id'] is None
            continue
        o=row['outcome'];cid=row['executed_contract_id'];g=gains(s,cid) if cid is not None else {'buyer_gain':0,'seller_gain':0}
        assert o['any_deal']==(cid is not None)==(o['terminal_reason']=='agreement')
        assert all(o[k]==g[k] for k in ['buyer_gain','seller_gain'])
        assert o['buyer_harm']==(g['buyer_gain']<0) and o['seller_harm']==(g['seller_gain']<0)
        assert row['gap']==g['buyer_gain']-g['seller_gain']
    assert sum(r['status']=='completed' for r in rows)==951
    equal(summarize(rows),load('reference/primary.json'),'primary')
    assert summarize(rows)['primary'] is None
    secondary=load('reference/secondary.json')
    equal(canonical(summary(rows)),secondary['all_outcomes'],'all outcomes')
    for name,keys in [('category_summary',['category']),('category_start_summary',['category','first_mover']),('orientation_summary',['orientation']),('category_orientation_start_summary',['category','orientation','first_mover'])]:
        for expected in secondary[name]:
            rs=[r for r in rows if all(r[k]==expected[k] for k in keys)]
            actual={**{k:expected[k] for k in keys},**summary(rs)}
            equal(canonical(actual),expected,name)
    rng=np.random.Generator(np.random.PCG64(2026110401));uncertainty=load('reference/uncertainty-data.json')
    for cat in ['tradeoffs','narrow_zone']:
        draws=rng.integers(0,30,size=(20000,30))
        for starter in ['buyer','seller']:
            subset=[r for r in rows if r['category']==cat and r['first_mover']==starter]
            mean,ci,fams=compute(subset,draws);ref=next(c for c in uncertainty['cells'] if c['id']==cat+'-'+starter)
            equal(mean,ref['mean_gap'],'completed mean');equal(ci,ref['ci95_completed_cluster_bootstrap'],'bootstrap CI');equal(fams,ref['families'])
            known=[r for r in subset if r['gap'] is not None];missing=[r for r in subset if r['gap'] is None]
            bounds=[(sum(r['gap'] for r in known)+sum(r[k] for r in missing))/len(subset) for k in ['lo','hi']]
            equal(bounds,ref['full_schedule_sample_legal_bounds'])
    for ref in load('reference/distribution-data.json')['cells']:
        subset=[r for r in rows if r['category']==ref['category'] and r['first_mover']==ref['starter']];known=[r for r in subset if r['gap'] is not None]
        assert (len(subset),len(known),len(subset)-len(known))==(ref['assigned'],ref['completed'],ref['unknown'])
        freq=[dict(gap=k,count=v) for k,v in sorted(collections.Counter(r['gap'] for r in known).items())];equal(freq,ref['frequency'])
        equal(st.mean(r['gap'] for r in known),ref['mean_gap'])
        byid={r['episode_id']:r for r in known}
        for public in ref['outcomes']:
            r=byid[public['episode_id']]
            for key,value in public.items():equal(r.get(key,r['outcome'].get(key)),value,'individual '+key)
        equal({name:sum(r['gap']>0 if name=='buyer_higher' else r['gap']<0 if name=='seller_higher' else r['gap']==0 for r in known) for name in ['buyer_higher','seller_higher','equal']},ref['comparison_counts'])
        assert ref['equal_walkaways']==sum(r['gap']==0 and r['outcome']['terminal_reason']=='walkaway' for r in known)
        assert ref['equal_agreements']==sum(r['gap']==0 and r['outcome']['terminal_reason']=='agreement' for r in known)
    print('PASS: file hashes; 80 exact mirrors across 13,440 contracts; all 960 assignments, 951 scored outcomes and 9 unknowns; primary bounds/suppression; all published secondary cells; four 20,000-draw family-bootstrap intervals; all six distributions and individual gains.')
    print('Offline numerical reproduction only. No model calls, collection replay or billing audit.')
if __name__=='__main__':main()
