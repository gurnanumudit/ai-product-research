"""Pure functions extracted unchanged from the frozen study computation engine.
Copyright (c) 2026 Mudit Gurnani. MIT License; see LICENSE.
Original engine SHA256: 450f05468a03eb11763edbad4f3ba128737505c88522907bb57746807e3901e2
No collector, grading runner, canonical report entrypoint, or private custody code.
"""
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import math
import random

MODEL = 'openai/gpt-6-luna'
WORKFLOWS = ('A', 'S', 'R')
TOKENS = ('input', 'output', 'total', 'cached', 'cache_write', 'reasoning')
TIMES = ('logical_elapsed', 'physical_elapsed', 'receipt_wait', 'receipt_elapsed', 'grading_elapsed')
PRIMARY = ('coding:S-A', 'coding:R-S', 'planning:S-A', 'planning:R-S')
DRAWS, SEED = 20000, 20261111


def need(ok, why):
    if not ok: raise ValueError(why)


def integer(x):
    return type(x) is int and x >= 0


def measurement(x):
    return x is None or (type(x) in (int, float) and math.isfinite(x) and x >= 0)


def metric(values):
    values = list(values)
    need(all(measurement(x) for x in values), 'metric_nonnegative_or_null')
    known = sum(x for x in values if x is not None)
    missing = sum(x is None for x in values)
    return {'known_sum': known, 'missing': missing, 'complete_sum': None if missing else known, 'n': len(values)}


def quantile(values, probability):
    need(bool(values) and 0 <= probability <= 1, 'quantile_input')
    a = sorted(values); position = (len(a)-1)*probability; lo = math.floor(position); hi = math.ceil(position)
    return a[lo] + (a[hi]-a[lo])*(position-lo)


def exact_mcnemar(gains, regressions):
    need(integer(gains) and integer(regressions), 'discordant_counts')
    n = gains + regressions
    p = Fraction(1) if n == 0 else min(Fraction(1), Fraction(2*sum(math.comb(n,k) for k in range(min(gains,regressions)+1)),2**n))
    return {'two_sided_p': float(p), 'p_numerator': str(p.numerator), 'p_denominator': str(p.denominator), 'discordant': n}


def holm(tests):
    need(len(tests) == 4 and set(tests) == set(PRIMARY), 'exact_four_primary_tests')
    ps = {k: Fraction(int(v['p_numerator']), int(v['p_denominator'])) for k,v in tests.items()}
    order = sorted(ps, key=lambda k: (ps[k], PRIMARY.index(k)))
    adjusted = {}; previous = Fraction(0)
    for i,k in enumerate(order):
        previous = max(previous, min(Fraction(1), (4-i)*ps[k])); adjusted[k] = previous
    return {k: {'holm_adjusted_p': float(adjusted[k]), 'adjusted_numerator': str(adjusted[k].numerator),
                'adjusted_denominator': str(adjusted[k].denominator), 'reject_two_sided_at_0_05': adjusted[k] <= Fraction(1,20)} for k in PRIMARY}


def pair_table(families, baseline, followup):
    cells = Counter((r['endpoints'][baseline]['passed'],r['endpoints'][followup]['passed']) for r in families)
    gains, losses = cells[False,True], cells[True,False]
    return dict(n=len(families), both_pass=cells[True,True], both_fail=cells[False,False], gains=gains, regressions=losses,
                net=gains-losses, difference=(gains-losses)/len(families), **exact_mcnemar(gains,losses))


def paired_bootstrap(families, draws=DRAWS, seed=SEED):
    """Joint family draws retain all endpoints. Stable sorted IDs make input order irrelevant."""
    need(type(draws) is int and draws > 0 and type(seed) is int, 'bootstrap_parameters')
    pools = {s: sorted([r for r in families if ('coding' if r['domain']=='coding' else r['stratum']) == s],
                      key=lambda r:r['canonical_family_id']) for s in ('coding','graph_color','sokoban')}
    need(all(pools.values()), 'bootstrap_nonempty_strata')
    rng = random.Random(seed); samples = {k:[] for k in PRIMARY}; stream = hashlib.sha256()
    # Sample all endpoints together, compute both contrasts from the same drawn family.
    for _ in range(draws):
        counts = {'coding':[0,0,0], 'planning':[0,0,0]}
        for s,pool in pools.items():
            domain = 'coding' if s=='coding' else 'planning'
            for _ in pool:
                i = rng.randrange(len(pool)); stream.update(i.to_bytes(4,'big')); row = pool[i]
                for j,w in enumerate(WORKFLOWS): counts[domain][j] += row['endpoints'][w]['passed']
        for domain,n in [('coding',len(pools['coding'])),('planning',len(pools['graph_color'])+len(pools['sokoban']))]:
            a,s,r = counts[domain]
            samples[domain+':S-A'].append((s-a)/n); samples[domain+':R-S'].append((r-s)/n)
    return {'draws':draws,'seed':seed,'rng':'Python random.Random MT19937 randrange; runtime pinned',
            'resample_index_stream_sha256':stream.hexdigest(),'stratum_sizes':{k:len(v) for k,v in pools.items()},
            'interval_method':'pointwise95percent percentile, linear interpolation type7; not simultaneous',
            'intervals':{k:{'low':quantile(v,0.025),'high':quantile(v,0.975)} for k,v in samples.items()}}


def validate_tokens(t):
    need(isinstance(t,dict) and set(t)==set(TOKENS) and all(v is None or integer(v) for v in t.values()), 'usage_fields_null_or_integer')
    if all(t[k] is not None for k in ('input','output','total')): need(t['total']==t['input']+t['output'],'usage_total')
    if t['reasoning'] is not None and t['output'] is not None: need(t['reasoning']<=t['output'],'reasoning_subset')
    if all(t[k] is not None for k in ('input','cached','cache_write')): need(t['cached']+t['cache_write']<=t['input'],'input_subsets')


def rollup(rows, dimensions):
    groups=defaultdict(list)
    for r in rows: groups[tuple(r[k] for k in dimensions)].append(r)
    out=[]
    for keys,rs in sorted(groups.items()):
        out.append({**dict(zip(dimensions,keys)), 'rows':len(rs), 'logical_answers':sum(r.get('logical_answer',True) for r in rs),
                    'physical_requests':sum(r.get('constituent_calls',1) for r in rs),
                    'cost_nano_usd':metric(r['cost_nano_usd'] for r in rs),
                    'tokens':{k:metric(r['tokens'][k] for r in rs) for k in TOKENS},
                    'times_ms':{k:metric(r['times_ms'][k] for r in rs) for k in TIMES}})
    return out


def standalone_rows(families):
    out=[]
    def plus(values): return None if any(v is None for v in values) else sum(values)
    for f in families:
        for w in WORKFLOWS:
            rs=[f['endpoints'][x] for x in (('S','R') if w=='R' else (w,))]
            out.append({'model':MODEL,'domain':f['domain'],'stratum':f['stratum'],'workflow':w,'canonical_family_id':f['canonical_family_id'],
                        'constituent_calls':len(rs),'cost_nano_usd':plus([r['cost_nano_usd'] for r in rs]),
                        'tokens':{k:plus([r['tokens'][k] for r in rs]) for k in TOKENS},
                        'times_ms':{k:(rs[-1]['times_ms'][k] if k=='grading_elapsed' else plus([r['times_ms'][k] for r in rs])) for k in TIMES}})
    return out
