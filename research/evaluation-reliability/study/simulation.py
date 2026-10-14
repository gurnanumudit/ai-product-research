"""Phase 1 known-truth implementation. Importing this module never runs a study.

The lead must freeze the protocol/configuration and authorize execute_study.
Only the Python standard library is used. All confidence intervals are normal
approximations; look adjustment does not fix missingness or model assumptions.
"""

from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from fractions import Fraction
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import random
import resource
from statistics import NormalDist
import time
import sys
from typing import NamedTuple


MECHANISMS = ('clean_iid', 'clustered_complete', 'clustered_mcar', 'clustered_mnar', 'clustered_duplicate')
EFFECTS = (-.04, .02, .10)
METHODS = ('row_fixed', 'row_peek', 'context_fixed', 'context_peek',
           'context_adjusted', 'integrity_adjusted')
LOOKS = (40, 80, 120, 160, 200)
ALPHA = .05
TAU = .02


def _fraction(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise ValueError(f'{name} must be a finite real number, not bool')
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f'{name} must be finite')
    return value if isinstance(value, Fraction) else Fraction(str(value))


def _positive_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f'{name} must be a positive integer, not bool')


@dataclass(frozen=True)
class World:
    index: int
    mechanism: str
    delta: float
    h: float
    seed: int
    q: float = .5
    m: int = 5
    horizon: int = 200

    def __post_init__(self):
        if isinstance(self.index, bool) or not isinstance(self.index, int) or self.index < 0:
            raise ValueError('world index must be a nonnegative integer')
        if self.mechanism not in MECHANISMS:
            raise ValueError('unknown observation mechanism')
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ValueError('seed must be an integer')
        _positive_integer(self.m, 'm')
        _positive_integer(self.horizon, 'horizon')
        law(self.q, self.delta, self.h, self.m)

    @property
    def world_id(self):
        return f'w{self.index:02d}_{self.mechanism}'


def law(q, delta, h, m=5):
    """Exact decimal/Fraction population law; no Monte Carlo truth estimation."""
    q, d, h = (_fraction(v, n) for v, n in ((q,'q'),(delta,'delta'),(h,'h')))
    _positive_integer(m, 'm')
    if not 0 <= q <= 1 or h < 0 or abs(d-h) > q or abs(d+h) > q:
        raise ValueError('require q in [0,1], h>=0 and |delta +/- h|<=q')
    probabilities = {c: ((q-d-h*c)/2, 1-q, (q+d+h*c)/2) for c in (-1,1)}
    return {'probabilities': probabilities, 'mean_d': d, 'mean_D': d,
            'variance_d': q-d*d, 'covariance_d': h*h,
            'variance_D': (q-d*d+(m-1)*h*h)/m,
            'mean_a': (1-d)/2, 'mean_b': (1+d)/2}


def worlds(seed_base=2709271800):
    if isinstance(seed_base, bool) or not isinstance(seed_base, int):
        raise ValueError('seed_base must be an integer')
    result = []
    for mechanism in MECHANISMS:
        for delta in EFFECTS:
            index = len(result)
            result.append(World(index, mechanism, delta,
                                0. if mechanism == 'clean_iid' else .3,
                                seed_base+index))
    return tuple(result)


@dataclass(frozen=True)
class Ledger:
    world_id: str
    cohort_index: int
    horizon: int
    m: int
    a_bits: str
    b_bits: str
    b_observed: str
    b_multiplicity: str
    context_signs: str
    shared_bits: str

    def __post_init__(self):
        _positive_integer(self.horizon, 'horizon')
        _positive_integer(self.m, 'm')
        if isinstance(self.cohort_index, bool) or not isinstance(self.cohort_index, int) or self.cohort_index < 0:
            raise ValueError('cohort index must be nonnegative integer')
        size = self.horizon*self.m
        for name in ('a_bits','b_bits','b_observed'):
            value = getattr(self, name)
            if len(value) != size or set(value)-{'0','1'}:
                raise ValueError(f'invalid {name}')
        if len(self.b_multiplicity) != size or set(self.b_multiplicity)-{'0','1','2'}:
            raise ValueError('invalid multiplicity')
        if any((mask == '0') != (copies == '0') for mask,copies in zip(self.b_observed,self.b_multiplicity)):
            raise ValueError('mask and multiplicity disagree')
        if len(self.context_signs) != self.horizon or set(self.context_signs)-{'-','+'}:
            raise ValueError('invalid context signs')
        if len(self.shared_bits) != self.horizon or set(self.shared_bits)-{'0','1'}:
            raise ValueError('invalid shared bits')


class ObservedRow(NamedTuple):
    pair_id: int
    a: int
    b: int
    context_index: int


def simulate_cohort(world, cohort_index, rng, *, probability_table=None):
    """Truth first, then one B-observation uniform/original pair in every world.

    Frozen stream contract must be confirmed by the lead before random runs.
    Each context consumes C,Z,m difference draws, even degenerate probabilities.
    After all truth records, consume H*m mask draws even for clean/duplicate.
    """
    table = probability_table or law(world.q,world.delta,world.h,world.m)['probabilities']
    cuts = {c:(float(v[0]),float(v[0]+v[1])) for c,v in table.items()}
    a, b, signs, shared = [], [], [], []
    for _ in range(world.horizon):
        c = -1 if rng.random() < .5 else 1
        z = int(rng.random() < .5)
        signs.append('-' if c == -1 else '+')
        shared.append(str(z))
        minus_cut, zero_cut = cuts[c]
        for _ in range(world.m):
            u = rng.random()
            av,bv = (1,0) if u < minus_cut else (z,z) if u < zero_cut else (0,1)
            a.append(str(av)); b.append(str(bv))
    mask, copies = [], []
    for bv in b:
        u = rng.random()
        drop = .2 if world.mechanism == 'clustered_mcar' else (.4 if bv == '0' else .05) if world.mechanism == 'clustered_mnar' else 0.
        seen = u >= drop
        mask.append('1' if seen else '0')
        copies.append('0' if not seen else '2' if world.mechanism == 'clustered_duplicate' and bv == '1' else '1')
    return Ledger(world.world_id,cohort_index,world.horizon,world.m,
                  ''.join(a),''.join(b),''.join(mask),''.join(copies),''.join(signs),''.join(shared))


def observed_rows(ledger):
    """Only surviving paired records cross into the decision-method interface."""
    rows = []
    for pair_id,(a,b,mask,copies) in enumerate(zip(ledger.a_bits,ledger.b_bits,
                                                ledger.b_observed,ledger.b_multiplicity)):
        if mask == '1':
            rows.extend([ObservedRow(pair_id,int(a),int(b),pair_id//ledger.m)]*int(copies))
    return tuple(rows)


def deduplicate(rows, intended_pairs, m):
    """Use IDs/observed values only; return current-prefix diagnostics."""
    unique, conflicts, invalid = {}, set(), 0
    for row in rows:
        valid_id = (type(row.pair_id) is int and 0 <= row.pair_id < intended_pairs
                    and type(row.context_index) is int
                    and row.context_index == row.pair_id//m)
        valid_value = all(type(x) is int and x in (0,1) for x in (row.a,row.b))
        if not valid_id or not valid_value:
            invalid += 1
            continue
        values = (row.a,row.b)
        if row.pair_id in unique and unique[row.pair_id] != values:
            conflicts.add(row.pair_id)
        else:
            unique[row.pair_id] = values
    missing = intended_pairs-len(unique)
    reason = 'invalid_observed_row' if invalid else 'conflicting_duplicate' if conflicts else 'missing_pairs' if missing else None
    diagnostic = {'intended_pairs':intended_pairs,'observed_joined_rows':len(rows),
                  'unique_observed_pairs':len(unique),'missing_pairs':missing,
                  'duplicate_extra_rows':len(rows)-len(unique)-invalid,
                  'conflicting_ids':len(conflicts),'invalid_rows':invalid,
                  'integrity_reason':reason}
    return unique, diagnostic


def normal_interval(values, alpha=.05, looks_adjustment=1):
    """Two-sided normal approximation; insufficient/zero SD stays inconclusive."""
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('alpha must be in (0,1)')
    _positive_integer(looks_adjustment,'looks_adjustment')
    values = tuple(values)
    if any(not math.isfinite(x) or not -1 <= x <= 1 for x in values):
        raise ValueError('differences must be finite in [-1,1]')
    n = len(values)
    mean = math.fsum(values)/n if n else None
    result = {'n':n,'mean':mean,'sd':None,'se':None,'lower':None,'upper':None,
              'reason':'insufficient_n' if n < 2 else None}
    if n < 2:
        return result
    # Exact constant-input detection precedes floating mean/variance arithmetic.
    sd = 0. if max(values) == min(values) else math.sqrt(math.fsum((x-mean)**2 for x in values)/(n-1))
    result.update(sd=sd,se=sd/math.sqrt(n))
    if sd <= 0:
        result['reason'] = 'zero_sd'
        return result
    z = NormalDist().inv_cdf(1-alpha/(2*looks_adjustment))
    result.update(lower=mean-z*result['se'],upper=mean+z*result['se'])
    return result


def interval_decision(interval, tau=TAU):
    if not math.isfinite(tau) or not -1 <= tau <= 1:
        raise ValueError('tau must be finite in [-1,1]')
    if interval['reason'] is not None:
        return 'inconclusive'
    if interval['lower'] > tau:
        return 'ship'
    if interval['upper'] < tau:
        return 'hold'
    return 'inconclusive'


def evaluate_prefix(rows, intended_contexts, m=5, *, alpha=ALPHA, tau=TAU, k=5):
    """No latent truth, world effect or future records are accepted here."""
    _positive_integer(intended_contexts,'intended_contexts')
    _positive_integer(m,'m')
    unique, diagnostic = deduplicate(rows,intended_contexts*m,m)
    if diagnostic['invalid_rows']:
        # Current accrued invalid IDs cannot be silently filtered away or use
        # a future corruption flag. Unguarded intervals are unavailable here.
        valid_contexts = {row.context_index for row in rows
                          if type(row.context_index) is int and 0 <= row.context_index < intended_contexts}
        diagnostic.update(intended_contexts=intended_contexts,
                          available_contexts=len(valid_contexts),
                          zero_observation_contexts=intended_contexts-len(valid_contexts))
        intervals = {name:{'n':None,'mean':None,'sd':None,'se':None,'lower':None,'upper':None,
                           'reason':'integrity_invalid_observed_row' if name == 'integrity_adjusted'
                                    else 'invalid_observed_row'}
                     for name in ('row','context','context_adjusted','integrity_adjusted')}
        return {'intended_contexts':intended_contexts,'diagnostics':diagnostic,
                'intervals':intervals,'decisions':{name:'inconclusive' for name in intervals}}
    groups = defaultdict(list)
    for row in rows:
        groups[row.context_index].append(row.b-row.a)
    row_values = tuple(row.b-row.a for row in rows)
    context_values = tuple(math.fsum(group)/len(group) for _,group in sorted(groups.items()))
    diagnostic.update(intended_contexts=intended_contexts,available_contexts=len(groups),
                      zero_observation_contexts=intended_contexts-len(groups))
    intervals = {'row':normal_interval(row_values,alpha),
                 'context':normal_interval(context_values,alpha),
                 'context_adjusted':normal_interval(context_values,alpha,k)}
    if diagnostic['integrity_reason'] is None:
        cleaned = defaultdict(list)
        for pair_id,(a,b) in unique.items():
            cleaned[pair_id//m].append(b-a)
        clean_means = tuple(math.fsum(v)/len(v) for _,v in sorted(cleaned.items()))
        guarded = normal_interval(clean_means,alpha,k)
    else:
        guarded = {'n':len(groups),'mean':None,'sd':None,'se':None,'lower':None,
                   'upper':None,'reason':'integrity_'+diagnostic['integrity_reason']}
    intervals['integrity_adjusted'] = guarded
    return {'intended_contexts':intended_contexts,'diagnostics':diagnostic,
            'intervals':intervals,
            'decisions':{name:interval_decision(interval,tau) for name,interval in intervals.items()}}


def evaluate_cohort(rows, *, m=5, looks=LOOKS, tau=TAU, alpha=ALPHA):
    """Fixed methods decide at final look; repeated methods retain first crossing."""
    looks = tuple(looks)
    if not looks or any(type(t) is not int or t < 1 for t in looks) or tuple(sorted(set(looks))) != looks:
        raise ValueError('looks must be strictly increasing positive integers')
    rows = tuple(rows)
    # Accrual metadata is independent of pair identity. An unexpected pair ID
    # still appears at its observed context's look and reaches the guard.
    if any(type(row.context_index) is not int or not 0 <= row.context_index < looks[-1] for row in rows):
        raise ValueError('missing/invalid event accrual context')
    history, first = [], {}
    mappings = {'row_fixed':'row','row_peek':'row','context_fixed':'context',
                'context_peek':'context','context_adjusted':'context_adjusted',
                'integrity_adjusted':'integrity_adjusted'}
    for t in looks:
        prefix = tuple(row for row in rows if row.context_index < t)
        record = evaluate_prefix(prefix,t,m,alpha=alpha,tau=tau,k=len(looks))
        history.append(record)
        for method,name in mappings.items():
            eligible = not method.endswith('_fixed') or t == looks[-1]
            if eligible and method not in first and record['decisions'][name] != 'inconclusive':
                first[method] = {'decision':record['decisions'][name],'decision_contexts':t,
                                 'interval':record['intervals'][name],
                                 'diagnostics':record['diagnostics'],'reason':'boundary_crossing'}
    outcomes = {}
    for method,name in mappings.items():
        outcomes[method] = first.get(method,{
            'decision':'inconclusive','decision_contexts':looks[-1],
            'interval':history[-1]['intervals'][name],
            'diagnostics':history[-1]['diagnostics'],
            'reason':history[-1]['intervals'][name]['reason'] or 'interval_spans_threshold'})
    return {'methods':outcomes,'looks':history,
            'forced_row_fixed': 'hold' if outcomes['row_fixed']['decision'] == 'inconclusive' else outcomes['row_fixed']['decision']}


def classify(decision, true_delta, tau=TAU):
    """Reporting only; never called by a decision method."""
    if decision not in ('ship','hold','inconclusive'):
        raise ValueError('unknown decision')
    if decision == 'inconclusive':
        return decision
    worthwhile = true_delta > tau
    return ('correct_' if (decision == 'ship') == worthwhile else 'false_')+decision


def _json(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def _file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda:source.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


@contextmanager
def _gzip_text(path):
    """Fixed gzip header and UTF-8 newlines allow byte-for-byte full replay."""
    with Path(path).open('xb') as binary:
        with gzip.GzipFile(filename='',mode='wb',fileobj=binary,mtime=0) as compressed:
            with io.TextIOWrapper(compressed,encoding='utf-8',newline='\n') as text:
                yield text


def _resources():
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {'cpu_seconds':usage.ru_utime+usage.ru_stime,
            'peak_rss_bytes':usage.ru_maxrss*(1 if sys.platform == 'darwin' else 1024)}


def _enforce_limits(started, output):
    current = _resources()
    current['wall_seconds'] = time.perf_counter()-started
    current['retained_bytes'] = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
    if current['wall_seconds'] > 1200 or current['peak_rss_bytes'] > 1024**3 or current['retained_bytes'] > 2*1024**3-10*1024**2:
        raise RuntimeError('frozen wall/RSS/storage resource ceiling reached: '+_json(current))
    return current


def execute_study(output_dir, protocol_path, expected_protocol_sha256, *,
                  seed_base=2709271800, cohorts_per_world=2000):
    """Explicit lead-only entrypoint after independent review and freeze/GO.

    No CLI/default execution. Refuse existing output files, preserve all cohorts,
    and log/re-raise errors rather than silently replacing an unsuccessful run.
    """
    if type(cohorts_per_world) is not int or cohorts_per_world != 2000 or seed_base != 2709271800:
        raise ValueError('reporting execution requires the frozen 2000 cohorts/world and seed base')
    protocol = Path(protocol_path)
    actual_hash = _file_sha256(protocol)
    if actual_hash != expected_protocol_sha256:
        raise ValueError('protocol hash does not match frozen input')
    output = Path(output_dir)
    output.mkdir(parents=True,exist_ok=True)
    names = ('ledger.jsonl.gz','decisions.jsonl.gz','manifest.json','summary.json','execution.json','error.json')
    if any((output/name).exists() for name in names):
        raise FileExistsError('refusing to overwrite a prior execution')
    source_hash = _file_sha256(__file__)
    specs = worlds(seed_base)
    manifest = {'schema':'phase1-v1','protocol_path':str(protocol.resolve()),
                'protocol_sha256':actual_hash,'simulation_sha256':source_hash,
                'python':platform.python_version(),'rng':'random.Random: continuous per world',
                'worlds':[asdict(world) for world in specs],
                'cohorts_per_world':cohorts_per_world,'looks':LOOKS,'tau':TAU,'alpha':ALPHA,
                'methods':METHODS,'ledger_index':'pair_id=context_index*m+question_index, all zero-based',
                'resource_limits':{'wall_seconds':1200,'peak_rss_bytes':1024**3,'output_bytes':2*1024**3},
                'external_spend_usd':0,'timing_unit':'local monotonic wall seconds, not human active labor'}
    (output/'manifest.json').write_text(_json(manifest)+'\n')
    started = time.perf_counter()
    baseline = _resources()
    completed = 0
    counts = {}
    active_world_id, cohort_index = None, None
    try:
        with _gzip_text(output/'ledger.jsonl.gz') as raw, _gzip_text(output/'decisions.jsonl.gz') as decisions:
            for world in specs:
                active_world_id = world.world_id
                rng = random.Random(world.seed)
                table = law(world.q,world.delta,world.h,world.m)['probabilities']
                tally = {method:Counter() for method in METHODS+('forced_row_fixed',)}
                counts[world.world_id] = tally
                for cohort_index in range(cohorts_per_world):
                    _enforce_limits(started,output)
                    ledger = simulate_cohort(world,cohort_index,rng,probability_table=table)
                    raw.write(_json(asdict(ledger))+'\n')
                    result = evaluate_cohort(observed_rows(ledger),m=world.m)
                    result.update(world_id=world.world_id,cohort_index=cohort_index,
                                  true_delta=world.delta,
                                  truth_class='ship_worthy' if world.delta > TAU else 'hold_worthy')
                    decisions.write(_json(result)+'\n')
                    for method,record in result['methods'].items():
                        tally[method][classify(record['decision'],world.delta)] += 1
                    tally['forced_row_fixed'][classify(result['forced_row_fixed'],world.delta)] += 1
                    completed += 1
        (output/'summary.json').write_text(_json({'completed_cohorts':completed,
            'planned_cohorts':len(specs)*cohorts_per_world,'counts':counts})+'\n')
        _enforce_limits(started,output)
        hashes = {name:_file_sha256(output/name)
                  for name in ('ledger.jsonl.gz','decisions.jsonl.gz','manifest.json','summary.json')}
        resources = _enforce_limits(started,output)
        execution = {'completed_cohorts':completed,'planned_cohorts':len(specs)*cohorts_per_world,
                     'resources':resources,'cpu_seconds_delta':resources['cpu_seconds']-baseline['cpu_seconds'],
                     'baseline_resources':baseline,'external_spend_usd':0,'files':hashes}
        (output/'execution.json').write_text(_json(execution)+'\n')
        return execution
    except BaseException as exc:
        (output/'error.json').write_text(_json({'completed_cohorts':completed,
            'planned_cohorts':len(specs)*cohorts_per_world,
            'active_world_id':active_world_id,'active_cohort_index':cohort_index,
            'error_type':type(exc).__name__,'message':str(exc),
            'elapsed_seconds':time.perf_counter()-started})+'\n')
        raise
