"""Portable offline supplement for the revised calculation-warning rule.
No provider calls or input acquisition. Outputs contain aggregate results only.
"""
import argparse
from collections import Counter
from dataclasses import replace
from fractions import Fraction
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PUBLIC = HERE.parent / 'article-analysis'
spec = importlib.util.spec_from_file_location('frozen_replay', PUBLIC / 'analyze.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
from package.checker import check_response, evaluate
from package.numbers import number
from package.policies import matched_policies, PRIMARY_SEED
from package.schema import parse_response

GRID = tuple(map(Fraction, ('0', '.001', '.005', '.01')))
BUDGETS = ((5, 20), (10, 10), (20, 5), (50, 2))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def residual_scale(payload, reference):
    """Smallest t making this answer a match; rational boundary is inclusive.

Percent divided by100 and ratios use t/100 in scoring coordinates; other
answers use t. This exactly preserves the published numerical adapter.
"""
    if payload['answer'] is None:
        return None
    value = Fraction(payload['answer'])
    unit = payload['unit'].strip().lower()
    divide_percent = unit == 'percent' and not old.final_times100(reference['program'])
    if divide_percent:
        value /= 100
    error = abs(value - Fraction(str(reference['exe_ans'])))
    return error * (100 if unit == 'ratio' or divide_percent else 1)


def label_at(residual, t):
    if residual is None:
        return 'abstention'
    return 'match' if residual <= t else 'numeric_nonmatch'


def adjusted_checker(payload, report):
    """Single frozen modification, without reference answers or label access."""
    if not report.usable:
        return report, None
    values = {o['id']: number(o['value']) for o in payload['operands'] + payload['constants']}
    calculated, _ = evaluate(payload['expression'], values)
    residual = abs(calculated - number(payload['answer']))
    tolerance = Fraction('.00005') if payload['unit'].strip().lower() == 'ratio' else Fraction('.005')
    warnings = set(report.warnings) - {'arithmetic'}
    details = set(report.details) - {'arithmetic_mismatch'}
    if residual > tolerance:
        warnings.add('arithmetic')
        details.add('arithmetic_mismatch')
    return replace(report, warnings=tuple(sorted(warnings)), details=tuple(sorted(details))), residual


def all_queues(reports):
    result = {}
    previous = {}
    for percent, divisor in BUDGETS:
        policies = matched_policies(reports, budget=len(reports)//divisor,
                                    seed=PRIMARY_SEED, verification='priority')
        for name, decision in policies.items():
            require(previous.get(name, set()) <= set(decision.review_ids), 'Non-nested queue')
            previous[name] = set(decision.review_ids)
        result[percent] = policies
    return result


def summarize(residuals, t, decisions):
    labels = {i: label_at(r, t) for i, r in residuals.items()}
    counts = Counter(labels.values())
    return {'t_fraction': str(t), 't_decimal': float(t), 'counts': dict(counts),
            'budgets': [{'review_percent': pct, 'policies': {
                name: old.metrics(labels, d) for name, d in policies.items()}}
                for pct, policies in decisions.items()]}


def breakpoint_intervals(residuals, decisions, limit=Fraction('.01')):
    """All right-continuous step intervals; labels change at <= boundary.

Detailed steps include every observed residual within range. Sign runs merge
adjacent steps only for the same sign, preserving all leads/ties/reversals.
"""
    points = sorted({Fraction(0), limit} | {r for r in residuals.values() if r is not None and 0 <= r <= limit})
    result = {}
    for pct, policies in decisions.items():
        c, v = map(lambda n: set(policies[n].review_ids), ('confidence', 'verification_priority'))
        steps = []
        for j, t in enumerate(points):
            mismatches = {i for i, r in residuals.items() if r is not None and r > t}
            delta = len(c & mismatches) - len(v & mismatches)
            steps.append({'left': str(t), 'right': str(points[j+1]) if j+1 < len(points) else str(limit),
                          'right_inclusive': j+1 == len(points),
                          'confidence_minus_verification': delta,
                          'sign': 'confidence' if delta > 0 else 'verification' if delta < 0 else 'tie'})
        runs = []
        for row in steps:
            if runs and runs[-1]['sign'] == row['sign']:
                runs[-1]['right'] = row['right']
                runs[-1]['right_inclusive'] = row['right_inclusive']
                runs[-1]['delta_min'] = min(runs[-1]['delta_min'], row['confidence_minus_verification'])
                runs[-1]['delta_max'] = max(runs[-1]['delta_max'], row['confidence_minus_verification'])
            else:
                runs.append({'left': row['left'], 'right': row['right'],
                             'right_inclusive': row['right_inclusive'], 'sign': row['sign'],
                             'delta_min': row['confidence_minus_verification'],
                             'delta_max': row['confidence_minus_verification']})
        deltas = [x['confidence_minus_verification'] for x in steps]
        result[str(pct)] = {'steps': steps, 'sign_intervals': runs,
                            'nonmonotonic_delta': any(a < b for a,b in zip(deltas,deltas[1:]))
                            and any(a > b for a,b in zip(deltas,deltas[1:]))}
    return result

def difference_chart(breakpoints):
    colors = {'5':'#a34b29','10':'#236b60','20':'#655a9d','50':'#595953'}
    low = min(r['confidence_minus_verification'] for b in breakpoints.values() for r in b['steps'])
    high = max(r['confidence_minus_verification'] for b in breakpoints.values() for r in b['steps'])
    bound = max(10, ((max(abs(low),abs(high))+9)//10)*10)
    x = lambda t: 80+float(Fraction(t))/.01*680
    y = lambda v: 260-v/bound*160
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 480" role="img" aria-labelledby="title desc">',
             '<title id="title">Which rule catches more mismatches as the numerical allowance changes?</title>',
             '<desc id="desc">Confidence minus verification mismatch catches. Positive favors confidence; negative favors verification. Original queues remain fixed. Allowance scale is unit dependent.</desc>',
             '<rect width="820" height="480" fill="#faf9f5"/>',
             '<g font-family="sans-serif" fill="#202421"><text x="25" y="28" font-size="19">The ranking depends on what counts as a mismatch</text>',
             '<text x="25" y="50" font-size="13">Confidence − verification: extra mismatches selected at the same review budget</text>']
    for t in (-bound, -bound//2, 0, bound//2, bound):
        parts.append(f'<line x1="80" x2="760" y1="{y(t)}" y2="{y(t)}" stroke="{"#222" if t == 0 else "#ddd"}"/><text x="68" y="{y(t)+5}" text-anchor="end" font-size="12">{t:+d}</text>')
    for t in GRID:
        parts.append(f'<text x="{x(t)}" y="440" text-anchor="middle" font-size="13">{float(t):g}</text>')
    for j,(pct, data) in enumerate(breakpoints.items()):
        points = []
        for row in data['steps']:
            points += [(x(row['left']), y(row['confidence_minus_verification'])),
                       (x(row['right']), y(row['confidence_minus_verification']))]
        coords = ' '.join(f'{a:.4f},{b:.4f}' for a,b in points)
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{colors[pct]}" stroke-width="2"/>')
        lx = 90+j*175
        parts.append(f'<line x1="{lx}" x2="{lx+22}" y1="76" y2="76" stroke="{colors[pct]}" stroke-width="3"/><text x="{lx+28}" y="80" font-size="13">{pct}% reviewed</text>')
    parts.append('<text x="420" y="467" text-anchor="middle" font-size="12">Numerical allowance t (percent: points; ratio: t/100; other units: t)</text></g></svg>')
    return '\n'.join(parts)


def analyze(inputs, refs, responses):
    original, _, decisions = old.analyze(inputs, refs, responses)
    inputs, refs, responses = map(old.keyed, (inputs, refs, responses))
    residuals, reports, adjusted, audits = {}, [], [], []
    unit_counts = Counter()
    for identity, item in inputs.items():
        payload = parse_response(old.response_text(responses[identity]['response']))
        ref = refs[identity]['original_reference']
        residual = residual_scale(payload, ref)
        residuals[identity] = residual
        unit = payload['unit'].strip().lower() or '(abstention)'
        unit_counts[unit] += 1
        report = check_response(item, payload)
        changed, calculation_residual = adjusted_checker(payload, report)
        require(report.usable == changed.usable and report.mandatory_reasons == changed.mandatory_reasons and report.confidence == changed.confidence,
                'Non-arithmetic checker property changed')
        require(set(report.warnings)-{'arithmetic'} == set(changed.warnings)-{'arithmetic'}, 'Other warnings changed')
        reports.append(report)
        adjusted.append(changed)
        audits.append({'id':identity, 'unit':unit, 'score_residual_t_fraction':str(residual) if residual is not None else None,
                      'calculation_residual_fraction':str(calculation_residual) if calculation_residual is not None else None,
                      'published_label':label_at(residual, Fraction('.005')),
                      'original_warnings':list(report.warnings), 'adjusted_warnings':list(changed.warnings),
                      'usable':report.usable})
    published_labels = {i:label_at(r, Fraction('.005')) for i,r in residuals.items()}
    require(Counter(published_labels.values()) == {'match':765,'numeric_nonmatch':347,'abstention':15}, 'Sweep anchor failed')
    sweep = [summarize(residuals, t, decisions) for t in GRID]
    require(sweep[2]['budgets'] == original['results'], 'Published sweep metrics not reproduced')
    for row in sweep:
        row['unit_counts'] = {unit:dict(Counter(label_at(residuals[a['id']], Fraction(row['t_fraction'])) for a in audits if a['unit']==unit)) for unit in sorted(unit_counts)}
    adjusted_decisions = all_queues(adjusted)
    checker_results = []
    for pct, policies in adjusted_decisions.items():
        for name in ('confidence','random'):
            require(policies[name] == decisions[pct][name], 'Confidence or random queue changed')
        require(policies['verification_priority'].mandatory_ids == decisions[pct]['verification_priority'].mandatory_ids,
                'Mandatory review set changed')
        before, after = map(lambda d:set(d.review_ids), (decisions[pct]['verification_priority'],policies['verification_priority']))
        entered, left = after-before, before-after
        checker_results.append({'review_percent':pct, 'original':old.metrics(published_labels, decisions[pct]['verification_priority']),
                                'adjusted':old.metrics(published_labels, policies['verification_priority']),
                                'confidence':old.metrics(published_labels, policies['confidence']),
                                'overlap':len(before & after), 'entered_count':len(entered), 'left_count':len(left),
                                'entered_labels':dict(Counter(published_labels[i] for i in entered)),
                                'left_labels':dict(Counter(published_labels[i] for i in left))})
    removed = [a for a in audits if 'arithmetic' in a['original_warnings'] and 'arithmetic' not in a['adjusted_warnings']]
    added = [a for a in audits if 'arithmetic' not in a['original_warnings'] and 'arithmetic' in a['adjusted_warnings']]
    require(not added, 'Relaxation unexpectedly added warnings')
    breakpoints = breakpoint_intervals(residuals, decisions)
    result = {'scope':'Exploratory same-batch follow-up, no fresh validation or financial materiality claim',
              'N':len(residuals), 'seed':PRIMARY_SEED, 'external_spend_usd':0, 
              'units':dict(unit_counts), 'allowance_definition':'percent: t percentage points; ratio: t/100; other stated units: t; inclusive boundary',
              'grid':sweep,  'checker_adjustment':checker_results,
              'warning_diagnostic':{'original_arithmetic_count':sum('arithmetic' in r.warnings for r in reports),
                                    'adjusted_arithmetic_count':sum('arithmetic' in r.warnings for r in adjusted),
                                    'removed_count':len(removed), 'removed_labels':dict(Counter(a['published_label'] for a in removed)),
                                    'added_count':len(added)},
              'original_strict5_at20':original['strict5_sensitivity_at_20_percent']}
    return result


def reproduce(archive, out):
    archive = Path(archive).resolve()
    out = old.fresh_destination(Path(out), archive)
    provenance = json.loads((PUBLIC / 'provenance.json').read_text())
    def verify():
        for rel, expected in provenance['source_input_sha256'].items():
            require(old.digest(archive / rel) == expected, 'Historical input checksum mismatch: ' + rel)
        for rel, expected in provenance['implementation_sha256'].items():
            require(old.digest(old.IMPLEMENTATION / rel) == expected, 'Implementation checksum mismatch: ' + rel)
        paths = sorted((archive / 'runs/test-01').glob('*-response.json'))
        hashes = {p.name: old.digest(p) for p in paths}
        require(old.canonical_digest(hashes) == provenance['response_hash_map_sha256'],
                'Saved response collection checksum mismatch')
        return paths
    paths = verify()
    inputs = json.loads((archive / 'data/test-v1/inputs.json').read_text())
    refs = json.loads((archive / 'data/test-v1/annotations.json').read_text())['records']
    responses = [json.loads(p.read_text()) for p in paths]
    original, _, _ = old.analyze(inputs, refs, responses)
    require(original == json.loads((PUBLIC / 'aggregate-results.json').read_text()),
            'Historical aggregate replay differs')
    result = analyze(inputs, refs, responses)
    require(result == json.loads((HERE / 'aggregate-results.json').read_text()),
            'Published follow-up aggregate replay differs')
    verify()
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'aggregate-results.json').open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    receipt = {'source_input_sha256': provenance['source_input_sha256'],
               'response_hash_map_sha256': provenance['response_hash_map_sha256'],
               'response_count': len(paths), 'external_spend_usd': 0,
               'code_sha256': old.digest(Path(__file__)),
               'aggregate_sha256': old.digest(out / 'aggregate-results.json'),
               'historical_and_followup_aggregates_verified': True}
    with (out / 'reproduction-receipt.json').open('x') as f:
        json.dump(receipt, f, indent=2)
        f.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    reproduce(args.archive, args.out)
