"""Post-study descriptive diagnostic. No model calls, reranking, or tuning."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'diagnostic-input.json'
ORIGINAL_SUMMARY_SHA256 = 'a15fa1d7d746ecb32ebfb122a54c4bbcbb878a7e8b2f76b7199d19f9b920d0be'
EXPECTED = 'b5b43f8e0fcfb6e8aa33e0aa050f19560854aee210be4742ee672dad9c3bce90'


def diagnose(rows, selected):
    ids = {r['id'] for r in rows}
    assert len(ids) == len(rows) and selected <= ids
    bad = {r['id'] for r in rows if r['grade'] == 'numerical_mismatch'}
    good = {r['id'] for r in rows if r['grade'] == 'match'}
    mandatory = {r['id'] for r in rows if not r['usable']}
    warned = {r['id'] for r in rows if r['usable'] and r['warnings']}
    quiet = ids - mandatory - warned
    assert not (mandatory & warned) and mandatory <= selected
    def count(group):
        return dict(total=len(group), mismatches=len(group & bad), matches=len(group & good),
                    selected=len(group & selected), selected_mismatches=len(group & selected & bad),
                    selected_matches=len(group & selected & good))
    result = {name: count(group) for name, group in
              [('all',ids),('mandatory',mandatory),('warned',warned),('no_warning',quiet)]}
    result['warning_coverage_of_all_mismatches'] = len(warned & bad)/len(bad) if bad else None
    result['warning_or_mandatory_coverage_of_all_mismatches'] = len((warned|mandatory)&bad)/len(bad) if bad else None
    result['warned_mismatch_capture'] = len(warned & bad & selected)/len(warned & bad) if warned & bad else None
    result['warning_precision'] = len(warned & bad)/len(warned) if warned else None
    result['warning_types'] = {w: count({r['id'] for r in rows if r['usable'] and w in r['warnings']})
                               for w in ['arithmetic','evidence','unused']}
    assert sum(result[k]['mismatches'] for k in ['mandatory','warned','no_warning']) == len(bad)
    assert sum(result[k]['selected_mismatches'] for k in ['mandatory','warned','no_warning']) == len(bad & selected)
    return result


def fixtures():
    rows = [dict(id='a',grade='numerical_mismatch',usable=True,warnings=['evidence']),
            dict(id='b',grade='match',usable=True,warnings=['arithmetic']),
            dict(id='c',grade='numerical_mismatch',usable=True,warnings=[]),
            dict(id='d',grade='numerical_mismatch',usable=False,warnings=[]),
            dict(id='e',grade='abstention',usable=False,warnings=[])]
    d = diagnose(rows, {'a','b','d','e'})
    assert d['warning_coverage_of_all_mismatches'] == 1/3
    assert d['warning_or_mandatory_coverage_of_all_mismatches'] == 2/3
    assert d['warned_mismatch_capture'] == 1 and d['warning_precision'] == .5
    assert d['mandatory']['selected_mismatches'] == 1 and d['warned']['selected_matches'] == 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    output = args.output.absolute()
    if output.exists() or any(p.is_symlink() for p in (output,*output.parents)):
        raise ValueError('fresh non-symlink output required')
    fixtures()
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED
    source = json.loads(raw)
    rows = [r for r in source['coverage'] if r['included_common_set']]
    assert len(rows) == 3768
    cells = []
    for cell in source['cells']:
        selected = set(cell['point_estimates']['20']['policies']['verification']['review_ids'])
        subset = [r for r in rows if (r['dataset'],r['model']) == (cell['dataset'],cell['model'])]
        assert len(subset) == cell['N']
        result = diagnose(subset,selected)
        assert result['all']['selected_mismatches'] == cell['point_estimates']['20']['policies']['verification']['numerical_mismatches_caught']
        cells.append(dict(dataset=cell['dataset'],model=cell['model'],**result))
    result = dict(source_sha256=ORIGINAL_SUMMARY_SHA256, input_sha256=EXPECTED, analysis='post-study descriptive, not preregistered; frozen queues unchanged',
                  definitions='Any warning means usable response with arithmetic/evidence/unused warning; mandatory unusable responses reported separately. Warning types overlap. False alarms mean answer-key matches, not proof of harmless reasoning.',
                  external_spend_usd=0,cells=cells)
    with output.open('x') as f:
        json.dump(result,f,indent=2)
        f.write('\n')
    print(json.dumps(result,indent=2))
