"""Offline evaluator-only assembly from supplied source-first/revision records.

Safe-output adaptation, not an automatic source reviewer or label repair tool.
Historical fractional powers remain restricted to their original index guards
AND original first-pass/input/gold hashes. All rational cases retain the original
arithmetic, rendering, reference diagnostic and scoring tolerance conventions.
"""
import argparse
import ast
import json
import re
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import final_io

HISTORICAL_SOURCE_SCRIPT_SHA = 'e155e88bcd5a2d118961c8c294f2500de5b582e91edd65a744cef98343b58933'
HISTORICAL_PINS = {
    'source-first-decisions.jsonl': '76a8071f1c61e8554eb231b387f28ecfee8be1a9bb144df4e6ba671b7dcba354',
    'inputs.json': 'e34f6857ce9f41756d0d4dbb27a3b5d90895f03165177566fbd988a29cc99c06',
    'gold.json': '77ce6f0182928fcd271ef024576eee8948970652ca0dc8551bc1756f1a1c602e'
}
CAGR_INDICES = {685, 923, 1098}  # Historical qualification guards, not general model logic.
REQUIRED = ('source/test.json', 'source-first-decisions.jsonl', 'SOURCE-FIRST-FREEZE.json',
            'inputs.json', 'gold.json', 'selection.json', 'source-review-revisions.json',
            'reference-review-notes.json')

def rational(expression):
    tree = ast.parse(expression, mode='eval')
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return Fraction(ast.get_source_segment(expression, node))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            x = visit(node.operand)
            return -x if isinstance(node.op, ast.USub) else x
        if isinstance(node, ast.BinOp):
            a,b = visit(node.left),visit(node.right)
            if isinstance(node.op, ast.Add): return a+b
            if isinstance(node.op, ast.Sub): return a-b
            if isinstance(node.op, ast.Mult): return a*b
            if isinstance(node.op, ast.Div): return a/b
        raise ValueError('Unapproved rational expression node')
    return visit(tree.body)

def decimal_fraction(x, precision=60):
    with localcontext() as ctx:
        ctx.prec = precision
        return Decimal(x.numerator)/Decimal(x.denominator)

def target(i, expression):
    if '**' not in expression:
        x = rational(expression)
        return format(decimal_fraction(x), 'f'), {'method':'exact_rational', 'numerator':str(x.numerator),'denominator':str(x.denominator)}
    if i not in CAGR_INDICES:
        raise ValueError('Fractional power not authorized at this row index')
    match = re.fullmatch(r'\((\d+(?:\.\d+)?)/100\)\*\*\(1/5\)-1',expression)
    if not match:
        raise ValueError('Only three reviewed positive five-year CAGR forms permitted')
    def compute(precision):
        with localcontext() as ctx:
            ctx.prec=precision
            return (Decimal(match[1])/Decimal(100))**(Decimal(1)/Decimal(5))-1
    a,b=compute(80),compute(100)
    if abs(a-b) >= Decimal('1e-70'):
        raise ValueError('Fractional-power precision agreement failed')
    with localcontext() as ctx:
        ctx.prec=60
        rendered=format(+b,'f')
    return rendered, {'method':'Decimal_positive_fractional_power','formula':expression,'evaluation_precision_digits':[80,100],'agreement_absolute_bound':'1e-70','rendered_significant_digits':60,'note':'Non-rational compound annual return; not simple total-return/5. This does not modify the operational checker.'}

def comparison(i, inp, original, scoring):
    row={'i':i,'id':inp['id'],'original_answer':original.get('answer'),'original_exe_ans':original.get('exe_ans'),'original_program':original.get('program'),'comparison_not_used_for_model_scoring':True}
    if scoring is None:
        row.update(category='source_question_unresolved',note='Completed source review found no uniquely qualified target; released references do not cure missing scope, units, dates or semantics.')
        return row
    # Purely syntactic percent conversion, never selected by numerical closeness.
    prog=original.get('program','')
    ops=re.findall(r'(\w+)\(([^()]*)\)',prog)
    percent=False
    if scoring['unit']=='ratio' and ops:
        op,args=ops[-1]; args=[x.strip()for x in args.split(',')]
        percent=op=='multiply' and len(args)==2 and 'const_100' in args
    factor=Decimal('0.01') if percent else Decimal(1)
    with localcontext() as ctx:
        ctx.prec=100
        delta=Decimal(str(original['exe_ans']))*factor-Decimal(scoring['value'])
    row.update(declared_conversion_basis='Explicit final program multiply by const_100 produces percent; convert to source canonical ratio' if percent else 'No program-unit conversion inferred', comparison_factor=str(factor),same_displayed_convention_delta=str(delta))
    # Released exe_ans is rounded by dataset; this diagnostic allowance is not a scoring tolerance.
    consistent=abs(delta)<=max(Decimal(scoring['tolerance']),Decimal('0.000005')*factor)
    row.update(category='execution_consistent_with_source' if consistent else 'released_reference_disagreement_pending_source_review',note='Diagnostic agreement only; prose and program semantics remain preserved. Not a benchmark defect claim.' if consistent else 'Numerical disagreement under the annotated reporting convention; may reflect units, precision, interpretation or a genuine defect. Requires source review, not automatic repair.')
    return row

def indexed(rows, n, label):
    if not isinstance(rows, list) or any(not isinstance(r, dict) or type(r.get('i')) is not int or not 0 <= r['i'] < n for r in rows):
        raise ValueError('Invalid ' + label + ' indices')
    result = {r['i']: r for r in rows}
    if len(result) != len(rows):
        raise ValueError('Duplicate ' + label + ' indices')
    return result


def assemble(archive, binding_path, out, expected_n):
    ROOT = Path(archive)
    out = final_io.destination(out, [ROOT, Path(binding_path).parent])
    if type(expected_n) is not int or expected_n <= 0:
        raise ValueError('Positive expected row count required')
    expected = final_io.bindings(binding_path, REQUIRED)
    bodies = {name: final_io.read_bound(ROOT / name, expected[name]) for name in REQUIRED}
    if json.loads(bodies['SOURCE-FIRST-FREEZE.json'])['source_first_sha256'] != expected['source-first-decisions.jsonl']:
        raise ValueError('Source-first freeze mismatch')
    decisions = [json.loads(line) for line in bodies['source-first-decisions.jsonl'].decode().splitlines()]
    inputs = json.loads(bodies['inputs.json'])
    gold = json.loads(bodies['gold.json'])
    selected = json.loads(bodies['selection.json'])['selected']
    revisions = json.loads(bodies['source-review-revisions.json'])
    notes = indexed(json.loads(bodies['reference-review-notes.json']), expected_n, 'review note')
    rev = indexed(revisions, expected_n, 'revision')
    if any(not isinstance(rows, list) or len(rows) != expected_n for rows in (inputs, gold, selected, decisions)):
        raise ValueError('Exact complete expected frame required')
    if [d['i'] for d in decisions] != list(range(expected_n)):
        raise ValueError('Source-first order mismatch')
    ids = [r['id'] for r in inputs]
    if len(set(ids)) != expected_n or any(not isinstance(i, str) for i in ids):
        raise ValueError('Unique string input IDs required')
    if any([r['id'] for r in rows] != ids for rows in (gold, selected)):
        raise ValueError('Input/reference/selection order mismatch')
    for i, first in enumerate(decisions):
        expression = rev.get(i, {}).get('decision', {}).get('formula', first['formula'])
        if expression is not None and '**' in expression:
            if expected_n != 1127 or any(expected[key] != value for key, value in HISTORICAL_PINS.items()):
                raise ValueError('CAGR cases require the original reviewed first-pass/input/gold bindings')
    records=[]; comparisons=[]
    for i,(first,inp,g,meta)in enumerate(zip(decisions,inputs,gold,selected)):
        d=dict(first); d.update(rev.get(i,{}).get('decision',{}))
        qualified=d['formula']is not None
        evidence={k:inp['locations'][k]for k in d['evidence']}
        scoring=None; computation=None
        if qualified:
            value,computation=target(i,d['formula'])
            tolerance='0' if d.get('exact_count') else ('0.00005' if d['unit']=='ratio' else '0.005')
            scoring={'qualified':True,'value':value,'unit':d['unit'],'scale':d['scale'], 'provenance':'All-row source-first review of pinned FinQA test neutral context; '+d['reason'], 'tolerance':tolerance, 'tolerance_provenance':'Unchanged prospective reporting convention: canonical ratio ±0.00005; continuous displayed nonratio ±0.005; explicitly exact discrete counts0. Not source-measurement uncertainty or financial materiality.'}
        c=comparison(i,inp,g['original_qa'],scoring)
        if i in notes: c.update(source_review=notes[i],category=notes[i]['category'])
        comparisons.append(c)
        record={'id':inp['id'],'index':i,'question':inp['question'],'qualified':qualified,'status':'qualified'if qualified else'unresolved','source_first':first,'review_revision':rev.get(i),'adjudication':d,'sampling':meta,'source_evidence':evidence,'original_reference':g['original_qa'],'reference_reconciliation':c,'scoring':scoring,'target_computation':computation}
        records.append(record)
    summary=dict(Counter(r['status']for r in records))
    artifact={'version':1,'split':'test','review_state':'METHODS_REVIEW_PENDING','source_sha256':expected['source/test.json'],'source_first_sha256':expected['source-first-decisions.jsonl'],'inputs_sha256':expected['inputs.json'],'gold_sha256':expected['gold.json'],'selection_sha256':expected['selection.json'],'source_review_revisions_sha256':expected['source-review-revisions.json'],'qualification_scope':'Caller-supplied source-reviewed decisions; displayed-source calculations and explicit interpretations, not exact unrounded accounting truth. Unknowns remain all-planned. No model outcomes used.','summary':summary,'records':records}
    final_io.save(out/'annotations.json', artifact)
    final_io.save(out/'reference-reconciliation.json', comparisons)
    here = Path(__file__).parent
    final_io.receipt(out, {**expected, 'bindings_file': final_io.digest(binding_path)},
                     HISTORICAL_SOURCE_SCRIPT_SHA,
                     [Path(__file__), here/'final_io.py', here/'safe_output.py'])
    return artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True, help='Supplied reviewed final-test local archive')
    parser.add_argument('--bindings', type=Path, required=True, help='Explicit SHA256 map for all REQUIRED files')
    parser.add_argument('--expected-n', type=int, required=True)
    parser.add_argument('--out', type=Path, required=True, help='Fresh directory outside supplied archives')
    args = parser.parse_args()
    result = assemble(args.archive, args.bindings, args.out, args.expected_n)
    print(json.dumps({'summary': result['summary'], 'mode': 'offline_unreviewed_reproduction'}))


if __name__ == '__main__':
    main()

