"""Independent closed-output audit. No study execution or new seed/world.

Usage: python3 -B audit_saved.py CLOSED_RUN_DIR ROOT_ANALYSIS_JSON
Prints a receipt only; refuses an incomplete/error run.
"""
from collections import Counter, defaultdict
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
from types import SimpleNamespace

from independent_reproduce import reference_ledger, reference_interval, decision, close

N = 2000
LOOKS = (40,80,120,160,200)
METHOD_MAP = {'row_fixed':'row','row_peek':'row','context_fixed':'context',
              'context_peek':'context','context_adjusted':'context_adjusted',
              'integrity_adjusted':'integrity_adjusted'}
CONTRASTS = (('context_fixed','row_fixed'),('row_peek','row_fixed'),
             ('context_peek','context_fixed'),('context_adjusted','context_peek'),
             ('integrity_adjusted','context_adjusted'))
EVENTS = ('false_ship','false_hold','correct_ship','correct_hold','correct_decision','false_decision','inconclusive')
Z = 1.959963984540054


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path):
    with gzip.open(path,'rt') as source:
        for line in source:
            yield json.loads(line)


def reference_saved_prefix(ledger, saved):
    exposed = [(i,int(a),int(b)) for i,(a,b,copies) in enumerate(zip(ledger['a_bits'],ledger['b_bits'],ledger['b_multiplicity'])) for _ in range(int(copies))]
    checks = 0
    for t,record in zip(LOOKS,saved['looks']):
        prefix = [row for row in exposed if row[0] < t*5]
        groups, unique = defaultdict(list), {}
        for pair,a,b in prefix:
            groups[pair//5].append(b-a)
            unique[pair] = (a,b)
        context = [statistics.fmean(v) for _,v in sorted(groups.items())]
        expected = {'row':reference_interval([b-a for _,a,b in prefix]),
                    'context':reference_interval(context),
                    'context_adjusted':reference_interval(context,True)}
        if len(unique) < t*5:
            expected['integrity_adjusted'] = dict(n=len(groups),mean=None,lower=None,upper=None,reason='integrity_missing_pairs')
        else:
            cleaned = defaultdict(list)
            for pair,(a,b) in unique.items():
                cleaned[pair//5].append(b-a)
            expected['integrity_adjusted'] = reference_interval([statistics.fmean(v) for _,v in sorted(cleaned.items())],True)
        for name,interval in expected.items():
            for key,value in interval.items():
                close(record['intervals'][name][key],value)
            assert record['decisions'][name] == decision(interval)
            checks += 1
    return checks


def indicators(action, delta):
    good = delta > .02
    return dict(false_ship=int(action=='ship' and not good),
                false_hold=int(action=='hold' and good),
                correct_ship=int(action=='ship' and good),
                correct_hold=int(action=='hold' and not good),
                correct_decision=int((action=='ship' and good) or (action=='hold' and not good)),
                false_decision=int((action=='ship' and not good) or (action=='hold' and good)),
                inconclusive=int(action=='inconclusive'))


def audit(run, analysis_path):
    base = Path(__file__).resolve().parent
    run, analysis_path = Path(run),Path(analysis_path)
    assert (run/'execution.json').is_file() and not (run/'error.json').exists(), 'run not closed successfully'
    freeze = json.loads((base/'SOURCE-FREEZE.json').read_text())
    for name,expected in freeze['files'].items():
        assert sha(base/name) == expected,name
    execution = json.loads((run/'execution.json').read_text())
    for name,expected in execution['files'].items():
        assert sha(run/name) == expected,name
    assert execution['completed_cohorts'] == execution['planned_cohorts'] == 30000
    manifest = json.loads((run/'manifest.json').read_text())
    original = json.loads((run/'summary.json').read_text())
    analysis = json.loads(analysis_path.read_text())
    assert manifest['protocol_sha256'] == freeze['files']['PROTOCOL.md']
    assert manifest['simulation_sha256'] == freeze['files']['simulation.py']
    assert manifest['cohorts_per_world'] == N and manifest['looks'] == list(LOOKS)
    assert tuple(manifest['methods']) == tuple(METHOD_MAP)
    specs = {f"w{x['index']:02d}_{x['mechanism']}":x for x in manifest['worlds']}
    assert len(specs)==15
    for index,spec in enumerate(specs.values()):
        assert spec['seed']==2709271800+index and spec['delta']==(-.04,.02,.10)[index%3]
        assert (spec['h'],spec['m'],spec['horizon'])==(0 if index<3 else .3,5,200)
    methods = tuple(METHOD_MAP)+('forced_row_fixed',)
    counts = {w:{m:Counter() for m in methods} for w in specs}
    consumption = {w:{m:Counter() for m in methods} for w in specs}
    paired = {w:{f'{a}-minus-{b}':{event:[0,0] for event in ('false_decision','correct_decision','inconclusive')} for a,b in CONTRASTS} for w in specs}
    ledger_seen, selected = set(), {}
    rngs = {w:random.Random(s['seed']) for w,s in specs.items()}
    prefix_count=interval_checks=decision_count=0
    for ledger in rows(run/'ledger.jsonl.gz'):
        w,i=ledger['world_id'],ledger['cohort_index']
        assert w in specs and 0<=i<N and (w,i) not in ledger_seen
        ledger_seen.add((w,i))
        assert (ledger['horizon'],ledger['m'])==(200,5)
        for field,alphabet,size in (('a_bits','01',1000),('b_bits','01',1000),('b_observed','01',1000),('b_multiplicity','012',1000),('context_signs','-+',200),('shared_bits','01',200)):
            assert len(ledger[field])==size and not set(ledger[field])-set(alphabet)
        if i<2:
            assert i==sum(key[0]==w for key in selected)
            ref=reference_ledger(SimpleNamespace(**specs[w]),i,rngs[w])
            for key,value in ref.items(): assert ledger[key]==value,(w,i,key)
            selected[(w,i)]=ledger
            prefix_count+=1
    assert len(ledger_seen)==30000 and prefix_count==30
    seen=set()
    for saved in rows(run/'decisions.jsonl.gz'):
        w,i=saved['world_id'],saved['cohort_index']
        assert (w,i) in ledger_seen and (w,i) not in seen
        seen.add((w,i))
        assert [look['intended_contexts'] for look in saved['looks']]==list(LOOKS)
        assert set(saved['methods'])==set(METHOD_MAP)
        for look in saved['looks']:
            for name,interval in look['intervals'].items():
                assert look['decisions'][name]==decision(interval)
        if i<2: interval_checks+=reference_saved_prefix(selected[(w,i)],saved)
        vectors={}
        for method,name in METHOD_MAP.items():
            eligible = saved['looks'][-1:] if method.endswith('_fixed') else saved['looks']
            chosen = next((look for look in eligible if decision(look['intervals'][name])!='inconclusive'),None)
            expected = decision(chosen['intervals'][name]) if chosen else 'inconclusive'
            used = chosen['intended_contexts'] if chosen else 200
            record=saved['methods'][method]
            assert (record['decision'],record['decision_contexts'])==(expected,used)
            assert record['interval']==(chosen or saved['looks'][-1])['intervals'][name]
            vectors[method]=indicators(expected,specs[w]['delta'])
            counts[w][method].update(vectors[method]); counts[w][method]['cohorts']+=1
            counts[w][method]['contexts_consumed']+=used
            consumption[w][method][str(used)]+=1
            if expected=='inconclusive':
                counts[w][method]['integrity_inconclusive' if record['reason'].startswith('integrity_') else 'statistical_inconclusive']+=1
        action=saved['methods']['row_fixed']['decision']
        forced='hold' if action=='inconclusive' else action
        assert saved['forced_row_fixed']==forced
        vectors['forced_row_fixed']=indicators(forced,specs[w]['delta'])
        counts[w]['forced_row_fixed'].update(vectors['forced_row_fixed']); counts[w]['forced_row_fixed']['cohorts']+=1
        counts[w]['forced_row_fixed']['contexts_consumed']+=200
        consumption[w]['forced_row_fixed']['200']+=1
        for a,b in CONTRASTS:
            for event,acc in paired[w][f'{a}-minus-{b}'].items():
                difference=vectors[a][event]-vectors[b][event]
                acc[0]+=difference; acc[1]+=difference*difference
        decision_count+=1
    assert seen==ledger_seen and decision_count==30000 and interval_checks==600
    assert len(analysis['worlds'])==15 and {world['world_id'] for world in analysis['worlds']}==set(specs)
    for world in analysis['worlds']:
        w=world['world_id']
        for method,count in counts[w].items():
            reported=world['methods'][method]
            for key in set(count)|set(reported['counts']): assert count[key]==reported['counts'].get(key,0),(w,method,key)
            assert sum(count[e] for e in ('false_ship','false_hold','correct_ship','correct_hold','inconclusive'))==N
            for event in ('false_ship','false_hold','correct_ship','correct_hold','inconclusive'):
                assert count[event]==original['counts'][w][method].get(event,0)
            close(reported['mean_contexts_consumed'],count['contexts_consumed']/N)
            assert reported['context_consumption_distribution']==dict(consumption[w][method])
            for event in EVENTS+('integrity_inconclusive','statistical_inconclusive'):
                k=count[event]; p=k/N; z2=Z*Z
                center=(k+z2/2)/(N+z2)
                half=Z*math.sqrt(N*p*(1-p)+z2/4)/(N+z2)
                interval=[0 if k==0 else center-half,1 if k==N else center+half]
                close(reported['rates'][event]['estimate'],p)
                for actual,expected in zip(reported['rates'][event]['wilson95'],interval): close(actual,expected)
        for contrast,events in paired[w].items():
            for event,(total,squares) in events.items():
                mean=float(Fraction(total,N))
                variance=Fraction(squares*N-total*total,N*(N-1))
                half=Z*math.sqrt(float(variance)/N) if variance else math.sqrt(2*math.log(40)/N)
                target=world['paired_contrasts'][contrast][event]
                close(target['difference'],mean)
                for actual,expected in zip(target['interval95'],(max(-1,mean-half),min(1,mean+half))): close(actual,expected)
    return {'status':'passed','closed_cohorts':30000,'authorized_prefix_cohorts':prefix_count,
            'prefix_interval_checks':interval_checks,'method_records_recounted':30000*7,
            'paired_contrast_intervals_checked':15*5*3,
            'source_freeze_sha256':sha(base/'SOURCE-FREEZE.json'),
            'run_execution_sha256':sha(run/'execution.json'),'analysis_sha256':sha(analysis_path),
            'audit_source_sha256':sha(__file__),'fresh_seeds_or_worlds':0,
            'limit':'Saved first-two/world math plus all-record decisions/counts; not a second full independent generator study or formal integrated Loop1.'}


if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('Usage: audit_saved.py CLOSED_RUN_DIR ROOT_ANALYSIS_JSON')
    print(json.dumps(audit(sys.argv[1],sys.argv[2]),indent=2))
