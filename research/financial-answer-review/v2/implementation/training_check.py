"""Read the exact prior50 training records; diagnostic only, no model rerun."""
from dataclasses import asdict
import json
from pathlib import Path
import argparse
from package.checker import check_response
from runner import digest, load_inputs, save_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, help='New non-overwriting diagnostic JSON')
    args = parser.parse_args()
    stage = Path(__file__).resolve().parents[2] / 'hq-finqa-review-policy-stage-a-20261012'
    rows = load_inputs(stage / 'data/inputs.json', 50)
    old = json.loads((stage / 'runs/pilot-01/summary.json').read_text())
    old_by_id = {r['id']: r for r in old['rows']}
    new = []
    source_hashes = {'data/inputs.json': digest(stage / 'data/inputs.json'),
                     'runs/pilot-01/summary.json': digest(stage / 'runs/pilot-01/summary.json')}
    for attempt, row in enumerate(rows, 1):
        path = stage / f'runs/pilot-01/{attempt:02d}-response.json'
        record = json.loads(path.read_text())
        if record['id'] != row['id']:
            raise ValueError('Training response order mismatch')
        source_hashes[str(path.relative_to(stage))] = digest(path)
        report = check_response(row, record['response']['choices'][0]['message']['content'])
        new.append({'id': row['id'], 'v1_checker': old_by_id[row['id']]['checker'], 'v2_checker': asdict(report)})
    save_json(args.out, {'scope': 'Training-only diagnostics; development and test unseen; not independent efficacy',
        'planned': 50, 'v1_any_concern': sum(not r['v1_checker']['usable'] or bool(r['v1_checker']['warnings']) for r in new),
        'v2_any_concern': sum(not r['v2_checker']['usable'] or bool(r['v2_checker']['warnings']) for r in new),
        'v1_mandatory': sum(not r['v1_checker']['usable'] for r in new),
        'v2_mandatory': sum(not r['v2_checker']['usable'] for r in new),
        'rows': new, 'source_hashes': source_hashes})


if __name__ == '__main__': main()
