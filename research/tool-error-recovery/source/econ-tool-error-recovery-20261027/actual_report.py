"""Audit and report saved pilot evidence once; no solver or grader invocation."""
import argparse,datetime,hashlib,json,subprocess
from pathlib import Path
from analyze import summarize,ARMS,CONDITIONS

HERE=Path(__file__).resolve().parent
NODE='/Users/muditgurnani/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'

def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def require(b,m):
 if not b:raise ValueError(m)
def pct(x):return 'unavailable' if x is None else f'{100*x:.1f}%'
def secondary_metrics(rr,cc):
 settled=cc.get('settled_nano_usd',0)/1e9;reserve=cc.get('pending_nano_usd',0)/1e9;success=sum(r['passed'] is True for r in rr);missing=sum(r['passed'] is None for r in rr)
 return {'assigned':40,'terminal_complete':sum(r['completion']=='complete' for r in rr),'missing_outcomes':missing,'code_present':sum(r.get('final_code_present',False) for r in rr),'syntax_valid':sum(r.get('final_code_syntactically_valid') is True for r in rr),'syntax_unknown_with_code':sum(r.get('final_code_present',False) and r.get('final_code_syntactically_valid') is None for r in rr),'calls':sum(r['calls'] for r in rr),'revisions':sum(r['revisions'] for r in rr),'explicit_reruns':sum(r['explicit_reruns'] for r in rr),'automatic_verifications':sum(r['automatic_verifications'] for r in rr),'evaluator_executions':sum(r['evaluator_count'] for r in rr),'evaluator_seconds':sum(r['evaluator_seconds'] for r in rr),'invalid_outputs':sum(r['invalid_outputs'] for r in rr),'api_settled_usd':settled,'api_reserved_usd':reserve,'success_per_api_usd_lower':success/(settled+reserve) if settled+reserve else None,'success_per_api_usd_upper':(success+missing)/settled if settled else None,'efficiency_zero_settled_denominator':'unbounded_or_undefined' if not settled else None,'first_fail_final_pass':sum(r['first_actual_passed'] is False and r['passed'] is True for r in rr),'first_report_differs':sum(r['first_report_differs'] is True for r in rr),'first_verdict_differs':sum(r['first_verdict_differs'] is True for r in rr)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--actual',action='store_true',required=True);ap.parse_args()
 for n in ['ACTUAL-AUDIT.json','ANALYSIS.json','REPORT.md']:require(not (HERE/n).exists(),'refusing report overwrite')
 require((HERE/'COLLECTION-COMPLETE.json').exists() or (HERE/'HOLD.json').exists(),'collector has no terminal marker')
 release=load(HERE/'RELEASE.json');require(release.get('accepted') is True,'release unaccepted')
 for f,pin in release['files'].items():require(h(HERE/f)==pin,'release pin changed: '+f)
 data=load(HERE/'RESULTS.json');schedule=load(HERE/'SCHEDULE.json');tasks=load(HERE/'TASKS.json')['selected_rows'];bytask={r['task_id']:r for r in tasks};bysched={r['task_id']:r for r in schedule}
 require(data['assigned_tasks']==40 and data['assigned_arms']==120 and len(data['results'])==120,'planned denominator mismatch')
 rows=[];pins={};calls=set()
 def evidence(f):
  full=(HERE/f).resolve();require(full.is_relative_to(HERE),'evidence path escapes workstream');pins[f]=h(full);return load(full)
 for r in data['results']:
  tid=r['task_id'];require(tid in bysched and r['condition']==bysched[tid]['condition'] and r['arm'] in ARMS,'row identity')
  require(r['observation'] in ('observed','missing'),'observation status')
  if r['observation']=='missing':require(r['passed'] is None,'missing not null')
  else:
   require(type(r['passed']) is bool,'observed score type')
   if r['final_grade_path']:
    g=evidence(r['final_grade_path']);require(g['status'] in ('pass','fail') and r['passed']==(g['status']=='pass') and g['task_id']==tid,'final grade binding')
    cf=(HERE/r['final_candidate_path']).resolve();require(cf.is_relative_to(HERE),'candidate path');pins[r['final_candidate_path']]=h(cf);require(g['solution_sha256']==h(cf),'final candidate binding')
   else:require(r['passed'] is False and not r['final_code_present'],'no-candidate scoring')
  require(r['calls']<=4,'call ceiling')
  if r['observation']=='observed':require(r['calls']>=1 or r['stop_reason']=='input_limit','observed without a model attempt')
  for a in r.get('actions',[]):
   if a.get('call_consumed',True) and a.get('action') not in ('input_limit','pending'):
    require(a['call_id'] not in calls,'duplicate action call');calls.add(a['call_id'])
   if a.get('action_path'):evidence(a['action_path'])
  for e in r.get('evaluations',[]):
   if e.get('grade_path') and (HERE/e['grade_path']).exists():evidence(e['grade_path'])
   if e.get('report_path') and (HERE/e['report_path']).exists():evidence(e['report_path'])
  if r.get('first_actual_grade_path'):
   g=evidence(r['first_actual_grade_path']);require(r['first_actual_passed']==(g['status']=='pass'),'first grade binding')
  rows.append({**r,'domain':bytask[tid]['domain'],'completed':r.get('completion')=='complete'})
 # This imports only local pure accounting code. No provider/SDK calls.
 js="import {inspectCosts} from './audit-costs.mjs'; console.log(JSON.stringify(inspectCosts(process.cwd())));"
 costs=json.loads(subprocess.check_output([NODE,'--input-type=module','-e',js],cwd=HERE));account=costs['totals'];pins.update(costs['pins'])
 require(account['settled_nano_usd']==data['settled_nano_usd'] and account['pending_nano_usd']==data['pending_nano_usd'],'accounting ledger mismatch')
 require(account['reserved_attempts']==data['calls'],'reserved attempt reconciliation')
 require(account['physical_post_intents']+account['known_undispatched']+account['uncertain_dispatch']==data['calls'],'dispatch state reconciliation')
 action_ids={a['call_id'] for r in rows for a in r.get('actions',[]) if a.get('call_consumed',True) and a.get('action')!='input_limit'}
 require(set(c['call_id'] for c in account['calls'])<=action_ids,'accounted attempt absent from actions')
 require(account['settled_nano_usd']+account['pending_nano_usd']+data['infrastructure_reserve_nano_usd']<=30e9,'pilot budget exceeded')
 summary=summarize(rows,40,bootstrap=True)
 if data['collection_status']!='complete':summary['pilot_gate']['decision']='infrastructure_incomplete_no_main_authority'
 summary.update(accounting=account,resource_closures=data['resource_closures'],infrastructure_actual_usd=data['actual_infrastructure_usd'],infrastructure_reserve_usd=data['infrastructure_reserve_nano_usd']/1e9,human_codex_costs='unmeasured',collection_status=data['collection_status'])
 secondary={}
 for arm in ARMS:
  secondary[arm]=secondary_metrics([r for r in rows if r['arm']==arm],account['by_arm'].get(arm,{}))
 summary['secondary']=secondary
 summary['descriptive_domains']={d:{a:sum(r['passed'] is True for r in rows if r['domain']==d and r['arm']==a) for a in ARMS}|{'assigned_tasks':sum(t['domain']==d for t in tasks)} for d in sorted({t['domain'] for t in tasks})}
 for n in ['RESULTS.json','EVENTS.jsonl','RELEASE.json','SCHEDULE.json','TASKS.json','actual_report.py','audit-costs.mjs','analyze.py']:
  pins[n]=h(HERE/n)
 lines=['# Tool-error recovery — pilot results','',f"Coverage: {sum(r['observation']=='observed' for r in rows)}/120 task-arm outcomes observed across 40 assigned tasks. Decision: **{summary['pilot_gate']['decision']}**.",'','Primary success is passing all official hidden tests, on all assigned tasks. Below are paired assigned-condition results; unknown infrastructure outcomes remain explicit.','', '| Assigned condition | A | B | C | B−A | C−A | C−B |','|---|---:|---:|---:|---:|---:|---:|']
 for c,s in summary['strata'].items():
  arms=[f"{s['arms'][a]['successes']}/{s['arms'][a]['assigned']} ({pct(s['arms'][a]['success_lower'])}); missing {s['arms'][a]['missing']}" for a in ARMS]
  diffs=[f"{100*v['difference']:+.1f} pp" if v['difference'] is not None else f"[{100*v['lower']:+.1f}, {100*v['upper']:+.1f}] pp bounds" for v in s['contrasts']]
  lines.append('| '+' | '.join([c,*arms,*diffs])+' |')
 lines+=['','All15 paired comparisons and their20,000-draw95% percentile intervals are retained in ANALYSIS.json. Pilot intervals are descriptive and not multiplicity-adjusted; this pilot is not pooled into a main run. Recovery uses the assigned misleading-success and stale-test-report rows above. Realised erroneous exposure and first-fail→final-pass counts below are descriptive only.','', '| Arm | Terminal complete | Syntax-valid final code | Unknown syntax with code | Calls | Revisions | Requested reruns | Automatic verification | Tool executions | Tool seconds | Settled API USD | API reserve USD |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for a,s in secondary.items():lines.append('| '+' | '.join(map(str,[a,f"{s['terminal_complete']}/40",f"{s['syntax_valid']}/40",s['syntax_unknown_with_code'],s['calls'],s['revisions'],s['explicit_reruns'],s['automatic_verifications'],s['evaluator_executions'],round(s['evaluator_seconds'],2),s['api_settled_usd'],s['api_reserved_usd']]))+' |')
 lines+=['',f"Settled API total: ${account['settled_nano_usd']/1e9:.8f}; unresolved API reserve: ${account['pending_nano_usd']/1e9:.8f}. Infrastructure actual invoice amount is {data['actual_infrastructure_usd']}; keep the separate $4 infrastructure reserve until reconciliation. Placeholder-cache/setup/synthetic-check executions and host overhead are included in infrastructure, not assigned to an arm's model spend. Human/Codex-session cost is unmeasured.",'','Terminal completion means the workflow reached an observed endpoint; it is distinct from syntactically valid final code. Ordinary no-code/syntax failures still count as failures in primary success. Input, output, reasoning and cached tokens, provider latency, per-arm success-per-dollar bounds, domains and descriptive exposure/transition counts are in ANALYSIS.json. Reasoning tokens are already included in output tokens. Provider latency is not total wall time.','', 'A qualifying pilot contrast authorizes only the previously conditional main after a fresh combined cost check within $50. A ceiling/floor or no qualifying contrast ends this experiment. No task replacement, warning tuning or paid reruns are authorized.','', 'Scope: GPT-6 Luna medium on this public benchmark and these programmed reporting errors. Stale test report does not test stale files generally. Training contamination remains possible. Successful recovery does not prove awareness. Independent actual-result review remains pending; no article-worthiness conclusion is made before that review.']
 audit={'accepted':True,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'assigned_arms':120,'observed_arms':sum(r['observation']=='observed' for r in rows),'verified_files':len(pins),'files':pins,'accounting':account,'no_execution_or_provider_calls':True,'independent_actual_review_pending':True}
 for n,obj in [('ACTUAL-AUDIT.json',audit),('ANALYSIS.json',summary)]:
  with (HERE/n).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
 with (HERE/'REPORT.md').open('x') as f:f.write('\n'.join(lines)+'\n')
 print(json.dumps({'audit':'accepted','observed':audit['observed_arms'],'assigned':120,'gate':summary['pilot_gate']['decision'],'settled_api_usd':account['settled_nano_usd']/1e9,'pending_api_usd':account['pending_nano_usd']/1e9}))
if __name__=='__main__':main()
