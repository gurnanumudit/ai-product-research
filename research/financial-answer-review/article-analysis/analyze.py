"""Offline article supplement: original-reference scoring and matched review queues.

This is a portable adaptation, not the historical generating executable.
No provider calls, credentials, downloads or automatic input acquisition.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
IMPLEMENTATION = HERE.parent / 'v2' / 'implementation'
sys.path.insert(0, str(IMPLEMENTATION))
from package.checker import check_response
from package.policies import matched_policies, PRIMARY_SEED
from package.schema import parse_response


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()).hexdigest()


def final_times100(program):
    match = re.search(r'multiply\(([^,()]+),\s*([^,()]+)\)\s*$', program)
    return bool(match and any(s.strip() in ('100', 'const_100') for s in match.groups()))


def score(response, reference, strict=False):
    """Final-answer agreement, NOT official FinQA program execution accuracy."""
    gold = reference['exe_ans']
    if isinstance(gold, bool) or not isinstance(gold, (int, float)) or not math.isfinite(gold):
        raise ValueError('A finite original numerical answer is required')
    if response['answer'] is None:
        return 'abstention'
    value = Fraction(response['answer'])
    unit = response['unit'].strip().lower()
    divide_percent = unit == 'percent' and not final_times100(reference['program'])
    if divide_percent:
        value /= 100
    tolerance = Fraction('0.00005') if unit == 'ratio' or divide_percent else Fraction('0.005')
    match = (round(float(value), 5) == float(gold)) if strict else abs(value - Fraction(str(gold))) <= tolerance
    return 'match' if match else 'numeric_nonmatch'


def response_text(body):
    """Same completed-single-assistant-choice contract as the historical runner."""
    if not isinstance(body, dict) or body.get('error'):
        raise ValueError('Invalid or error response body')
    choices = body.get('choices')
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise ValueError('Expected one response choice')
    choice = choices[0]
    message = choice.get('message')
    if (not isinstance(message, dict) or message.get('role') != 'assistant'
            or message.get('refusal') or choice.get('finish_reason') != 'stop'
            or not isinstance(message.get('content'), str) or not message['content'].strip()):
        raise ValueError('Incomplete, refused or missing assistant answer')
    return message['content']


def keyed(rows):
    result = {}
    for row in rows:
        identity = row['id']
        if not isinstance(identity, str) or not identity or identity in result:
            raise ValueError('Unique nonempty row IDs required')
        result[identity] = row
    return result


def fraction(n, d):
    return {'numerator': n, 'denominator': d, 'percent': n / d * 100 if d else None}


def metrics(labels, decision):
    review, accepted, mandatory = map(set, (decision.review_ids, decision.accepted_ids, decision.mandatory_ids))
    if (not decision.feasible or len(review) != decision.budget or review & accepted
            or review | accepted != set(labels) or not mandatory <= review):
        raise ValueError('Invalid or infeasible review partition')
    mismatch = {i for i, label in labels.items() if label == 'numeric_nonmatch'}
    abstain = {i for i, label in labels.items() if label == 'abstention'}
    matching = {i for i, label in labels.items() if label == 'match'}
    found = len(review & mismatch)
    return {'reviewed': len(review), 'released': len(accepted),
            'reviewed_mismatches': found, 'released_mismatches': len(accepted & mismatch),
            'reviewed_abstentions': len(review & abstain), 'released_abstentions': len(accepted & abstain),
            'mandatory_slots': len(mandatory), 'mandatory_mismatches': len(mandatory & mismatch),
            'discretionary_mismatches': len((review - mandatory) & mismatch),
            'released_accuracy': fraction(len(accepted & matching), len(accepted)),
            'review_precision_per_slot': fraction(found, len(review)),
            'numeric_answer_precision': fraction(found, len(review - abstain)),
            'error_capture': fraction(found, len(mismatch))}


def analyze(inputs, annotations, responses):
    inputs, annotations, responses = map(keyed, (inputs, annotations, responses))
    if not inputs or set(inputs) != set(annotations) or set(inputs) != set(responses):
        raise ValueError('Complete, aligned input/reference/response sets required')
    labels, strict_labels, reports = {}, {}, []
    for identity, item in inputs.items():
        payload = parse_response(response_text(responses[identity]['response']))
        ref = annotations[identity]['original_reference']
        labels[identity] = score(payload, ref)
        strict_labels[identity] = score(payload, ref, strict=True)
        reports.append(check_response(item, payload))
    rows, decisions = [], {}
    previous = {}
    for percent, divisor in ((5, 20), (10, 10), (20, 5), (50, 2)):
        policies = matched_policies(reports, budget=len(labels) // divisor, seed=PRIMARY_SEED, verification='priority')
        for name, decision in policies.items():
            if not previous.get(name, set()) <= set(decision.review_ids):
                raise ValueError('Non-nested queue')
            previous[name] = set(decision.review_ids)
        decisions[percent] = policies
        rows.append({'review_percent': percent, 'policies': {name: metrics(labels, d) for name, d in policies.items()}})
    counts = Counter(labels.values())
    result = {'scope': 'Post-study adapted final-answer agreement, not official program execution accuracy',
              'seed': PRIMARY_SEED, 'N': len(labels), 'matches': counts['match'],
              'numeric_mismatches': counts['numeric_nonmatch'], 'abstentions': counts['abstention'],
              'baseline_accuracy': fraction(counts['match'], len(labels)), 'results': rows,
              'strict5_sensitivity_at_20_percent': {
                  'counts': dict(Counter(strict_labels.values())),
                  'policies': {name: metrics(strict_labels, d) for name, d in decisions[20].items()}}}
    return result, labels, decisions


def fresh_destination(out, archive):
    out, archive = out.absolute(), archive.resolve()
    if out.exists() or out.is_symlink() or any(p.is_symlink() for p in out.parents):
        raise ValueError('Output must be new and non-symlinked')
    if out.resolve() == archive or archive in out.resolve().parents:
        raise ValueError('Output must be outside the input archive')
    return out


def reproduce(archive, out):
    out = fresh_destination(Path(out), Path(archive))  # Refuse unsafe output before reading inputs.
    archive = Path(archive)
    provenance = json.loads((HERE / 'provenance.json').read_text())
    for relative, expected in provenance['source_input_sha256'].items():
        if digest(archive / relative) != expected:
            raise ValueError('Historical input checksum mismatch: ' + relative)
    for relative, expected in provenance['implementation_sha256'].items():
        if digest(IMPLEMENTATION / relative) != expected:
            raise ValueError('Implementation checksum mismatch: ' + relative)
    paths = sorted((archive / 'runs/test-01').glob('*-response.json'))
    hashes = {p.name: digest(p) for p in paths}
    if canonical_digest(hashes) != provenance['response_hash_map_sha256']:
        raise ValueError('Saved response collection checksum mismatch')
    result, _, _ = analyze(json.loads((archive / 'data/test-v1/inputs.json').read_text()),
                          json.loads((archive / 'data/test-v1/annotations.json').read_text())['records'],
                          [json.loads(p.read_text()) for p in paths])
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'aggregate-results.json').open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    receipt = {'source_input_sha256': provenance['source_input_sha256'],
               'response_hash_map_sha256': canonical_digest(hashes), 'response_count': len(paths),
               'analysis_code_sha256': digest(Path(__file__)),
               'output_sha256': digest(out / 'aggregate-results.json'), 'external_spend_usd': 0}
    with (out / 'reproduction-receipt.json').open('x') as handle:
        json.dump(receipt, handle, indent=2)
        handle.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    reproduce(args.archive, args.out)
