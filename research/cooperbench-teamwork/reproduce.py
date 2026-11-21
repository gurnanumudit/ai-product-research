"""Offline numerical replay from released derived outcomes. No network or model calls."""
import argparse
import collections
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from analysis import analyze, ARMS

ROOT = Path(__file__).resolve().parent

def read(name):
    return json.loads((ROOT / name).read_text())

def check(ok, reason):
    if not ok:
        raise ValueError(reason)

def verify_manifest():
    for name, digest in read('SHA256SUMS.json').items():
        check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, 'Hash mismatch: ' + name)

def validate_inputs(rows, schedule, missing, interrupted):
    check(len(schedule) == 333 and len(rows) == 327, '327 observed / 333 assigned required')
    slots = {r['key']: r for r in schedule}
    check(len(slots) == 333, 'Duplicate schedule key')
    lookup = {r['key']: r for r in rows}
    check(len(lookup) == len(rows), 'Duplicate outcome key')
    check(len(missing) == 6 and len(set(missing)) == 6, 'Six unique missing keys')
    check(set(lookup).isdisjoint(missing) and set(lookup) | set(missing) == set(slots), 'Observed/missing partition')
    check(collections.Counter(r['arm'] for r in schedule) == {a:111 for a in ARMS}, 'Assigned denominators')
    check(len({(r['repo'],r['task_id']) for r in schedule}) == 24, '24 underlying tasks')
    check(len({r['repo'] for r in schedule}) == 11, '11 repositories')
    pairs = {}
    for run in schedule:
        check(run['key'] == f"t{run['ti']:02d}-r{run['rep']}-{run['arm']}", 'Schedule key identity')
        check(run['rep'] in range(3) and run['arm'] in ARMS, 'Assignment domain')
        meta = {k:run[k] for k in ['repo','task_id','features','previously_run_base']}
        if run['ti'] in pairs:
            check(pairs[run['ti']] == meta, 'Pair metadata consistency')
        pairs[run['ti']] = meta
    check(len(pairs) == 37, '37 feature pairs')
    for row in rows:
        check(row['key'] in slots, 'Unassigned result')
        check(all(row[k] == v for k,v in slots[row['key']].items()), 'Assignment metadata changed')
        for phase in row['phases'].values():
            check(all(isinstance(v,(int,float)) and math.isfinite(v) and v >= 0 for v in phase.values()), 'Invalid phase value')
        check(sum(p['messages'] for p in row['phases'].values()) == row['messages'], 'Saved messages')
        check(sum(p['messages_delivered'] for p in row['phases'].values()) == row['messages_delivered'], 'Delivered messages')
    check(sum(r['calls'] for r in rows) + sum(x['settled_calls'] for x in interrupted.values()) == 9783, 'Settled-call conservation')
    check(sum(x['unknown_requests'] for x in interrupted.values()) == 1, 'One unresolved same-study request')
    check(sum(round(r['api_usd']*1e9) for r in rows) + sum(x['settled_nano_usd'] for x in interrupted.values()) == 5250162005, 'Known API nano-USD conservation')
    return pairs

def compare(actual, expected, path='analysis'):
    if isinstance(expected,dict):
        check(isinstance(actual,dict) and actual.keys() == expected.keys(), path+' keys')
        for key in expected: compare(actual[key],expected[key],path+'.'+key)
    elif isinstance(expected,list):
        check(isinstance(actual,list) and len(actual)==len(expected),path+' length')
        for i,(a,b) in enumerate(zip(actual,expected)): compare(a,b,path+f'[{i}]')
    elif isinstance(expected,float):
        check(isinstance(actual,(int,float)) and math.isclose(actual,expected,rel_tol=1e-11,abs_tol=1e-9),path+' numerical mismatch')
    else:
        check(type(actual)==type(expected) and actual==expected,path+' mismatch')

def independent_fraction_bounds(rows,schedule):
    """Separate rational-arithmetic check, independent of analysis.weighted_summary."""
    observed={r['key']:r['both'] for r in rows}
    answer={}
    for arm in ARMS:
        bybase=collections.defaultdict(lambda:collections.defaultdict(list))
        for r in schedule:
            if r['arm']==arm:bybase[(r['repo'],r['task_id'])][r['ti']].append(r['key'])
        endpoints=[]
        for fill in [0,1]:
            base_means=[]
            for pairs in bybase.values():
                pair_means=[sum(Fraction(observed.get(k,fill)) for k in keys)/len(keys) for keys in pairs.values()]
                base_means.append(sum(pair_means)/len(pair_means))
            endpoints.append(sum(base_means)/len(base_means))
        answer[arm]=endpoints
    check(answer == {'SOLO':[Fraction(19,36),Fraction(77,144)],'SIMPLE':[Fraction(5,16),Fraction(49,144)],'STRUCTURED':[Fraction(23,48),Fraction(71,144)]},'Independent rational bounds')
    return answer

def reproduce():
    verify_manifest()
    rows,schedule,missing,costs = [read('data/'+n+'.json') for n in ['outcomes','schedule','missing-keys','interrupted-costs']]
    pairs=validate_inputs(rows,schedule,missing,costs)
    result=analyze(rows,pairs,interrupted_costs=costs)
    # JSON normalizes the historical None dictionary key to "null".
    result=json.loads(json.dumps(result))
    compare(result,read('reference/analysis.json'))
    independent_fraction_bounds(rows,schedule)
    check(result['resampling'] is None,'No sampling confidence claim')
    print('PASS: 333 assignments, 327 observed, six missing; every saved analysis field agrees.')
    print('Independent rational missing bounds and $5.250162005 known API conservation verified.')
    for arm,v in result['arms'].items():
        print(f"{arm}: {v['successes']}/{v['observed']} both pass; {v['features']} feature credits; ${v['api_per_observed_success']:.6f} API per observed success")
    print('Numerical replay only: does not independently regrade software or verify provider invoices.')
    return result

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    reproduce()
