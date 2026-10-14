"""Review only: independently reproduce the authorized first 2 cohorts/world.

No fresh seed or world; no study runner, files, network or outcome-rate reporting.
"""

from collections import defaultdict
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

import simulation as prod


def reference_ledger(world, index, rng):
    a, b, signs, shared = [], [], [], []
    delta, h = F(str(world.delta)), F(str(world.h))
    for _ in range(200):
        c = (-1,1)[rng.random() >= .5]
        z = int(rng.random() < .5)
        signs.append('+' if c == 1 else '-')
        shared.append(str(z))
        minus = float((F(1,2)-delta-h*c)/2)
        zero_end = float((F(1,2)-delta-h*c)/2+F(1,2))
        for _ in range(5):
            u = rng.random()
            if u < minus:
                av, bv = 1, 0
            elif u < zero_end:
                av, bv = z, z
            else:
                av, bv = 0, 1
            a.append(str(av)); b.append(str(bv))
    masks, copies = [], []
    for bv in b:
        u = rng.random()
        cutoff = .2 if world.mechanism == 'clustered_mcar' else (.4 if bv == '0' else .05) if world.mechanism == 'clustered_mnar' else 0
        seen = u >= cutoff
        masks.append(str(int(seen)))
        copies.append('0' if not seen else '2' if world.mechanism == 'clustered_duplicate' and bv == '1' else '1')
    return dict(a_bits=''.join(a),b_bits=''.join(b),b_observed=''.join(masks),
                b_multiplicity=''.join(copies),context_signs=''.join(signs),shared_bits=''.join(shared))


def reference_interval(values, adjusted=False):
    n = len(values)
    mean = statistics.fmean(values) if n else None
    if n < 2:
        return dict(n=n,mean=mean,lower=None,upper=None,reason='insufficient_n')
    if len(set(values)) == 1:
        return dict(n=n,mean=mean,lower=None,upper=None,reason='zero_sd')
    se = statistics.stdev(values)/math.sqrt(n)
    z = 2.5758293035489004 if adjusted else 1.959963984540054
    return dict(n=n,mean=mean,lower=mean-z*se,upper=mean+z*se,reason=None)


def decision(interval):
    if interval['reason']:
        return 'inconclusive'
    if interval['lower'] > .02:
        return 'ship'
    if interval['upper'] < .02:
        return 'hold'
    return 'inconclusive'


def close(actual, expected):
    if isinstance(expected,float):
        assert math.isclose(actual,expected,rel_tol=0,abs_tol=1e-12),(actual,expected)
    else:
        assert actual == expected,(actual,expected)


def check_prefixes():
    checks = 0
    mapping = {'row_fixed':'row','row_peek':'row','context_fixed':'context',
               'context_peek':'context','context_adjusted':'context_adjusted',
               'integrity_adjusted':'integrity_adjusted'}
    specs = prod.worlds()
    assert len(specs) == 15
    assert tuple(w.delta for w in specs) == (-.04,.02,.10)*5
    for i,world in enumerate(specs):
        assert world.seed == 2709271800+i
        assert world.h == (0 if i < 3 else .3)
        actual_rng = random.Random(world.seed)
        reference_rng = random.Random(world.seed)
        for cohort in range(2):
            ledger = prod.simulate_cohort(world,cohort,actual_rng)
            reference = reference_ledger(world,cohort,reference_rng)
            for key,value in reference.items():
                assert getattr(ledger,key) == value,key
            assert actual_rng.getstate() == reference_rng.getstate()
            rows = [(i,int(a),int(b),i//5) for i,(a,b,k) in enumerate(zip(reference['a_bits'],reference['b_bits'],reference['b_multiplicity'])) for _ in range(int(k))]
            assert tuple(rows) == prod.observed_rows(ledger)
            observed = prod.evaluate_cohort(prod.observed_rows(ledger))
            first = {}
            for t,record in zip((40,80,120,160,200),observed['looks']):
                prefix = [r for r in rows if r[3] < t]
                groups, unique = defaultdict(list), {}
                for pair,a,b,context_index in prefix:
                    groups[context_index].append(b-a)
                    unique[pair] = (a,b)
                context = [statistics.fmean(v) for _,v in sorted(groups.items())]
                refs = {'row':reference_interval([b-a for _,a,b,_ in prefix]),
                        'context':reference_interval(context),
                        'context_adjusted':reference_interval(context,True)}
                if len(unique) != t*5:
                    refs['integrity_adjusted'] = dict(n=len(groups),mean=None,lower=None,upper=None,reason='integrity_missing_pairs')
                else:
                    clean = defaultdict(list)
                    for pair,(a,b) in unique.items():
                        clean[pair//5].append(b-a)
                    refs['integrity_adjusted'] = reference_interval([statistics.fmean(v) for _,v in sorted(clean.items())],True)
                for name,ref in refs.items():
                    for key,value in ref.items():
                        close(record['intervals'][name][key],value)
                    assert record['decisions'][name] == decision(ref)
                    checks += 1
                diagnostic = record['diagnostics']
                assert diagnostic['missing_pairs'] == t*5-len(unique)
                assert diagnostic['duplicate_extra_rows'] == len(prefix)-len(unique)
                assert diagnostic['available_contexts'] == len(groups)
                for method,name in mapping.items():
                    action = decision(refs[name])
                    if method not in first and (not method.endswith('_fixed') or t == 200) and action != 'inconclusive':
                        first[method] = (action,t)
            for method in mapping:
                action,t = first.get(method,('inconclusive',200))
                assert observed['methods'][method]['decision'] == action
                assert observed['methods'][method]['decision_contexts'] == t
            terminal = first.get('row_fixed',('inconclusive',200))[0]
            assert observed['forced_row_fixed'] == ('hold' if terminal == 'inconclusive' else terminal)
    return {'worlds':15,'authorized_prefix_cohorts':30,'per_look_interval_checks':checks,
            'fresh_seeds':0,'simulation_sha256':hashlib.sha256(Path(prod.__file__).read_bytes()).hexdigest(),
            'independent_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    print(json.dumps(check_prefixes(),sort_keys=True))
