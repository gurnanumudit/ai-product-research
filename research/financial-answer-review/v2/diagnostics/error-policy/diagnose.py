"""One offline frozen-taxonomy/fixed-policy diagnostic; no calls or source review."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
import time

INPUT_HASHES = {
    'audit': '41c3cbee07480e989f8dd5f14851d429bc1fde642d3a65b20b405c6a6a72f511',
    'summary': 'deb29d7e1ec5dddbac49922ac00f09777c6951d1db4aa174dba71c45cabebd6a',
    'neutral': 'f6e2ae3ea6931c234b7cffdccc3a1df88f89ab597995dfa0c9c4455e42c390b6',
}
CODE_HASHES = {
    'runner.py': '5c87e3bb85daeb353fc4e14cd55a929806fd88a43fc31e3a3f62996eeca74cae',
    'package/__init__.py': '17808b1afeb0c62ac94f368f20726b4788e9aaafe711709c3175674267622046',
    'package/schema.py': 'a1e4434659005443a05e5283fda30e9a878057184820841d6024f9ddcef434a3',
    'package/checker.py': 'e0d03cc1be408039b3b1c6163e81a10830969eb7d9bf4404d38bd7376212f901',
    'package/numbers.py': '1db53a55b346ad7f27a90e26f7458c251c70e26218ec61065e2f8573b7d3ea98',
}
CATEGORIES = ('arithmetic', 'metric_period_component_denominator',
              'precision_sign_source_interpretation', 'unit_scale')
EXPECTED_COUNTS = dict(zip(CATEGORIES, (70, 14, 14, 2)))
CELLS = ('both', 'B_only', 'confidence_only', 'neither')
AUDIT_SEED = 'finqa-test-error-audit-20261013'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def bound_read(path, expected, limit=5000000):
    with Path(path).open('rb') as handle:
        body = handle.read(limit + 1)
    require(len(body) <= limit and digest(body) == expected, 'Input hash/size mismatch: ' + str(path))
    return body


def save(path, obj):
    with Path(path).open('x') as handle:
        json.dump(obj, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        handle.write('\n')


def fresh(out, roots):
    out = Path(out).absolute()
    require(not out.exists() and not out.is_symlink() and not any(p.is_symlink() for p in out.parents),
            'Output must be fresh and not symlinked')
    require(not any(out.resolve().is_relative_to(Path(p).resolve()) for p in roots),
            'Output must be outside input archives')
    out.mkdir(parents=True, exist_ok=False)
    return out


def section(text, heading):
    marker = heading + '\n'
    require(text.count(marker) == 1, 'Missing/duplicate audit heading: ' + heading)
    body = text.split(marker, 1)[1]
    level = len(heading) - len(heading.lstrip('#'))
    return re.split(r'(?m)^#{1,' + str(level) + r'} ', body, maxsplit=1)[0]


def parse_taxonomy(text, expected_counts=EXPECTED_COUNTS):
    table = section(text, '### Known mismatch sample')
    sample = [(m[1].strip(), int(m[2])) for m in
              re.finditer(r'(?m)^\| ([^|\n]+/[^|\n]+) \| (\d+) \|\s*$', table)]
    require(len(sample) == sum(expected_counts.values()), 'Audit sample size mismatch')
    require(len({i for i, _ in sample}) == len(sample) == len({n for _, n in sample}), 'Duplicate audit ID/number')
    arithmetic = section(text, '### Arithmetic trace roster')
    lists = re.findall(r'`([\d,\s]+)`', arithmetic)
    require(len(lists) == 1, 'Ambiguous arithmetic roster')
    rosters = {'arithmetic': [int(x.strip()) for x in lists[0].split(',')]}
    for cat, heading in [('metric_period_component_denominator', '### Metric and component differences'),
                         ('precision_sign_source_interpretation', '### Precision sign and interpretation differences')]:
        rosters[cat] = [int(x) for x in re.findall(r'(?m)^\| (\d+) \|', section(text, heading))]
    rosters['unit_scale'] = [int(x) for x in re.findall(r'\bResponse (\d+)\b', section(text, '### Unit and scale differences'))]
    by_number = {}
    for cat in CATEGORIES:
        require(len(rosters[cat]) == expected_counts[cat], 'Category size mismatch: ' + cat)
        for n in rosters[cat]:
            require(n not in by_number, 'Duplicate category assignment')
            by_number[n] = cat
    require(set(by_number) == {n for _, n in sample}, 'Missing/extra category ID')
    return [{'id': i, 'response_number': n, 'category': by_number[n]} for i, n in sample]


def unique_rows(rows, label):
    require(isinstance(rows, list) and all(isinstance(r, dict) and isinstance(r.get('id'), str) for r in rows),
            'Invalid rows: ' + label)
    result = {r['id']: r for r in rows}
    require(len(result) == len(rows), 'Duplicate ID: ' + label)
    return result


def validate_sets(summary, neutral, sample, n=1127, budget=225, mismatch_n=131, mandatory_n=35):
    by_id, by_neutral = unique_rows(summary['rows'], 'summary'), unique_rows(neutral['rows'], 'neutral')
    universe = set(by_id)
    require(summary['N_planned'] == n == len(universe) and universe == set(by_neutral), 'Planned universe mismatch')
    require(summary['verification_candidate'] == 'priority' and summary['matched_budget'] == budget,
            'Fixed primary candidate/budget mismatch')
    require(neutral['summary_sha256'] == INPUT_HASHES['summary'], 'Neutral summary binding mismatch')
    for identity in universe:
        a, b = by_id[identity], by_neutral[identity]
        require(a['numerical_status'] == b['numerical_status'] and a['operational_status'] == b['operational_status'],
                'Status mismatch')
        require(b['mandatory'] == (not a['checker']['usable']), 'Mandatory status mismatch')
    errors = [i for i in universe if by_id[i]['numerical_status'] == 'known_numeric_error']
    require(len(errors) == mismatch_n, 'Frozen mismatch population differs')
    errors.sort(key=lambda i: (digest((AUDIT_SEED + '\0' + i).encode()), i))
    require([r['id'] for r in sample] == errors[:len(sample)], 'Original ordered hash sample differs')
    mandatory = {i for i in universe if by_neutral[i]['mandatory']}
    require(len(mandatory) == mandatory_n, 'Mandatory population differs')
    reviewed = {}
    for name in ('verification_priority', 'confidence'):
        p = summary['policies'][name]
        r, a, m = set(p['review_ids']), set(p['accepted_ids']), set(p['mandatory_ids'])
        require(p['feasible'] is True and p['budget'] == budget, 'Primary policy infeasible/wrong budget')
        require(len(r) == len(p['review_ids']) == budget and len(a) == len(p['accepted_ids']) == n-budget,
                'Review/accepted count or duplicate mismatch')
        require(not r & a and r | a == universe, 'Policy partition differs')
        require(len(m) == len(p['mandatory_ids']) and m == mandatory and m <= r, 'Common mandatory sets differ')
        reviewed[name] = r
    return by_neutral, reviewed['verification_priority'], reviewed['confidence'], mandatory


def membership(identity, b, c):
    return 'both' if identity in b and identity in c else 'B_only' if identity in b else 'confidence_only' if identity in c else 'neither'


def rounded(value, places=8):
    # Exact nonnegative Fraction -> decimal half-up, without binary floats.
    require(value >= 0, 'Magnitude must be nonnegative')
    q = value * 10**places
    k = q.numerator // q.denominator
    if q - k >= Fraction(1, 2): k += 1
    return str(k // 10**places) + '.' + str(k % 10**places).zfill(places)


def encoded(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'decimal_pp': rounded(value)}


def stats(values):
    values = sorted(values)
    if not values:
        return {'n': 0, 'min': None, 'median': None, 'max': None}
    n = len(values)
    median = values[n//2] if n % 2 else (values[n//2-1] + values[n//2])/2
    return {'n': n, 'min': encoded(values[0]), 'median': encoded(median), 'max': encoded(values[-1])}


def replicate(values):
    result = stats(values)
    require(result['n'] == 58, 'Percent arithmetic subset is not 58')
    for key, expected in [('min', '0.00510'), ('median', '0.00999'), ('max', '0.31494')]:
        f = result[key]
        require(rounded(Fraction(int(f['numerator']), int(f['denominator'])), 5) == expected,
                'Original percent aggregate replication failed: ' + key)
    return result


def load_helpers(implementation):
    root = Path(implementation).resolve()
    for name, expected in CODE_HASHES.items(): bound_read(root/name, expected)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root))
    runner = importlib.import_module('runner')
    schema = importlib.import_module('package.schema')
    checker = importlib.import_module('package.checker')
    numbers = importlib.import_module('package.numbers')
    for module in (runner, schema, checker, numbers):
        require(Path(module.__file__).resolve().is_relative_to(root), 'Wrong imported helper origin')
    return runner.response_content, schema.parse_response, checker.evaluate, numbers.number


def read_arithmetic(sample, neutral, summary, run, helpers, trace_log):
    content, parse, evaluate, number = helpers
    run = Path(run).resolve()
    magnitudes, units = {}, Counter()
    for row in sample:
        identity, n = row['id'], row['response_number']
        path = Path(neutral[identity]['response_file'])
        require(path.name == f'{n:02d}-response.json' and path.resolve().parent == run and not path.is_symlink(),
                'Response number/path differs or escapes run directory')
        if row['category'] != 'arithmetic':
            continue  # Do not open other categories, even though their paths are checked.
        expected = summary['provenance']['response_files'][path.name]
        body = bound_read(path, expected)
        trace_log.append({'id': identity, 'response_number': n, 'path': 'runs/test-01/'+path.name,
                          'sha256': expected, 'bytes': len(body)})
        record = json.loads(body)
        require(record['id'] == identity and record['attempt'] == n and record['status'] == 'received',
                'Response embedded identity/status mismatch')
        text, status = content(record['response'])
        require(status == 'complete' and text is not None, 'Arithmetic response not complete')
        response = parse(text)
        units[response['unit']] += 1
        if response['unit'] == 'percent':
            require(response['scale'] == '1', 'Percent scale is not 1')
            values = {x['id']: number(x['value']) for x in response['operands'] + response['constants']}
            calculated, _ = evaluate(response['expression'], values)
            magnitudes[identity] = abs(number(response['answer']) - calculated)
    require(len(trace_log) == 70, 'Exactly 70 arithmetic response reads required')
    aggregate = replicate(list(magnitudes.values()))  # Must pass before any policy split.
    return magnitudes, aggregate, dict(units)


def join(sample, b, c, mandatory, magnitudes):
    rows = [{**r, 'membership': membership(r['id'], b, c), 'mandatory': r['id'] in mandatory,
             'reviewed_B': r['id'] in b, 'reviewed_confidence': r['id'] in c} for r in sample]
    tables = []
    for category in (*CATEGORIES, 'all_audited_100'):
        group = rows if category == 'all_audited_100' else [r for r in rows if r['category'] == category]
        counts = {cell: sum(r['membership'] == cell for r in group) for cell in CELLS}
        m = sum(r['mandatory'] for r in group)
        require(all(not r['mandatory'] or r['membership'] == 'both' for r in group), 'Mandatory outside shared review')
        tables.append({'category': category, 'n': len(group), **counts, 'mandatory_within_both': m,
                       'discretionary_both': counts['both']-m, 'reviewed_B': counts['both']+counts['B_only'],
                       'reviewed_confidence': counts['both']+counts['confidence_only'],
                       'B_minus_confidence_reviewed': counts['B_only']-counts['confidence_only']})
    magnitude_rows = [{'id': r['id'], 'response_number': r['response_number'], 'membership': r['membership'],
                       'difference_pp': encoded(magnitudes[r['id']])} for r in rows if r['id'] in magnitudes]
    magnitude_cells = {cell: stats([magnitudes[r['id']] for r in rows if r['id'] in magnitudes and r['membership'] == cell])
                       for cell in CELLS}
    return rows, tables, magnitude_rows, magnitude_cells


def execute(args):
    paths = {key: Path(getattr(args, key)).resolve() for key in INPUT_HASHES}
    out = fresh(args.out, [p.parent for p in paths.values()] + [args.implementation, args.run_dir])
    start, traces = time.monotonic(), []
    resources = {'status': 'started', 'external_usd': 0, 'model_calls': 0, 'network_requests': 0,
                 'trace_files_read': traces, 'original_modifications': False}
    try:
        bodies = {key: bound_read(path, INPUT_HASHES[key]) for key, path in paths.items()}
        summary, neutral = json.loads(bodies['summary']), json.loads(bodies['neutral'])
        sample = parse_taxonomy(bodies['audit'].decode())
        by_neutral, b, c, mandatory = validate_sets(summary, neutral, sample)
        require(Path(args.run_dir).resolve() == paths['audit'].parent/'runs/test-01', 'Wrong approved run directory')
        helpers = load_helpers(args.implementation)
        magnitudes, aggregate, units = read_arithmetic(sample, by_neutral, summary, args.run_dir, helpers, traces)
        rows, table, magnitude_rows, cells = join(sample, b, c, mandatory, magnitudes)
        result = {'scope': 'Post-study descriptive audit only; no primary-result or policy change',
                  'planned_n': 1127, 'audited_n': 100, 'mismatch_population_n': 131,
                  'budget_per_policy': 225, 'candidate': 'priority', 'category_membership': table,
                  'full_frame_membership': dict(Counter(membership(i, b, c) for i in by_neutral)),
                  'original_arithmetic_units': units, 'percent_magnitude_aggregate': aggregate,
                  'percent_magnitude_by_membership': cells, 'joined_audit_rows': rows,
                  'percent_magnitude_rows': magnitude_rows,
                  'interpretation': 'Counts describe the original audited sample only. Differences are answer-versus-own-expression percentage points, not materiality, target error, relative-percent error or financial loss. Mandatory cases are shared. The original overall comparison remains unidentified.'}
        script_root = Path(__file__).parent
        provenance = {'inputs': {key: {'path': str(path), 'sha256': INPUT_HASHES[key]} for key, path in paths.items()},
                      'frozen_helpers': CODE_HASHES, 'trace_files': traces,
                      'historical_protocol_hashes': {'PLAN.md': '2f6c22c63260f90fc8079879d8c520d61480d283149dd6e0ba9f67d5a90a1b08',
                                                    'PLAN-REVIEW.md': 'cb73e8444d27732fa5072819200813af7cd33344cef1045db72ab14d5ef4ee48'},
                      'diagnostic_files': {name: digest((script_root/name).read_bytes()) for name in ('diagnose.py', 'test_diagnose.py')},
                      'invariants_passed': True, 'aggregate_replicated_before_policy_split': True}
        save(out/'results.json', result)
        save(out/'provenance.json', provenance)
        resources['status'] = 'completed'
        print(json.dumps({'status': 'completed', 'out': str(out), 'audited_n': len(rows), 'percent_n': len(magnitudes)}))
    except Exception as error:
        resources['status'] = 'failed'
        save(out/'failure.json', {'type': type(error).__name__, 'message': str(error), 'no_automatic_retry': True})
        raise
    finally:
        resources['elapsed_seconds'] = time.monotonic()-start
        resources['trace_count'] = len(traces)
        resources['trace_bytes'] = sum(t['bytes'] for t in traces)
        resources['output_hashes'] = {p.name: digest(p.read_bytes()) for p in out.iterdir() if p.is_file()}
        save(out/'resources.json', resources)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('audit', 'summary', 'neutral', 'implementation', 'run-dir', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    execute(p.parse_args())


if __name__ == '__main__':
    main()
