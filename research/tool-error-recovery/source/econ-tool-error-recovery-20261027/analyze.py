"""Fixed assigned-condition paired analysis. No models/network/task execution.

Input to summarize is one row per assigned task-arm, with true final success
(bool or None for infrastructure-unknown), completion, condition and domain.
No exposed-only denominator is used for progression. CLI adapter added against
reviewed runtime schema before collection; the statistical functions are pure.
"""
from collections import Counter
import random

ARMS=('A','B','C')
CONDITIONS=('clean','test-tool execution error','misleading success','stale test report')
PAIRS=(('B','A'),('C','A'),('C','B'))
SEED=2026102807
DRAWS=20000


def metrics(rows):
    n=len(rows); successes=sum(r['passed'] is True for r in rows)
    missing=sum(r['passed'] is None for r in rows)
    completed=sum(r.get('completed') is True for r in rows)
    return dict(assigned=n,successes=successes,known_failures=n-successes-missing,
                missing=missing,success_lower=successes/n if n else None,
                success_upper=(successes+missing)/n if n else None,
                completed=completed,completion=completed/n if n else None)


def contrast(rows,hi,lo):
    tasks={r['task_id'] for r in rows}
    by={(r['task_id'],r['arm']):r for r in rows}
    differences=[];lower=[];upper=[];counts=Counter()
    for t in sorted(tasks):
        a,b=by[t,hi]['passed'],by[t,lo]['passed']
        lower.append(int(a is True)-int(b is not False))
        upper.append(int(a is not False)-int(b is True))
        if a is not None and b is not None:
            differences.append(int(a)-int(b));counts[f'{int(a)}{int(b)}']+=1
    n=len(tasks)
    return dict(contrast=hi+'-'+lo,assigned_pairs=n,observed_pairs=len(differences),
                difference=sum(differences)/n if len(differences)==n else None,
                lower=sum(lower)/n,upper=sum(upper)/n,
                discordant_hi_only=counts['10'],discordant_lo_only=counts['01'])


def paired_bootstrap(rows,hi,lo,seed=SEED,draws=DRAWS):
    if any(r['passed'] is None for r in rows):return None
    by={(r['task_id'],r['arm']):r for r in rows}
    groups={c:sorted({r['task_id'] for r in rows if r['condition']==c}) for c in CONDITIONS}
    differences=[[int(by[t,hi]['passed'])-int(by[t,lo]['passed']) for t in ts] for ts in groups.values() if ts]
    rng=random.Random(seed);n=sum(map(len,differences));values=[]
    for _ in range(draws):
        values.append(sum(sum(rng.choices(v,k=len(v))) for v in differences)/n)
    values.sort()
    # Nearest-rank percentile endpoints, frozen before data.
    return dict(lower=values[int(.025*(draws-1))],upper=values[int(.975*(draws-1))],
                draws=draws,seed=seed,method='task-paired within-assigned-condition stratified percentile bootstrap')


def summarize(rows,expected_tasks=40,bootstrap=False):
    if len(rows)!=expected_tasks*3:raise ValueError('all assigned task-arm rows required')
    if len({(r['task_id'],r['arm']) for r in rows})!=len(rows):raise ValueError('duplicate task-arm')
    ts={r['task_id'] for r in rows}
    if len(ts)!=expected_tasks:raise ValueError('task count')
    if any(r['arm'] not in ARMS or r['condition'] not in CONDITIONS or r['passed'] not in (True,False,None) for r in rows):raise ValueError('row schema')
    for t in ts:
        same=[r for r in rows if r['task_id']==t]
        if {r['arm'] for r in same}!=set(ARMS) or len({r['condition'] for r in same})!=1:raise ValueError('pairing')
    result={'assigned_tasks':expected_tasks,'assigned_arms':len(rows),'strata':{}}
    for i,c in enumerate(('overall',)+CONDITIONS):
        sub=rows if c=='overall' else [r for r in rows if r['condition']==c]
        if not sub:raise ValueError('empty condition')
        cs=[]
        for j,(hi,lo) in enumerate(PAIRS):
            v=contrast(sub,hi,lo)
            if bootstrap:v['bootstrap95']=paired_bootstrap(sub,hi,lo,SEED+i*10+j)
            cs.append(v)
        result['strata'][c]={'arms':{a:metrics([r for r in sub if r['arm']==a]) for a in ARMS},'contrasts':cs}
    overall=result['strata']['overall']['arms']
    allknown=all(v['missing']==0 for v in overall.values())
    ceiling=all(v['success_lower']>.90 for v in overall.values())
    floor=all(v['success_upper']<.10 for v in overall.values())
    qualifying=[{'stratum':c,**v} for c,s in result['strata'].items() for v in s['contrasts'] if v['lower']>=.10-1e-12]
    possible=[{'stratum':c,**v} for c,s in result['strata'].items() for v in s['contrasts'] if v['upper']>=.10-1e-12]
    decision='stop_near_ceiling' if ceiling else 'stop_near_floor' if floor else 'eligible_for_main_cost_check' if allknown and qualifying else 'stop_no_qualifying_difference' if not possible else 'infrastructure_incomplete_no_main_authority'
    result['pilot_gate']={'decision':decision,'near_ceiling':ceiling,'near_floor':floor,'coverage_complete':allknown,'qualifying_assigned_contrasts':qualifying,'no_cost_approval_implied':True}
    result['recovery_strata']=['misleading success','stale test report']
    result['claim_limits']=['Public benchmark only; possible training exposure.','Final success does not establish awareness.','Exposure and first-fail transitions descriptive only.','Pilot not pooled into any main.','No significance selection; all contrasts disclosed.']
    return result
