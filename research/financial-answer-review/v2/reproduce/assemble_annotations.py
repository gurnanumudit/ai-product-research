"""Evaluator-only assembly from frozen source-first human/agent decisions.

No model requests, no network, no heuristic score-unit inference. Gold enters only
after the 200-row source-first pass; originals are preserved, never overwritten.
"""
import argparse
import ast
from safe_output import fresh_output
import hashlib
import json
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

SOURCE_FIRST_SHA = '94707d1d8cb97ed7dd49cfd5f0c8d8e0df1b00df193575d6ac0216602dce49d7'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def arithmetic(expression):
    """Only finite decimal literals and +,-,*,/; exact rational computation."""
    tree = ast.parse(expression, mode='eval')
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return Fraction(ast.get_source_segment(expression, node))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            val = visit(node.operand)
            return -val if isinstance(node.op, ast.USub) else val
        if isinstance(node, ast.BinOp):
            a, b = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div): return a / b
        raise ValueError('Unapproved expression node')
    return visit(tree.body)

def decimal_text(value):
    with localcontext() as ctx:
        ctx.prec = 60
        return format(Decimal(value.numerator) / Decimal(value.denominator), 'f')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True, type=Path, help='Local reviewed development archive')
    parser.add_argument('--source-first-sha256', required=True, help='Independently frozen first-pass digest')
    parser.add_argument('--out', required=True, type=Path, help='Fresh output directory outside input archive')
    args = parser.parse_args()
    ROOT = args.data_dir
    expected_sha = args.source_first_sha256
    if len(expected_sha) != 64 or any(c not in '0123456789abcdef' for c in expected_sha):
        raise ValueError('Expected a lowercase SHA256 digest')
    destination = fresh_output(args.out, ROOT)
    path = ROOT / 'source-first-decisions.jsonl'
    if sha(path) != expected_sha:
        raise ValueError('Source-first freeze mismatch')
    decisions = [json.loads(line) for line in path.read_text().splitlines()]
    inputs = json.loads((ROOT / 'inputs.json').read_text())
    gold = json.loads((ROOT / 'gold.json').read_text())
    selection = json.loads((ROOT / 'selection.json').read_text())['selected']
    if [d['i'] for d in decisions] != list(range(200)):
        raise ValueError('Exact ordered 200 source decisions required')
    if any(len(rows) != 200 for rows in (inputs, gold, selection)):
        raise ValueError('All 200 input/reference/selection records required')
    if len({row['id'] for row in inputs}) != 200:
        raise ValueError('Unique input IDs required')
    revisions_path = ROOT / 'source-review-revisions.json'
    revisions = json.loads(revisions_path.read_text()) if revisions_path.exists() else []
    by_index = {r['i']:r for r in revisions}
    comparisons = json.loads((ROOT / 'reference-reconciliation.json').read_text())
    by_comparison = {r['i']:r for r in comparisons}
    records = []
    for i, (first, inp, original, meta) in enumerate(zip(decisions, inputs, gold, selection)):
        assert inp['id'] == original['id'] == meta['id']
        d = dict(first)
        if i in by_index: d.update(by_index[i]['decision'])
        qualified = d['formula'] is not None
        record = {'id': inp['id'], 'index':i, 'question':inp['question'],
                  'qualified':qualified, 'status':'qualified' if qualified else 'unresolved',
                  'source_first':first, 'review_revision':by_index.get(i),
                  'adjudication':d, 'sampling':meta,
                  'source_evidence':{k:inp['locations'][k] for k in d['evidence']},
                  'original_reference':original['original_qa'],
                  'reference_reconciliation':by_comparison.get(i, {'category':'not_yet_reconciled'}),
                  'scoring':None}
        if qualified:
            value = arithmetic(d['formula'])
            tolerance = '0' if d.get('exact_count') else ('0.00005' if d['unit']=='ratio' else '0.005')
            record['exact_rational'] = {'numerator':str(value.numerator),'denominator':str(value.denominator)}
            record['scoring'] = {'qualified':True,'value':decimal_text(value),
                'unit':d['unit'],'scale':d['scale'],
                'provenance': 'Source-first DATA review of pinned FinQA dev neutral context; '+d['reason'],
                'tolerance':tolerance,
                'tolerance_provenance':'Prospective reporting convention fixed before responses: ratio ±0.00005; continuous displayed nonratio ±0.005; direct/integer displayed count or year exact. Not source measurement uncertainty.'}
        records.append(record)
    counts = Counter(r['status'] for r in records)
    artifact = {'version':1,'split':'dev','review_state':'METHODS_REVIEW_PENDING',
        'source_sha256':sha(ROOT/'source/dev.json'),
        'source_first_sha256':expected_sha,
        'inputs_sha256':sha(ROOT/'inputs.json'),'gold_sha256':sha(ROOT/'gold.json'),
        'selection_sha256':sha(ROOT/'selection.json'),
        'source_review_revisions_sha256':sha(revisions_path) if revisions_path.exists() else None,
        'qualification_scope':'Displayed-source arithmetic and explicitly stated interpretations; no claim of exact unrounded accounting values. Unknowns remain in all200 denominator.',
        'summary':dict(counts),'records':records}
    out = destination/'annotations.json'
    with out.open('x') as handle:
        handle.write(json.dumps(artifact,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({'counts':dict(counts),'annotations_sha256':sha(out),'bytes':out.stat().st_size}))

if __name__ == '__main__': main()
