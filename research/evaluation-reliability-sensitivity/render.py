"""Render the saved sensitivity results as a local review, without simulation."""
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COLORS = {"row_fixed": "#a04738", "context_fixed": "#37698a", "context_adjusted": "#247468"}
LABELS = {"row_fixed": "Approach 1 · questions independent, one check",
          "row_peek": "Approach 2 · questions independent, five checks",
          "context_fixed": "Approach 3 · related questions, one check",
          "context_peek": "Approach 4 · related questions, five checks",
          "context_adjusted": "Approach 5 · related questions, five adjusted checks",
          "integrity_adjusted": "Approach 6 · adjusted checks and record checks"}


def pct(x):
    return f"{100*x:.2f}%"


def switch_rate(result, method):
    rates = result["methods"][method]["rates"]
    # Exactly one of these events can be a switch for a fixed truth/threshold.
    return rates["correct_ship" if result["truth_class"] == "switch_worthy" else "false_ship"]


def figure(panels, xfn, xlabel, ylabel, ymax=100):
    width, height = 1020, 385
    gap, left, right, top, bottom = 65, 62, 20, 57, 66
    panelwidth = (width-left-right-gap*(len(panels)-1))/len(panels)
    plotheight = height-top-bottom
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(ylabel)}" style="font-family:Arial,sans-serif;background:#fff">']
    for index, (title, rows, ticks) in enumerate(panels):
        offset = left+index*(panelwidth+gap)
        xmin, xmax = min(ticks), max(ticks)
        xx = lambda v: offset+(v-xmin)/(xmax-xmin)*panelwidth
        yy = lambda v: top+plotheight*(1-v/ymax)
        out.append(f'<text x="{offset}" y="24" font-size="16" font-weight="600" fill="#202827">{html.escape(title)}</text>')
        for k in range(5):
            value = ymax*k/4
            out.append(f'<path d="M {offset} {yy(value)} H {offset+panelwidth}" stroke="#e0e6e3"/>')
            out.append(f'<text x="{offset-10}" y="{yy(value)+4}" text-anchor="end" font-size="12" fill="#596460">{value:g}%</text>')
        for tick in ticks:
            out.append(f'<text x="{xx(tick)}" y="{height-bottom+23}" text-anchor="middle" font-size="12" fill="#596460">{tick:g}</text>')
        out.append(f'<text x="{offset+panelwidth/2}" y="{height-11}" text-anchor="middle" font-size="13" fill="#596460">{html.escape(xlabel)}</text>')
        for method, color in COLORS.items():
            points = [(xx(xfn(r)), yy(100*switch_rate(r, method)["estimate"])) for r in rows]
            out.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in points)}" stroke="{color}" stroke-width="2.5" fill="none"/>')
            for result, (x, y) in zip(rows, points):
                rate = switch_rate(result, method)
                lo, hi = [yy(100*v) for v in rate["wilson95"]]
                out.append(f'<path d="M {x} {lo} V {hi} M {x-3} {lo} H {x+3} M {x-3} {hi} H {x+3}" stroke="{color}" opacity=".55"/>')
                title = f'{LABELS[method]}: {pct(rate["estimate"])}; interval {pct(rate["wilson95"][0])} to {pct(rate["wilson95"][1])}'
                out.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"><title>{html.escape(title)}</title></circle>')
    out.append('</svg>')
    return ''.join(out)


def main():
    results = json.loads((ROOT/"results/analysis.json").read_text())
    cells = results["cells"]
    assert len(cells) == 23
    methods = results["methods_order"]
    assert len(methods) == 6
    missing = [r for r in cells if r["cell"]["family"] == "missingness"]
    threshold = [r for r in cells if r["cell"]["family"] == "threshold"]
    related = [r for r in cells if r["cell"]["family"] == "relatedness"]
    crossings = []
    for success in (.05,.10):
        rows = sorted([r for r in missing if r['cell']['successful_grade_loss']==success],key=lambda r:r['cell']['failed_grade_loss'])
        for hurdle in (.10,.25,.50):
            index = next((i for i,r in enumerate(rows) if switch_rate(r,'row_fixed')['estimate']>hurdle),None)
            def point(r):
                return {'failure_loss':r['cell']['failed_grade_loss'], 'false_switch':switch_rate(r,'row_fixed')}
            crossings.append({'success_loss':success,'descriptive_rate_hurdle':hurdle,
                              'first_tested_crossing':point(rows[index]) if index is not None else None,
                              'previous_tested_setting':point(rows[index-1]) if index is not None and index>0 else None,
                              'maximum_tested_setting':point(rows[-1]),
                              'scope':'Tested point estimates only; no interpolated breakpoint or universal safe cutoff.'})
    (ROOT/'results/crossings.json').write_text(json.dumps(crossings,indent=2)+'\n')
    legends = ''.join(f'<span><i style="background:{color}"></i>{html.escape(LABELS[m])}</span>' for m,color in COLORS.items())
    missing_panels = [(f'Successful grades missing: {100*s:g}%',
                       sorted([r for r in missing if r["cell"]["successful_grade_loss"] == s], key=lambda r:r["cell"]["failed_grade_loss"]),
                       [5,10,20,30,40]) for s in (.05,.1)]
    threshold_panels = []
    for delta in (-.04,.02,.10):
        rows = sorted([r for r in threshold if r["cell"]["delta"] == delta],key=lambda r:r["cell"]["tau"])
        threshold_panels.append((f'True gain {delta*100:+g} points'+(' · missing grades' if delta<0 else ' · complete'), rows, [1,2,5]))
    corr = [round(100*r["cell"]["paired_difference_icc"],2) for r in related]
    related_max = max(100*switch_rate(r,m)["wilson95"][1] for r in related for m in COLORS)
    related_ymax = max(10,math.ceil(related_max/5)*5)
    figures = {
        "missingness.svg": figure(missing_panels,lambda r:100*r["cell"]["failed_grade_loss"],"Failed grades missing (%)","Incorrect switches (% of evaluations)"),
        "threshold.svg": figure(threshold_panels,lambda r:100*r["cell"]["tau"],"Required improvement (points)","Switches (% of evaluations)"),
        "relatedness.svg": figure([('True gain +2 points · complete records · threshold +2',related,corr)],lambda r:round(100*r["cell"]["paired_difference_icc"],2),"Within-group correlation of paired differences (%)","Incorrect switches (% of evaluations)",related_ymax)
    }
    for name, svg in figures.items():
        (ROOT/"results"/name).write_text(svg+'\n')
    parts = ['''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Evaluation sensitivity checks · local review</title>
<style>body{margin:0;background:#f5f5f0;color:#202827;font:17px/1.6 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:48px 24px 80px}h1{font-size:38px;line-height:1.15;letter-spacing:-1px}h2{font-size:25px;line-height:1.3}p{max-width:850px}section{background:white;border:1px solid #dbe1dc;border-radius:8px;margin:28px 0;padding:26px}svg{width:100%;height:auto}.legend{display:flex;gap:10px 24px;flex-wrap:wrap;font-size:13px}.legend i{display:inline-block;width:13px;height:3px;margin:0 7px 4px 0}.note{color:#596460;font-size:14px}table{border-collapse:collapse;font-size:13px;width:100%;font-variant-numeric:tabular-nums}th,td{padding:9px 12px;border-bottom:1px solid #e2e6e3;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}details{padding:15px 0;border-bottom:1px solid #dbe1dc}summary{cursor:pointer;font-weight:600}.scroll{overflow-x:auto}a{color:#247468}.tag{font-size:12px;text-transform:uppercase;letter-spacing:1.3px;color:#596460}</style><main><p class="tag">Exploratory robustness extension · October 17, 2026 · local review</p><h1>How sensitive are our evaluation findings?</h1><p>We varied missing grades, the improvement required to switch, and how strongly questions are related. Each setting contains 2,000 evaluations. This review shows three representative approaches; the full tables below retain all six.</p><p class="note">These settings reuse outcomes or random draws. They are paired comparisons, not 46,000 independent new experiments. Short vertical lines show pointwise 95% Monte Carlo intervals, not production-risk guarantees. Line segments connect tested settings; intermediate values were not tested.</p>''']
    panels = [
        ('Missing grades can distort the apparent advantage','missingness.svg','Incorrect switches (% of evaluations)','B is truly four points worse. Every switch is incorrect under the two-point requirement. The two panels vary the probability of losing successful grades; points vary the probability of losing failed grades. Equal-loss and reversed-loss controls are included. The separate 0%/0% control is in the full table.'),
        ('A different switching requirement changes the decision','threshold.svg','Switches (% of evaluations)','At a true +2-point gain, a switch is warranted under a one-point requirement but not under the two- or five-point requirements. Switches in the −4-point panel are always incorrect; those in the +10-point panel are correct. Do not read every downward line as a worse method.'),
        ('Relatedness changes how much independent evidence we have','relatedness.svg','Incorrect switches (% of evaluations)','The true gain equals the two-point requirement, so switches do not clear the strict hurdle. The three dependence settings correspond to approximately 4.5%, 18.0% and 40.5% within-group correlation of paired differences. This panel uses a smaller vertical range to make the differences legible.')]
    for title,name,ylabel,description in panels:
        parts.append(f'<section><h2>{title}</h2><p>{description}</p><p class="note">{ylabel}</p><div class="legend">{legends}</div>{figures[name]}</section>')
    parts.append('<h2>All settings and all six approaches</h2><p class="note">At the +2-point boundary, a correct evidence-hold means the original operational classification, not proof that the true gain is strictly below the hurdle. An inconclusive result is neither a switch nor an evidence-hold.</p>')
    for result in cells:
        c = result['cell']
        if c['family']=='missingness':
            title=f"Missing grades: failed {100*c['failed_grade_loss']:g}%, successful {100*c['successful_grade_loss']:g}%"
        elif c['family']=='threshold':
            title=f"Required improvement {100*c['tau']:g} points · true gain {100*c['delta']:+g} points"
        else:
            title=f"Relatedness h={c['h']} · correlation {100*c['paired_difference_icc']:.2f}%"
        mean=result['approach1_final_look']
        parts.append(f'<details><summary>{html.escape(title)}</summary><p class="note">True gain {100*c["delta"]:+g} points; threshold &gt;{100*c["tau"]:g} points. Missing pairs: {pct(result["missing_pair_fraction"])}. Approach 1 final-look mean: {100*mean["mean_estimate"]:+.2f} points; bias: {100*mean["bias_vs_known_delta"]:+.2f} points.</p><div class="scroll"><table><tr><th>Approach</th><th>Switch rate [95% interval]</th><th>Correct hold</th><th>Incorrect hold</th><th>Inconclusive</th><th>Mean groups used</th></tr>')
        for method in methods:
            vals=result['methods'][method]; rates=vals['rates']; rate=switch_rate(result,method)
            parts.append(f'<tr><td>{html.escape(LABELS[method])}</td><td>{pct(rate["estimate"])} [{pct(rate["wilson95"][0])}, {pct(rate["wilson95"][1])}]</td><td>{pct(rates["correct_hold"]["estimate"])}</td><td>{pct(rates["false_hold"]["estimate"])}</td><td>{pct(rates["inconclusive"]["estimate"])}</td><td>{vals["mean_intended_contexts"]:.2f}</td></tr>')
        parts.append('</table></div></details>')
    parts.append('<p><a href="analysis.json">Full numerical results and intervals</a> · <a href="../DESIGN.md">Design and limitations</a></p></main></html>')
    (ROOT/'results/REVIEW.html').write_text(''.join(parts))
    print('Rendered 3 SVG figures, REVIEW.html and descriptive crossing summaries from all 23 cells / 138 method rows.')


if __name__ == '__main__':
    main()
