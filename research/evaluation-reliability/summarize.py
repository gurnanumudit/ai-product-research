"""Prespecified descriptive analysis of saved Phase1 decisions; no simulation."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

EVENTS = ('false_ship', 'false_hold', 'correct_ship', 'correct_hold',
          'correct_decision', 'false_decision', 'inconclusive')
CONTRASTS = (('context_fixed','row_fixed'), ('row_peek','row_fixed'),
             ('context_peek','context_fixed'), ('context_adjusted','context_peek'),
             ('integrity_adjusted','context_adjusted'))
Z95 = 1.959963984540054


def wilson(k, n):
    p, z2 = k/n, Z95**2
    center = (p+z2/(2*n))/(1+z2/n)
    half = Z95*math.sqrt(p*(1-p)/n+z2/(4*n*n))/(1+z2/n)
    return [0.0 if k == 0 else max(0., center-half),
            1.0 if k == n else min(1., center+half)]


def paired_interval(total, squares, n):
    mean = total/n
    variance = (squares-total*total/n)/(n-1)
    if variance > 0:
        half = Z95*math.sqrt(variance/n)
        label = 'approximate_paired_indicator_normal'
    else:
        half = math.sqrt(2*math.log(2/.05)/n)
        label = 'conservative_Hoeffding_degenerate_fallback'
    return {'difference':mean, 'interval95':[max(-1.,mean-half),min(1.,mean+half)],
            'interval_method':label, 'material_point_change_5pp':abs(mean)>=.05}


def event_vector(decision, worthwhile):
    correct = decision != 'inconclusive' and (decision == 'ship') == worthwhile
    wrong = decision != 'inconclusive' and not correct
    return dict(false_ship=int(decision == 'ship' and not worthwhile),
                false_hold=int(decision == 'hold' and worthwhile),
                correct_ship=int(decision == 'ship' and worthwhile),
                correct_hold=int(decision == 'hold' and not worthwhile),
                correct_decision=int(correct), false_decision=int(wrong),
                inconclusive=int(decision == 'inconclusive'))


def summarize(run_dir, output_path):
    run_dir, output_path = Path(run_dir), Path(output_path)
    if output_path.exists():
        raise FileExistsError('Preserve prior analysis; refusing overwrite')
    manifest = json.loads((run_dir/'manifest.json').read_text())
    n = manifest['cohorts_per_world']
    assert n == 2000 and len(manifest['worlds']) == 15
    methods = tuple(manifest['methods']) + ('forced_row_fixed',)
    specs = {f"w{x['index']:02d}_{x['mechanism']}":x for x in manifest['worlds']}
    assert len(specs) == 15
    counts = {w:{m:Counter() for m in methods} for w in specs}
    paired = {w:{f'{a}-minus-{b}':{e:[0,0] for e in ('false_decision','correct_decision','inconclusive')}
                 for a,b in CONTRASTS} for w in specs}
    looks = {w:{m:Counter() for m in methods} for w in specs}
    diagnostics = {w:Counter() for w in specs}
    identities = set()
    content_hash = hashlib.sha256()
    with gzip.open(run_dir/'decisions.jsonl.gz','rb') as handle:
        for raw in handle:
            content_hash.update(raw)
            row = json.loads(raw)
            w, i = row['world_id'], row['cohort_index']
            assert w in specs and 0 <= i < n and (w,i) not in identities
            identities.add((w,i))
            worthwhile = specs[w]['delta'] > manifest['tau']
            assert set(row['methods']) == set(manifest['methods'])
            assert [x['intended_contexts'] for x in row['looks']] == manifest['looks']
            vectors = {}
            for method in methods:
                if method == 'forced_row_fixed':
                    decision, used, reason = row['forced_row_fixed'], 200, 'operational_recoding'
                    expected = row['methods']['row_fixed']['decision']
                    assert decision == ('hold' if expected == 'inconclusive' else expected)
                else:
                    item = row['methods'][method]
                    decision, used, reason = item['decision'], item['decision_contexts'], item['reason']
                assert decision in ('ship','hold','inconclusive') and used in manifest['looks']
                assert not method.endswith('_fixed') or used == 200
                assert decision != 'inconclusive' or used == 200
                vectors[method] = event_vector(decision, worthwhile)
                counts[w][method].update(vectors[method])
                counts[w][method]['cohorts'] += 1
                counts[w][method]['contexts_consumed'] += used
                if decision == 'inconclusive':
                    key = 'integrity_inconclusive' if reason.startswith('integrity_') else 'statistical_inconclusive'
                    counts[w][method][key] += 1
                looks[w][method][str(used)] += 1
            for a,b in CONTRASTS:
                for event in paired[w][f'{a}-minus-{b}']:
                    x = vectors[a][event] - vectors[b][event]
                    acc = paired[w][f'{a}-minus-{b}'][event]
                    acc[0] += x
                    acc[1] += x*x
            end = row['looks'][-1]['diagnostics']
            for key in ('intended_pairs','observed_joined_rows','unique_observed_pairs',
                        'missing_pairs','duplicate_extra_rows','available_contexts','zero_observation_contexts'):
                diagnostics[w][key] += end[key]
            for m in ('row_fixed','context_fixed'):
                value = row['methods'][m]['interval']['mean']
                if value is not None:
                    diagnostics[w][m+'_terminal_mean_sum'] += value
                    diagnostics[w][m+'_terminal_mean_count'] += 1
    assert len(identities) == 30000
    original = json.loads((run_dir/'summary.json').read_text())
    worlds_out = []
    for w,spec in specs.items():
        method_outputs = {}
        for m in methods:
            counter = counts[w][m]
            assert counter['cohorts'] == n
            assert sum(counter[e] for e in ('false_ship','false_hold','correct_decision','inconclusive')) == n
            for event in ('false_ship','false_hold','correct_ship','correct_hold','inconclusive'):
                assert original['counts'][w][m].get(event,0) == counter[event]
            method_outputs[m] = {
                'counts':dict(counter),
                'rates':{e:{'estimate':counter[e]/n,'wilson95':wilson(counter[e],n)}
                         for e in EVENTS+('integrity_inconclusive','statistical_inconclusive')},
                'mean_contexts_consumed':counter['contexts_consumed']/n,
                'context_consumption_distribution':dict(looks[w][m]),
                'useful_point_criterion':None if spec['delta']==manifest['tau'] else
                    counter['false_decision']/n<=.05 and counter['correct_decision']/n>=.70,
            }
        diag = dict(diagnostics[w])
        diag['missing_fraction'] = diag['missing_pairs']/diag['intended_pairs']
        for m in ('row_fixed','context_fixed'):
            diag[m+'_mean_estimate'] = diag[m+'_terminal_mean_sum']/diag[m+'_terminal_mean_count']
            diag[m+'_bias_vs_known_delta'] = diag[m+'_mean_estimate']-spec['delta']
        worlds_out.append({'world_id':w,'spec':spec,'methods':method_outputs,
                           'paired_contrasts':{name:{e:paired_interval(*acc,n) for e,acc in events.items()}
                                               for name,events in paired[w].items()},
                           'terminal_data_diagnostics':diag})
    out = {'schema':'phase1-analysis-v1','cohorts_per_world':n,'distinct_cohorts':30000,
           'decisions_uncompressed_sha256':content_hash.hexdigest(),
           'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'protocol_sha256':manifest['protocol_sha256'],
           'caveats':['Known-law stress test, not empirical product prevalence.',
                      'Normal inference and nondegenerate paired MC contrasts are approximate.',
                      'Intervals are pointwise Monte Carlo descriptions, not simultaneous guarantees.',
                      'Operational forced holds are not evidence of no worthwhile benefit.'],
           'worlds':worlds_out}
    output_path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    return out


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: summarize.py RUN_DIR NEW_OUTPUT_JSON')
    result = summarize(sys.argv[1],sys.argv[2])
    print(json.dumps({'worlds':len(result['worlds']), 'cohorts':result['distinct_cohorts'],
                      'decisions_uncompressed_sha256':result['decisions_uncompressed_sha256']}))
