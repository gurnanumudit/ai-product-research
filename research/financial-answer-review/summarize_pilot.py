"""Offline, all-planned-ID Stage A accounting. Never calls a provider or repairs gold."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path

from package.checker import CheckReport, check_response
from package.policies import matched_policies, strict_withholding
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


def summarize(rows, annotations, responses, attempts=()):
    ids = [r['id'] for r in rows]
    if len(ids) != 50 or len(set(ids)) != 50:
        raise ValueError('All 50 unique planned IDs required')
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
    by_id = {r['id']: r for r in output}
    policy_results = {}
    for name, decision in matched_policies(reports, budget=10).items():
        result = asdict(decision)
        if decision.feasible:
            accepted = [by_id[i] for i in decision.accepted_ids]
            errors = sum(r['numerical_status'] == 'known_numeric_error' for r in accepted)
            unresolved = sum(r['numerical_status'].startswith('unknown_') for r in accepted)
            result.update(accepted_known_numeric_errors=errors, accepted_unresolved=unresolved,
                escaped_error_accounting_envelope={'lower_numerator': errors,
                    'upper_numerator': errors + unresolved, 'denominator': 50,
                    'lower': errors / 50, 'upper': (errors + unresolved) / 50})
        else:
            result.update(accepted_known_numeric_errors=None, accepted_unresolved=None,
                          escaped_error_accounting_envelope=None)
        policy_results[name] = result
    counts = Counter(r['numerical_status'] for r in output)
    correct, wrong = counts['known_correct'], counts['known_numeric_error']
    return {'schema_version': 1, 'scope': 'Stage A feasibility; no policy-efficacy assertion',
        'N_planned': 50, 'Q_qualified_references': sum(r['reference_qualified'] for r in output),
        'M_numerically_comparable': correct + wrong, 'C_known_correct': correct,
        'W_known_numeric_errors': wrong, 'unresolved_numerical': 50 - correct - wrong,
        'operational_failures_or_abstentions': sum(not r.usable for r in reports),
        'unqualified_reference_ids': [r['id'] for r in output if not r['reference_qualified']],
        'unit_contract_mismatch_ids': [r['id'] for r in output if r['numerical_status'] == 'unknown_unit_contract_mismatch'],
        'numerical_status_counts': dict(sorted(counts.items())), 'rows': output,
        'matched_budget': 10, 'policies': policy_results,
        'strict_all_warning_diagnostic': strict_withholding(reports),
        'interpretation': 'No output-dependent exclusions. C/M is not whole-pilot accuracy. '
            'Policy envelopes are unresolved-label accounting possibilities, not confidence intervals '
            'or established truth bounds: ambiguous questions may lack a unique correct answer. '
            'Mandatory abstentions consume capacity; over ten makes every matched policy infeasible. '
            'References are joined only after gold-free checker/policy inputs are formed.'}


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
            if type(attempt) is not int or not 1 <= attempt <= 50:
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
    args = parser.parse_args()
    rows = load_inputs(args.inputs)
    template, responses, attempts, preflight = load_run(args.run, rows)
    if digest(args.inputs) != template['input_sha256'] or digest(args.adjudication) != template['adjudication_sha256']:
        raise ValueError('Input/adjudication freeze mismatch')
    annotations = json.loads(Path(args.adjudication).read_text())
    result = summarize(rows, annotations, responses, attempts)
    result['provenance'] = {'input_sha256': digest(args.inputs),
        'adjudication_sha256': digest(args.adjudication), 'run_directory': str(Path(args.run).resolve()),
        'preflight': preflight,
        'response_files': {p.name: digest(p) for p in sorted(Path(args.run).glob('*-response.json'))},
        'request_files': {p.name: digest(p) for p in sorted(Path(args.run).glob('*-request.json'))}}
    save_json(args.out, result)
    print('Saved all 50 planned IDs; no efficacy conclusion.')


if __name__ == '__main__':
    main()
