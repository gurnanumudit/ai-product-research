"""Offline version2 all-planned-ID accounting. No calls or gold repair."""
import argparse
from collections import Counter
from dataclasses import asdict, replace
import json
from pathlib import Path
import random

from package.checker import CheckReport, check_response
from package.policies import matched_policies, strict_withholding, PRIMARY_SEED, TIE_SEEDS
from package.schema import parse_response
from package.scorer import score_final
from runner import digest, load_inputs, response_content, save_json, value_digest


def keyed(records, planned, label):
    result = {}
    for record in records:
        if not isinstance(record, dict) or record.get('id') not in planned:
            raise ValueError(label + ': unknown/missing ID')
        if record['id'] in result:
            raise ValueError(label + ': duplicate ID')
        result[record['id']] = record
    return result


def paired_accounting(left, right, by_id, denominator):
    """Verification minus confidence; shared unresolved outcomes cancel exactly."""
    if not left['feasible'] or not right['feasible']:
        return {'feasible': False, 'accounting_envelope': None}
    accepted_left, accepted_right = set(left['accepted_ids']), set(right['accepted_ids'])
    known, positive, negative = 0, 0, 0
    for identity in accepted_left ^ accepted_right:
        direction = 1 if identity in accepted_left else -1
        status = by_id[identity]['numerical_status']
        if status == 'known_numeric_error':
            known += direction
        elif status.startswith('unknown_'):
            positive += direction == 1
            negative += direction == -1
    return {'feasible': True, 'known_difference_numerator': known,
        'unknown_positive_discordant': positive, 'unknown_negative_discordant': negative,
        'denominator': denominator,
        'accounting_envelope': {'lower_numerator': known - negative,
            'upper_numerator': known + positive, 'denominator': denominator,
            'lower': (known - negative) / denominator, 'upper': (known + positive) / denominator},
        'sign': 'negative favors verification; positive favors confidence',
        'interpretation': 'Unresolved-label accounting possibilities, not confidence interval or truth bounds.'}


def policy_accounting(reports, output, budget, verification, seed=PRIMARY_SEED):
    by_id = {r['id']: r for r in output}
    n = len(output)
    policy_results = {}
    for name, decision in matched_policies(reports, budget=budget, seed=seed, verification=verification).items():
        result = asdict(decision)
        if decision.feasible:
            accepted = [by_id[i] for i in decision.accepted_ids]
            errors = sum(r['numerical_status'] == 'known_numeric_error' for r in accepted)
            unresolved = sum(r['numerical_status'].startswith('unknown_') for r in accepted)
            result.update(accepted_known_numeric_errors=errors, accepted_unresolved=unresolved,
                escaped_error_accounting_envelope={'lower_numerator': errors,
                    'upper_numerator': errors + unresolved, 'denominator': n,
                    'lower': errors / n, 'upper': (errors + unresolved) / n})
        else:
            result.update(accepted_known_numeric_errors=None, accepted_unresolved=None,
                          escaped_error_accounting_envelope=None)
        policy_results[name] = result
    paired = {name: paired_accounting(decision, policy_results['confidence'], by_id, n)
              for name, decision in policy_results.items() if name.startswith('verification_')}
    return policy_results, paired


def candidate_objectives(policy_results, denominator):
    """Report only candidates already evaluated; never introduce a test candidate."""
    objectives = {}
    for candidate in ('count', 'priority'):
        policy = policy_results.get('verification_' + candidate)
        if policy is None:
            continue
        errors = policy['accepted_known_numeric_errors']
        unresolved = policy['accepted_unresolved']
        objectives[candidate] = {'feasible': policy['feasible'],
            'accepted_known_numeric_errors': errors, 'accepted_unresolved': unresolved,
            'objective_numerator': errors + unresolved if policy['feasible'] else None,
            'denominator': denominator}
    return objectives


def development_selection(policy_results):
    feasible = [(policy_results['verification_' + c]['accepted_known_numeric_errors'] +
                 policy_results['verification_' + c]['accepted_unresolved'], i, c)
                for i, c in enumerate(('count', 'priority'))
                if policy_results['verification_' + c]['feasible']]
    return {'selected': min(feasible)[2] if feasible else None,
        'rule': 'Minimize all-planned accepted known errors plus unresolved at20%; tie chooses count.',
        'selection_is_not_final_test_efficacy': True}


def coefficient_bounds(left_ids, right_ids, original_ids, statuses, n):
    """Same original question has one unknown truth even when resampled twice."""
    coefficients = Counter()
    for identity in left_ids:
        coefficients[original_ids[identity]] += 1
    for identity in right_ids:
        coefficients[original_ids[identity]] -= 1
    known = sum(c for i, c in coefficients.items() if statuses[i] == 'known_numeric_error')
    lower = known + sum(min(c, 0) for i, c in coefficients.items() if statuses[i].startswith('unknown_'))
    upper = known + sum(max(c, 0) for i, c in coefficients.items() if statuses[i].startswith('unknown_'))
    return lower / n, upper / n


def linear_percentile(values, probability):
    values = sorted(values)
    position = (len(values) - 1) * probability
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


def cluster_uncertainty(reports, output, groups, verification, grouping='report', replicates=1000):
    """Frozen paired clustered resampling; all ranks/budgets recomputed per draw."""
    identities = {r.id for r in reports}
    if (not isinstance(groups, dict) or set(groups) != identities
            or not all(isinstance(g, str) and g for g in groups.values())):
        return {'status': 'unavailable', 'reason': 'missing_or_invalid_frozen_group_mapping', 'grouping': grouping}
    members = {}
    for report in reports:
        members.setdefault(groups[report.id], []).append(report)
    if len(members) < 2:
        return {'status': 'unavailable', 'reason': 'fewer_than_two_groups', 'grouping': grouping}
    actual = matched_policies(reports, len(reports) // 5, verification=verification)
    if not actual['confidence'].feasible:
        return {'status': 'unavailable', 'reason': 'actual_primary_budget_infeasible', 'grouping': grouping}
    statuses = {r['id']: r['numerical_status'] for r in output}
    names = sorted(members)
    rng = random.Random(20261012)
    samples = {name: [] for name in actual if name.startswith('verification_')}
    infeasible = 0
    for iteration in range(replicates):
        copied, original_ids = [], {}
        for occurrence, name in enumerate(rng.choices(names, k=len(names))):
            for row_position, report in enumerate(members[name]):
                identity = f'{occurrence:06d}:{row_position:06d}'
                copied.append(replace(report, id=identity))
                original_ids[identity] = report.id
        n = len(copied)
        policies = matched_policies(copied, n // 5, verification=verification, original_ids=original_ids)
        if not policies['confidence'].feasible:
            infeasible += 1
        for name in samples:
            if not policies[name].feasible:
                bounds, status = (-1.0, 1.0), 'infeasible_uninformative_envelope'
            else:
                bounds = coefficient_bounds(policies[name].accepted_ids,
                    policies['confidence'].accepted_ids, original_ids, statuses, n)
                status = 'feasible'
            samples[name].append({'replicate': iteration, 'N': n, 'K': n // 5,
                                  'status': status, 'lower': bounds[0], 'upper': bounds[1]})
    return {'status': 'available', 'grouping': grouping, 'group_count': len(names),
        'replicates': replicates, 'seed': 20261012, 'infeasible_replicates': infeasible,
        'infeasible_fraction': infeasible / replicates,
        'comparisons': {name: {'approximate_95pct_uncertainty_envelope': [
            linear_percentile([r['lower'] for r in records], .025),
            linear_percentile([r['upper'] for r in records], .975)], 'replicate_records': records}
            for name, records in samples.items()},
        'method': 'Report/company clusters sampled with replacement; entire clusters retained; '
            'N* and floor(.20N*) recomputed; original-ID primary tie hash, occurrenceID last. '
            'Aggregate coefficients of repeated original questions before unknown-label bounds. '
            'Infeasible replicates retained as[-1,+1] for this uncertainty envelope only.',
        'interpretation': 'Approximate benchmark-resampling uncertainty with unresolved-label possibilities; '
            'not a causal, production-generalization, or established truth confidence interval.'}


def summarize(rows, annotations, responses, attempts=(), verification='both', tie_sensitivity=True):
    ids = [r['id'] for r in rows]
    n = len(ids)
    if not 1 <= n <= 1147 or len(set(ids)) != n:
        raise ValueError('Every unique planned ID required, maximum1147')
    references = keyed(annotations['records'], ids, 'annotations')
    records = keyed(responses, ids, 'responses')
    intents = keyed(attempts, ids, 'attempts')
    reports, output = [], []
    for item in rows:
        identity = item['id']
        annotation = references.get(identity, {})
        reference = annotation.get('scoring') if annotation.get('qualified') is True else None
        qualified = score_final(None, reference).scorable
        record = records.get(identity)
        content = None
        if record is None:
            operational = 'attempt_without_response' if identity in intents else 'not_attempted_or_missing_record'
        elif record.get('status') != 'received':
            operational = str(record.get('status', 'missing_record_status'))
        else:
            content, operational = response_content(record.get('response'))
        if content is None:
            report = CheckReport(identity, False, None, mandatory_reasons=(operational,))
            prediction, score = None, score_final(None, reference)
            numerical = 'unknown_operational_failure'
        else:
            report = check_response(item, content)
            try:
                prediction = parse_response(content)
            except (ValueError, TypeError, KeyError, RecursionError):
                prediction = None
            score = score_final(prediction, reference)
            if prediction is None or prediction.get('answer') is None:
                numerical = 'unknown_operational_failure'
                operational = 'explicit_abstention' if prediction is not None else 'malformed_response'
            elif not score.scorable:
                numerical = 'unknown_reference'
            elif score.reason == 'unit_mismatch':
                numerical = 'unknown_unit_contract_mismatch'
            elif score.reason.startswith('invalid_prediction:'):
                numerical = 'unknown_prediction_comparability'
            else:
                numerical = 'known_correct' if score.correct else 'known_numeric_error'
        reports.append(report)
        output.append({'id': identity, 'reference_qualified': qualified,
            'annotation_status': annotation.get('status', 'missing_annotation'),
            'operational_status': operational, 'numerical_status': numerical,
            'scorer': asdict(score), 'checker': asdict(report),
            'attempt_record_present': identity in intents, 'response_record_present': record is not None})
    policy_results, paired = policy_accounting(reports, output, n // 5, verification)
    counts = Counter(r['numerical_status'] for r in output)
    correct, wrong = counts['known_correct'], counts['known_numeric_error']
    result = {'schema_version': 2, 'scope': 'Offline review-policy comparison; no automatic efficacy assertion',
        'N_planned': n, 'Q_qualified_references': sum(r['reference_qualified'] for r in output),
        'M_numerically_comparable': correct + wrong, 'C_known_correct': correct,
        'W_known_numeric_errors': wrong, 'unresolved_numerical': n - correct - wrong,
        'operational_failures_or_abstentions': sum(not r.usable for r in reports),
        'unqualified_reference_ids': [r['id'] for r in output if not r['reference_qualified']],
        'unit_contract_mismatch_ids': [r['id'] for r in output if r['numerical_status'] == 'unknown_unit_contract_mismatch'],
        'numerical_status_counts': dict(sorted(counts.items())), 'rows': output,
        'matched_budget': n // 5, 'policies': policy_results, 'paired_primary': paired,
        'verification_candidate': verification, 'primary_seed': PRIMARY_SEED,
        'strict_all_warning_diagnostic': strict_withholding(reports),
        'interpretation': 'No output-dependent exclusions. C/M is not whole-pilot accuracy. '
            'Policy envelopes are unresolved-label accounting possibilities, not confidence intervals '
            'or established truth bounds: ambiguous questions may lack a unique correct answer. '
            'Mandatory abstentions consume capacity; exceeding the review budget makes the operating point infeasible. '
            'References are joined only after gold-free checker/policy inputs are formed.'}
    result['secondary_budgets'] = {}
    for numerator in (1, 3):
        policies, comparisons = policy_accounting(reports, output, numerator * n // 10, verification)
        result['secondary_budgets'][str(numerator / 10)] = {'policies': policies, 'paired': comparisons}
    if verification == 'both':
        result['development_selection'] = development_selection(policy_results)
    if tie_sensitivity:
        result['tie_sensitivity'] = []
        for seed in TIE_SEEDS:
            seed_policies, seed_paired = policy_accounting(reports, output, n // 5, verification, seed)
            sensitivity = {'seed': seed, 'paired': seed_paired,
                'candidate_objectives': candidate_objectives(seed_policies, n)}
            if verification == 'both':
                sensitivity['development_selection'] = development_selection(seed_policies)
            result['tie_sensitivity'].append(sensitivity)
        result['tie_sensitivity_interpretation'] = '100 fixed secondary tie seeds; never select a favorable seed; not sampling confidence intervals.'
    return result


def load_run(folder, rows):
    """Check saved IDs/order/hash agreement; retain missing files as missing outcomes."""
    folder = Path(folder)
    preflight = json.loads((folder / 'preflight.json').read_text())
    template = json.loads((folder / 'approval-template.json').read_text())
    if template['ids'] != [r['id'] for r in rows]:
        raise ValueError('Frozen planned ID order mismatch')
    responses, attempts = [], []
    for suffix, destination in (('request', attempts), ('response', responses)):
        for path in sorted(folder.glob('*-' + suffix + '.json')):
            record = json.loads(path.read_text())
            attempt = record.get('attempt')
            if type(attempt) is not int or not 1 <= attempt <= len(rows):
                raise ValueError('Invalid saved attempt number')
            if path.name != f'{attempt:02d}-{suffix}.json' or record['id'] != template['ids'][attempt - 1]:
                raise ValueError('Saved attempt/ID/file order mismatch')
            if suffix == 'request' and value_digest(record['payload']) != template['request_sha256'][attempt - 1]:
                raise ValueError('Saved request payload differs from prospective freeze')
            destination.append(record)
    if any(r['id'] not in {a['id'] for a in attempts} for r in responses):
        raise ValueError('Response without durable dispatch intent')
    return template, responses, attempts, preflight


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--adjudication', required=True)
    parser.add_argument('--run', required=True)
    parser.add_argument('--out', required=True, help='New JSON file, never overwritten')
    parser.add_argument('--groups', help='Frozen selection metadata with selected id/report_group/company')
    args = parser.parse_args()
    template = json.loads((Path(args.run) / 'approval-template.json').read_text())
    rows = load_inputs(args.inputs, template['planned'])
    template, responses, attempts, preflight = load_run(args.run, rows)
    if digest(args.inputs) != template['input_sha256'] or digest(args.adjudication) != template['adjudication_sha256']:
        raise ValueError('Input/adjudication freeze mismatch')
    annotations = json.loads(Path(args.adjudication).read_text())
    result = summarize(rows, annotations, responses, attempts, verification=template['verification_candidate'])
    if args.groups:
        if digest(args.groups) != template['group_metadata_sha256']:
            raise ValueError('Group metadata differs from prospective freeze')
        selected = json.loads(Path(args.groups).read_text())['selected']
        group_rows = keyed(selected, [r['id'] for r in rows], 'groups')
        reports = [CheckReport(**r['checker']) for r in result['rows']]
        result['cluster_inference'] = {
            label: cluster_uncertainty(reports, result['rows'],
                {i: r.get(field) for i, r in group_rows.items()}, template['verification_candidate'], label)
            for label, field in (('report', 'report_group'), ('company', 'company'))}
        result['group_metadata_sha256'] = digest(args.groups)
    else:
        result['cluster_inference'] = {'status': 'unavailable', 'reason': 'no_frozen_group_mapping'}
    result['provenance'] = {'input_sha256': digest(args.inputs),
        'adjudication_sha256': digest(args.adjudication), 'run_directory': str(Path(args.run).resolve()),
        'preflight': preflight,
        'response_files': {p.name: digest(p) for p in sorted(Path(args.run).glob('*-response.json'))},
        'request_files': {p.name: digest(p) for p in sorted(Path(args.run).glob('*-request.json'))}}
    save_json(args.out, result)
    print(f'Saved all {len(rows)} planned IDs; no automatic efficacy conclusion.')


if __name__ == '__main__':
    main()
