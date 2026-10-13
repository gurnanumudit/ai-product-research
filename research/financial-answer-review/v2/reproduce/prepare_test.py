"""Offline final-frame transformation from explicitly supplied local files.

Adapted from the frozen prepare_test.py; no acquisition, approval, or model path.
Census/eligibility/order/audit logic is retained. Caller-supplied local bindings
are provenance checks, not scientific approval. No review records are distributed.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import prepare_dev
import final_io

SOURCE_N = 1147
HISTORICAL_SOURCE_SCRIPT_SHA = '05e1d645d6c2e61149d03a1341b423f7b55f733a02aac09e1e280252b6f3cec5'


def rank(seed, identifier):
    return hashlib.sha256((seed + '\0' + identifier).encode()).hexdigest()


def validate_exposure(exposure, protocol_sha):
    if exposure.get('protocol_sha256') != protocol_sha:
        raise ValueError('Exposure must bind the supplied protocol')
    groups = exposure['groups']
    if not isinstance(groups, dict) or not groups:
        raise ValueError('Explicit exposure groups required')
    union = set()
    for group in groups.values():
        ids = group['ids']
        if (not isinstance(ids, list) or len(ids) != len(set(ids)) or
                any(not isinstance(i, str) or len(i.split('/')) != 3 for i in ids)):
            raise ValueError('Invalid prior exposure IDs')
        expected = {'reports': sorted({'/'.join(i.split('/')[:2]) for i in ids}),
                    'pages': sorted({i.rsplit('-', 1)[0] for i in ids}),
                    'companies': sorted({i.split('/')[0] for i in ids})}
        if any(group[key] != value for key, value in expected.items()):
            raise ValueError('Exposure group metadata disagrees with IDs')
        union.update(ids)
    if exposure['excluded_exact_ids'] != sorted(union):
        raise ValueError('Exposure union differs from supplied groups')
    if exposure.get('excluded_exact_id_count') != len(union):
        raise ValueError('Exposure union count differs')
    expected_sha = hashlib.sha256((json.dumps(sorted(union), separators=(',', ':')) + '\n').encode()).hexdigest()
    if exposure.get('union_ids_sha256') != expected_sha:
        raise ValueError('Exposure union digest differs')

def census(records, protocol, exposure, expected_n=SOURCE_N):
    if not isinstance(records, list) or len(records) != expected_n:
        raise ValueError('Unexpected pinned source frame')
    identifiers = [r.get('id') if isinstance(r, dict) else None for r in records]
    # Non-string/malformed IDs receive ordinary unsupported-ID exclusion, but
    # duplicate source identifiers indicate a corrupt frame and stop intake.
    valid_ids = [i for i in identifiers if isinstance(i, str)]
    if len(valid_ids) != len(set(valid_ids)):
        raise ValueError('Duplicate source IDs')
    helper_protocol = {'prior_exposed_ids_excluded': exposure['excluded_exact_ids'],
                       'prior_exposed_reports_flagged': [], 'seed': protocol['seed']}
    selected, excluded, chosen = [], [], {}
    for source_index, record in enumerate(records):
        if not isinstance(record, dict) or not isinstance(record.get('qa', {}), dict):
            raise ValueError('Unexpected source object/qa schema')
        meta, reason = prepare_dev.metadata(record, helper_protocol)
        if reason:
            excluded.append({'source_index': source_index, 'id': record.get('id'), 'reason': reason})
            continue
        if meta['stratum'] not in protocol['strata']:
            raise ValueError('Unknown stratum')
        flags = {}
        for label, group in exposure['groups'].items():
            flags[label] = {'report': meta['report_group'] in group['reports'],
                            'page': meta['page_group'] in group['pages'],
                            'company': meta['company'] in group['companies']}
        meta['exposure_flags'] = flags
        meta['documented_prior_exposed_report'] = any(f['report'] for f in flags.values())
        selected.append(meta)
        chosen[meta['id']] = record
    selected.sort(key=lambda m: (m['rank_hash'], m['id']))
    if not selected or len(selected) > protocol['maximum_selected_n']:
        raise ValueError('Empty or oversized natural frame; no alternate sample')
    sample = []
    audit_rule = protocol['independent_audit']
    for stratum in protocol['strata']:
        candidates = [m for m in selected if m['stratum'] == stratum]
        candidates.sort(key=lambda m: (rank(audit_rule['seed'], m['id']), m['id']))
        sample.extend({'id': m['id'], 'stratum': stratum,
                       'audit_hash': rank(audit_rule['seed'], m['id'])}
                      for m in candidates[:audit_rule['n_per_stratum']])
    return [chosen[m['id']] for m in selected], selected, excluded, sample


def prepare(source, protocol_path, exposure_path, binding_path, out):
    paths = {'source': Path(source), 'protocol': Path(protocol_path), 'exposure': Path(exposure_path)}
    out = final_io.destination(out, [p.parent for p in [*paths.values(), Path(binding_path)]])
    expected = final_io.bindings(binding_path, paths)
    bodies = {key: final_io.read_bound(path, expected[key]) for key, path in paths.items()}
    protocol = json.loads(bodies['protocol'])
    exposure = json.loads(bodies['exposure'])
    if protocol['source_sha256'] != expected['source'] or protocol['source_expected_bytes'] != len(bodies['source']):
        raise ValueError('Source bytes/hash disagree with supplied protocol')
    validate_exposure(exposure, expected['protocol'])
    records = json.loads(bodies['source'])
    chosen, selected, excluded, audit = census(records, protocol, exposure,
                                                expected_n=protocol['source_expected_n'])
    inputs = [{'id': r['id'], 'question': r['qa']['question'],
               'locations': prepare_dev.locations(r)} for r in chosen]
    gold = [{'id': r['id'], 'source_split': 'test', 'original_qa': r['qa']} for r in chosen]
    selection = {'source_n': len(records), 'selected_n': len(selected), 'eligible_n': len(selected),
                 'selection': 'natural_eligible_census', 'seed': protocol['seed'],
                 'selected': selected, 'excluded': excluded,
                 'stratum_counts': dict(Counter(m['stratum'] for m in selected)),
                 'report_groups': len({m['report_group'] for m in selected}),
                 'page_groups': len({m['page_group'] for m in selected}),
                 'company_groups': len({m['company'] for m in selected}),
                 'report_group_sizes': dict(Counter(m['report_group'] for m in selected)),
                 'company_group_sizes': dict(Counter(m['company'] for m in selected))}
    for name, obj in {'inputs.json': inputs, 'gold.json': gold, 'selection.json': selection,
                      'independent-audit-selection.json': {'rule': protocol['independent_audit'], 'selected': audit}}.items():
        final_io.save(out / name, obj)
    here = Path(__file__).parent
    final_io.receipt(out, {**expected, 'bindings_file': final_io.digest(binding_path)},
                     HISTORICAL_SOURCE_SCRIPT_SHA,
                     [Path(__file__), here / 'prepare_dev.py', here / 'final_io.py', here / 'safe_output.py'])
    return selection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'protocol', 'exposure', 'bindings', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.source, args.protocol, args.exposure, args.bindings, args.out)
    print(json.dumps({'selected_n': result['selected_n'], 'mode': 'offline'}))


if __name__ == '__main__':
    main()

