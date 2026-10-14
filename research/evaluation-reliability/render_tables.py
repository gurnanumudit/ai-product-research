"""Render all frozen analysis cells without selecting or recomputing outcomes."""
import json
from pathlib import Path
import sys


def render(source, target):
    source, target = Path(source), Path(target)
    if target.exists():
        raise FileExistsError('Preserve prior rendered evidence')
    data = json.loads(source.read_text())
    lines = ['# All Phase 1 decision rates', '',
             'Every cell uses 2,000 simulated experiments. Rates are percentages; brackets are pointwise 95% Wilson Monte Carlo intervals. These intervals describe simulation precision, not external validity. Correct ship/hold breakdowns, integrity/statistical inconclusives, consumption distributions, and every prespecified paired contrast are in analysis.json.', '',
             'Forced row-fixed is an operational recoding, not a seventh statistical estimator: its “false hold” means a missed worthwhile change after mapping an inconclusive result to hold. It must not be interpreted as a false evidence-based claim.', '']
    for world in data['worlds']:
        lines.extend([f"## {world['world_id']}: true gain {world['spec']['delta']*100:+.0f} points", '',
                      '| Method | False ship | False hold | Correct decision | Inconclusive | Mean contexts | Point screen |',
                      '|---|---:|---:|---:|---:|---:|---|'])
        for method, values in world['methods'].items():
            cells = []
            for event in ('false_ship','false_hold','correct_decision','inconclusive'):
                rate = values['rates'][event]
                lo, hi = rate['wilson95']
                cells.append(f"{100*rate['estimate']:.2f} [{100*lo:.2f}, {100*hi:.2f}]")
            screen = values['useful_point_criterion']
            label = 'boundary: not assessed' if screen is None else 'meets' if screen else 'does not meet'
            lines.append('| ' + ' | '.join([method,*cells,f"{values['mean_contexts_consumed']:.2f}",label])+' |')
        lines.append('')
    lines.extend(['The prespecified nonboundary point screen requires false decisions at most 5% and correct decisions at least 70%. Meeting it in one world does not validate the method in other worlds; a biased method can meet it when the bias happens to favor the true answer. It is not a hypothesis test or a universal deployment recommendation.', ''])
    target.write_text('\n'.join(lines))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: render_tables.py ANALYSIS_JSON NEW_MARKDOWN_PATH')
    render(sys.argv[1], sys.argv[2])
