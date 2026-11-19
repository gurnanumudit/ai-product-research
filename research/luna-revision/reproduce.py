"""Offline numerical replay from released derived records. No work on import."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import computation as c

ROOT = Path(__file__).resolve().parent
FIELDS = {'family_id', 'domain', 'stratum', 'workflow', 'model', 'resolved',
          'passed', 'valid', 'truncated', 'cost_nano_usd',
          'pending_reserve_nano_usd', 'tokens', 'times_ms', 'output_status'}


def validate(rows):
    c.need(len(rows) == 600, 'exactly600_endpoints')
    families = {}
    for row in rows:
        c.need(set(row) == FIELDS, 'public_schema')
        d, s, fid, w = (row[k] for k in ('domain', 'stratum', 'family_id', 'workflow'))
        c.need((d, s) in [('coding', 'VERY_HARD'), ('planning', 'graph_color'),
                         ('planning', 'sokoban')], 'domain_stratum')
        prefix, size = {'VERY_HARD': ('coding', 100), 'graph_color': ('graph', 50),
                        'sokoban': ('sokoban', 50)}[s]
        c.need(fid in {f'{prefix}-{i:03d}' for i in range(1, size+1)}, 'family_rank')
        c.need(w in c.WORKFLOWS and row['model'] == c.MODEL, 'workflow_model')
        f = families.setdefault(fid, {'canonical_family_id': fid, 'domain': d,
                                     'stratum': s, 'endpoints': {}})
        c.need((f['domain'], f['stratum']) == (d, s) and w not in f['endpoints'],
               'identity_or_duplicate_endpoint')
        c.need(row['resolved'] is True and type(row['passed']) is bool, 'resolved_boolean')
        for key in ('valid', 'truncated'):
            c.need(row[key] is None or type(row[key]) is bool, 'nullable_boolean')
        c.need(not ((row['valid'] is False or row['truncated'] is True) and row['passed']),
               'invalid_truncated_failure')
        c.need(c.integer(row['cost_nano_usd']) and row['pending_reserve_nano_usd'] == 0,
               'all600_settled')
        c.validate_tokens(row['tokens'])
        c.need(set(row['times_ms']) == set(c.TIMES)
               and all(c.measurement(v) for v in row['times_ms'].values()), 'times')
        c.need(isinstance(row['output_status'], str), 'output_status')
        f['endpoints'][w] = row
    c.need(len(families) == 200, 'exactly200_families')
    c.need(Counter(f['stratum'] for f in families.values()) ==
           {'VERY_HARD': 100, 'graph_color': 50, 'sokoban': 50}, 'fixed_strata')
    c.need(all(set(f['endpoints']) == set(c.WORKFLOWS) for f in families.values()),
           'every_family_has_triplet')
    return sorted(families.values(), key=lambda f: (f['domain'], f['stratum'],
                                                   f['canonical_family_id']))


def cells(families):
    return {w: {'n': len(families),
                'passed': sum(f['endpoints'][w]['passed'] for f in families),
                'pass_rate': sum(f['endpoints'][w]['passed'] for f in families)/len(families),
                'validity': {
                    'valid': sum(f['endpoints'][w]['valid'] is True for f in families),
                    'invalid': sum(f['endpoints'][w]['valid'] is False for f in families),
                    'missing': sum(f['endpoints'][w]['valid'] is None for f in families)},
                'truncation': {
                    'yes': sum(f['endpoints'][w]['truncated'] is True for f in families),
                    'no': sum(f['endpoints'][w]['truncated'] is False for f in families),
                    'missing': sum(f['endpoints'][w]['truncated'] is None for f in families)}}
            for w in c.WORKFLOWS}


def reproduce(rows, orphan):
    families = validate(rows)
    primary = {}
    for d in ('coding', 'planning'):
        fs = [f for f in families if f['domain'] == d]
        for a, b in [('A', 'S'), ('S', 'R')]:
            primary[f'{d}:{b}-{a}'] = c.pair_table(fs, a, b)
    adjusted, bootstrap = c.holm(primary), c.paired_bootstrap(families)
    for k in c.PRIMARY:
        primary[k].update(adjusted[k], bootstrap_pointwise95=bootstrap['intervals'][k])
        primary[k]['formal_improvement'] = (primary[k]['difference'] > 0
                                            and primary[k]['reject_two_sided_at_0_05'])
    c.need(orphan['logical_answer'] is False and orphan['cost_nano_usd'] is None
           and orphan['pending_reserve_nano_usd'] == 591016800, 'unknown_attempt_not_imputed')
    c.need((orphan['model'], orphan['domain'], orphan['stratum'], orphan['workflow']) ==
           (c.MODEL, 'coding', 'VERY_HARD', 'A'), 'original_attempt_scope')
    c.need(orphan['tokens'] == dict.fromkeys(c.TOKENS)
           and orphan['times_ms'] == dict.fromkeys(c.TIMES), 'original_missing_preserved')
    physical = rows + [orphan]
    return {
        'primary': primary, 'bootstrap': bootstrap,
        'domain_cells': {d: cells([f for f in families if f['domain'] == d])
                         for d in ('coding', 'planning')},
        'planning_subtypes': {s: {
            'diagnostic_only': True,
            'cells': cells([f for f in families if f['stratum'] == s]),
            'S-A': c.pair_table([f for f in families if f['stratum'] == s], 'A', 'S'),
            'R-S': c.pair_table([f for f in families if f['stratum'] == s], 'S', 'R')}
            for s in ('graph_color', 'sokoban')},
        'usable_response_totals': c.rollup(rows, ())[0],
        'usable_response_by_model_domain_workflow': c.rollup(rows, ('model', 'domain', 'workflow')),
        'experiment_totals': c.rollup(physical, ())[0],
        'experiment_by_model_domain_workflow': c.rollup(physical, ('model', 'domain', 'workflow')),
        'experiment_by_planning_subtype_workflow': c.rollup(
            [r for r in physical if r['domain'] == 'planning'], ('stratum', 'workflow')),
        'standalone_workflow_by_model_domain': c.rollup(c.standalone_rows(families),
                                                     ('model', 'domain', 'workflow')),
        'standalone_constituent_calls': {'A': 200, 'S': 200, 'R': 400},
        'pairs': [{'family_id': f['canonical_family_id'], 'domain': f['domain'],
                   'stratum': f['stratum'],
                   'passed': {w: f['endpoints'][w]['passed'] for w in c.WORKFLOWS},
                   'S_minus_A': int(f['endpoints']['S']['passed'])-int(f['endpoints']['A']['passed']),
                   'R_minus_S': int(f['endpoints']['R']['passed'])-int(f['endpoints']['S']['passed'])}
                  for f in families]}


def compare(actual, expected, path='root'):
    """Exact statistics/integers/nulls. Only summed time floats allow 1e-6 ms roundoff."""
    if isinstance(expected, dict):
        c.need(isinstance(actual, dict) and actual.keys() == expected.keys(), path + ': keys')
        for k in expected: compare(actual[k], expected[k], path + '.' + k)
    elif isinstance(expected, list):
        c.need(isinstance(actual, list) and len(actual) == len(expected), path + ': length')
        for i, (a, e) in enumerate(zip(actual, expected)): compare(a, e, f'{path}[{i}]')
    elif isinstance(expected, float) and '.times_ms.' in path:
        c.need(type(actual) in (float, int) and
               math.isclose(actual, expected, rel_tol=0, abs_tol=1e-6), path + ': time roundoff')
    else:
        c.need(type(actual) is type(expected) and actual == expected, path + ': differs')


def check_accounting(result, reference):
    a = reference['accounting']
    current, history = result['experiment_totals'], reference['historical_totals']
    c.need(current['physical_requests'] == a['current_campaign_physical_requests'] == 601
           and current['logical_answers'] == a['current_campaign_logical_answers'] == 600,
           'current_call_counts')
    c.need(history['physical_requests'] == a['historical_physical_requests'] == 397
           and history['logical_answers'] == a['historical_logical_answers'] == 396,
           'historical_aggregate_call_counts')
    c.need(current['cost_nano_usd']['known_sum'] == a['current_campaign_known_nano_usd']
           == a['adopted_known_nano_usd'] + a['continuation_settled_nano_usd'], 'current_cost_once')
    c.need(current['cost_nano_usd']['known_sum'] + history['cost_nano_usd']['known_sum']
           == a['known_api_once_nano_usd'], 'lifetime_known_once')
    c.need(a['current_campaign_physical_requests'] + a['historical_physical_requests']
           == a['lifetime_physical_requests'] == 998, 'lifetime_physical')
    c.need(a['current_campaign_logical_answers'] + a['historical_logical_answers']
           == a['lifetime_logical_answers'] == 996, 'lifetime_logical')
    c.need(a['current_campaign_pending_reserve_nano_usd'] + a['historical_pending_reserve_nano_usd']
           == a['total_pending_reserve_nano_usd'], 'reserves')
    c.need(a['known_api_once_nano_usd'] + a['total_pending_reserve_nano_usd']
           + a['infrastructure_commitment_nano_usd']
           == a['known_reserved_committed_envelope_nano_usd'], 'envelope_not_actual_bill')
    for k in ('original_current_actual_charge_nano_usd', 'historical_unknown_actual_charge_nano_usd',
              'actual_complete_api_nano_usd', 'infrastructure_invoice_nano_usd', 'all_in_actual_nano_usd'):
        c.need(a[k] is None, 'unknown_not_zero:' + k)
    c.need(a['additional_pending_reserve_nano_usd'] == 0, 'no_new_pending')


def verify_release_files():
    manifest = json.loads((ROOT/'HANDOFF.json').read_text())
    for name, item in manifest['files'].items():
        path = ROOT/name
        c.need(path.resolve().is_relative_to(ROOT) and path.is_file(), 'release_member')
        b = path.read_bytes()
        c.need(len(b) == item['bytes'] and hashlib.sha256(b).hexdigest() == item['sha256'],
               'release_hash:' + name)


def main():
    ap = argparse.ArgumentParser(description='Offline reproduction of released Luna A/S/R comparisons; no network or grading.')
    ap.add_argument('--write', action='store_true', help='Also write output/reproduced.json, refusing to replace an existing file.')
    args = ap.parse_args()
    verify_release_files()
    rows = [json.loads(line) for line in (ROOT/'data/outcomes.jsonl').read_text().splitlines()]
    orphan = json.loads((ROOT/'data/original-unresolved-attempt.json').read_text())
    reference = json.loads((ROOT/'reference/summary.json').read_text())
    result = reproduce(rows, orphan)
    for key, value in result.items():
        expected = json.loads((ROOT/'reference/pairs.json').read_text()) if key == 'pairs' else reference[key]
        compare(value, expected, key)
    check_accounting(result, reference)
    if args.write:
        (ROOT/'output').mkdir(exist_ok=True)
        with (ROOT/'output/reproduced.json').open('x') as f:
            json.dump(result, f, indent=2, allow_nan=False)
            f.write('\n')
    print(json.dumps({'validated': True, 'families': 200, 'resolved_endpoints': 600,
                      'bootstrap_index_stream_sha256': result['bootstrap']['resample_index_stream_sha256'],
                      'primary': result['primary'],
                      'limits': 'Derived-outcome numerical replay; no model rerun, regrading or raw receipt audit.'}, indent=2))


if __name__ == '__main__':
    main()
