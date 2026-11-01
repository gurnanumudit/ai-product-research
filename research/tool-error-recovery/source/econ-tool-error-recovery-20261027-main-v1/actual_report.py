"""Report terminal saved main evidence ONCE. Local audit only; no provider/grader."""
import argparse, datetime, hashlib, json, os, subprocess
from decimal import Decimal
from pathlib import Path
from analyze import summarize, metrics, ARMS, CONDITIONS

HERE=Path(__file__).resolve().parent
NODE='/Users/muditgurnani/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
CARRY=4091279770
INFRA=24000000000
CAP=50000000000
REPORT_SOURCES=('actual_report.py','audit-costs.mjs','analyze.py','billing-scoped.mjs','runtime-controls.mjs','runner.mjs','model-client.mjs','interaction.mjs','preflight.mjs','worker.py','test_worker.py','bootstrap.sh','requirements.txt','PROMPTS.json','PROTOCOL.md','AUTHORIZATION.json','TASKS.json','SCHEDULE.json','PLACEHOLDERS.json','DATA-PINS.json')
PROJECTION='../econ-tool-error-recovery-20261027/MAIN-COST-PROJECTION-v1.json'
PRICE='../econ-tool-error-recovery-20261027/MAIN-PRICE-CHECK-v1.json'

def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def require(b,m):
 if not b:raise ValueError(m)
def pct(x):return 'unavailable' if x is None else f'{100*x:.2f}%'
def fmt(x):return 'unknown' if x is None else f'{x:.6g}' if isinstance(x,float) else str(x)
def write_once(p,obj):
 with p.open('x') as f:
  f.write(obj if isinstance(obj,str) else json.dumps(obj,indent=2)+'\n');f.flush();os.fsync(f.fileno())

def secondary_metrics(rr,cc):
 settled=cc.get('settled_nano_usd',0)/1e9;reserve=cc.get('pending_nano_usd',0)/1e9
 success=sum(r['passed'] is True for r in rr);missing=sum(r['passed'] is None for r in rr)
 result={'assigned':len(rr),'successes':success,'terminal_complete':sum(r['completion']=='complete' for r in rr),'missing_outcomes':missing,'code_present':sum(r.get('final_code_present',False) for r in rr),'syntax_valid':sum(r.get('final_code_syntactically_valid') is True for r in rr),'syntax_invalid':sum(r.get('final_code_syntactically_valid') is False for r in rr),'syntax_unknown_with_code':sum(r.get('final_code_present',False) and r.get('final_code_syntactically_valid') is None for r in rr),'calls':sum(r['calls'] for r in rr),'revisions':sum(r['revisions'] for r in rr),'explicit_reruns':sum(r['explicit_reruns'] for r in rr),'automatic_verifications':sum(r['automatic_verifications'] for r in rr),'evaluator_executions':sum(r['evaluator_count'] for r in rr),'evaluator_seconds':sum(r['evaluator_seconds'] for r in rr),'invalid_outputs':sum(r['invalid_outputs'] for r in rr),'api_settled_usd':settled,'api_reserved_usd':reserve,'success_per_api_usd_lower':success/(settled+reserve) if settled+reserve else None,'success_per_api_usd_upper':(success+missing)/settled if settled else None,'efficiency_zero_settled_denominator':'unbounded_or_undefined' if not settled else None,'first_fail_final_pass':sum(r['first_actual_passed'] is False and r['passed'] is True for r in rr),'first_report_differs':sum(r['first_report_differs'] is True for r in rr),'first_verdict_differs':sum(r['first_verdict_differs'] is True for r in rr),'first_grade_observed':sum(r['first_actual_passed'] is not None for r in rr),'first_actual_failed':sum(r['first_actual_passed'] is False for r in rr),'first_report_comparison_unknown':sum(r['first_report_differs'] is None for r in rr)}
 for key in ('input_tokens','output_tokens','reasoning_tokens','cached_tokens','cache_write_tokens','provider_latency_ms'):
  result[key]=cc.get(key,0) if cc else 0
  result['known_'+key]=cc.get('known_'+key,0)
 for key in ('usage_known_calls','usage_unknown_calls','cache_write_unknown_calls','latency_known_calls','latency_unknown_calls'):
  result[key]=cc.get(key,0)
 return result

def render_report(summary):
 lines=['# Tool-error recovery — final main results','',f"Coverage: {sum(v['assigned']-v['missing_outcomes'] for v in summary['secondary'].values())}/720 task-arm outcomes observed across 240 assigned tasks. Collection status: **{summary['collection_status']}**.",'',
 'Primary success is passing all official hidden tests, divided by all assigned tasks. Missing outcomes are not imputed or dropped. This final main report grants no permission for another study. Pilot outcomes are not pooled into main results.','',
 '| Assigned condition | Arm | Successes / assigned | Missing | Assigned success lower–upper |','|---|---|---:|---:|---|']
 for c,s in summary['strata'].items():
  for a,m in s['arms'].items():lines.append(f"| {c} | {a} | {m['successes']}/{m['assigned']} | {m['missing']} | {pct(m['success_lower'])}–{pct(m['success_upper'])} |")
 lines+=['','All 15 paired comparisons are shown below. Intervals use 20,000 task-paired draws, stratified by assigned condition for the overall comparison, with the frozen nearest-rank 95% percentile endpoints. They are descriptive and not multiplicity-adjusted. An unavailable interval is not replaced by imputed outcomes; planned-denominator contrast bounds remain visible.','',
 '| Assigned condition | Contrast | Assigned / observed pairs | Difference (pp) | Missing-outcome bounds (pp) | Bootstrap95% interval (pp) | Draws / seed |','|---|---|---:|---:|---|---|---|']
 for c,s in summary['strata'].items():
  for v in s['contrasts']:
   ci=v.get('bootstrap95');interval=f"[{100*ci['lower']:+.2f}, {100*ci['upper']:+.2f}]" if ci else 'unavailable: missing outcomes'
   point='unavailable' if v['difference'] is None else f"{100*v['difference']:+.2f}"
   lines.append(f"| {c} | {v['contrast']} | {v['assigned_pairs']}/{v['observed_pairs']} | {point} | [{100*v['lower']:+.2f}, {100*v['upper']:+.2f}] | {interval} | {str(ci['draws'])+' / '+str(ci['seed']) if ci else 'not drawn'} |")
 lines+=['','Recovery is the same assigned-condition success endpoint in misleading success and stale test report; all six recovery contrasts are in the table above.','',
 '| Arm | Successes / assigned | Terminal complete | Code present | Syntax-valid | Syntax-invalid | Unknown syntax with code | Settled API USD | Pending API reserve USD | Success / API USD lower–upper |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
 for a,s in summary['secondary'].items():
  efficiency=f"{fmt(s['success_per_api_usd_lower'])}–{fmt(s['success_per_api_usd_upper'])}" if not s['efficiency_zero_settled_denominator'] else 'unbounded or undefined: zero settled denominator'
  lines.append('| '+' | '.join(map(str,[a,f"{s['successes']}/{s['assigned']}",f"{s['terminal_complete']}/{s['assigned']}",s['code_present'],s['syntax_valid'],s['syntax_invalid'],s['syntax_unknown_with_code'],fmt(s['api_settled_usd']),fmt(s['api_reserved_usd']),efficiency]))+' |')
 lines+=['','Terminal completion is distinct from code presence and syntactic validity. Ordinary no-code/syntax failures remain primary failures. Efficiency bounds include missing outcomes and pending API liabilities; infrastructure is shown separately, not arbitrarily allocated to arms.','',
 '| Arm | Calls | Revisions | Requested reruns | Automatic verification | Invalid outputs | Tool executions | Tool seconds |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for a,s in summary['secondary'].items():lines.append('| '+' | '.join(fmt(x) for x in [a,s['calls'],s['revisions'],s['explicit_reruns'],s['automatic_verifications'],s['invalid_outputs'],s['evaluator_executions'],s['evaluator_seconds']])+' |')
 lines+=['','| Arm | Input tokens | Output tokens | Reasoning tokens | Cache-read tokens | Cache-write tokens | Usage known / unknown calls | Provider latency ms | Latency known / unknown calls |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 for a,s in summary['secondary'].items():
  vals=[a,*[fmt(s[k]) for k in ('input_tokens','output_tokens','reasoning_tokens','cached_tokens','cache_write_tokens')],f"{s['usage_known_calls']}/{s['usage_unknown_calls']}",fmt(s['provider_latency_ms']),f"{s['latency_known_calls']}/{s['latency_unknown_calls']}"]
  lines.append('| '+' | '.join(vals)+' |')
 lines+=['','Unknown usage or latency totals are shown as unknown, not zero. Known subtotals and coverage are retained in ANALYSIS.json. Cache-write coverage is separate when receipts omit it. Reasoning is already included in output tokens. Provider latency is not client/receipt/setup wall time. Tool seconds sum observed grader executions; cache/setup/check overhead remains in infrastructure.','',
 '| Assigned condition | Arm | Assigned | First grades observed | First actual failures | Report differs | Verdict differs | Comparison unknown | First-fail → final-pass |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
 for c,arms in summary['descriptive_condition_exposure'].items():
  for a,s in arms.items():lines.append('| '+' | '.join(str(x) for x in [c,a,s['assigned'],s['first_grade_observed'],s['first_actual_failed'],s['first_report_differs'],s['first_verdict_differs'],s['first_report_comparison_unknown'],s['first_fail_final_pass']])+' |')
 f=summary['financial_audit'];t=f['terminal']
 lines+=['','Exposure comparisons and first-fail transitions are descriptive only, without exposed-only filtering. Cached feedback remains stale even when it agrees with the actual report. Domain counts are descriptive and retained in ANALYSIS.json.','',
 f"Main settled API: ${t['settled_nano_usd']/1e9:.8f}; pending API reserve: ${t['pending_nano_usd']/1e9:.8f}. Retained pilot carry: ${CARRY/1e9:.8f}; main infrastructure reserve: $24.00. Main infrastructure actual invoice: {summary['infrastructure_actual_usd']}. Human/Codex cost is unmeasured.",
 f"Combined actual + pending + retained infrastructure/carry: ${f['combined_committed_nano_usd']/1e9:.8f} / $50 cap; within cap: {f['actual_plus_pending_cap_satisfied']}. Terminal remaining-capacity forecast: ${t['whole_completion_projection_nano_usd']/1e9:.8f}; within cap: {f['remaining_forecast_cap_satisfied']}. Current per-call forecast: ${t['forecast_per_call_nano_usd']/1e9:.8f}. Every saved dispatch was checked independently against both its pre-dispatch forecast and its full next $.05 reserve.",
 'The forecast is not a worst-case bound or a completion promise. A terminal budget hold may leave the forecast over cap; that stop is reported explicitly. Neither a budget stop nor an observed contrast authorizes a new study, replacement, retry, or changed prompt.',
 f"Resource closures verified: {summary['resource_audit']['verified_closed']}/{summary['resource_audit']['recorded']} recorded hosts (12 planned); unresolved recorded closures: {summary['resource_audit']['unresolved_blocks']}.",'',
 'Scope: GPT-6 Luna medium, this public benchmark and these programmed report errors. Stale test reports do not test stale files generally. Training exposure remains possible. Final success does not establish awareness or general agent capability. Independent actual-result review remains pending.']
 return '\n'.join(lines)+'\n'

def audit_and_report(root=HERE,node=NODE):
 root=Path(root).resolve()
 for n in ('ACTUAL-AUDIT.json','ANALYSIS.json','REPORT.md','REPORT-CLAIM.json'):require(not (root/n).exists(),'refusing report overwrite/replay')
 terminal=[n for n in ('COLLECTION-COMPLETE.json','HOLD.json') if (root/n).exists()]
 require(len(terminal)==1,'collector must have exactly one terminal marker')
 write_once(root/'REPORT-CLAIM.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),'phase':'main','terminal':terminal[0],'no_replay':True})
 try:
  return _report(root,node,terminal[0])
 except Exception as error:
  write_once(root/'REPORT-HOLD.json',{'error_type':type(error).__name__,'reason':str(error),'no_replay':True})
  raise

def _report(root,node,terminal):
 pins={}
 def evidence(f):
  full=(root/f).resolve();require(full.is_relative_to(root),'evidence path escapes workstream');pins[f]=h(full);return load(full)
 release=evidence('RELEASE.json');require(release.get('accepted') is True and release.get('phase')=='main' and release.get('independent_review_accepted') is True,'independent main release required')
 for n in (*REPORT_SOURCES,PROJECTION,PRICE):require(n in release['files'],'required report/source pin missing: '+n)
 for f,pin in release['files'].items():require(h(root/f)==pin,'release pin changed: '+f);pins[f]=pin
 projection=load(root/PROJECTION)
 nano=lambda x:int(Decimal(str(x))*Decimal(10**9))
 require(nano(projection['pilot_settled_api_usd'])+nano(projection['pilot_pending_api_usd'])+nano(projection['pilot_infrastructure_reserve_usd'])==CARRY and nano(projection['infrastructure']['reserve_usd'])==INFRA and nano(projection['combined_cap_usd'])==CAP and nano(projection['forecast_per_call_usd'])==2188000,'frozen projection/carry binding')
 require(projection['main_tasks']==240 and projection['main_arms']==720 and projection['max_new_calls']==2880,'frozen projection scope')
 claim=evidence('CLAIM.json');require(claim['phase']=='main' and claim['release_sha256']==h(root/'RELEASE.json'),'collector claim/release binding')
 marker=evidence(terminal);data=evidence('RESULTS.json');schedule=evidence('SCHEDULE.json');tasks=evidence('TASKS.json')['selected_rows']
 require(data['phase']=='main' and data['assigned_tasks']==240 and data['assigned_arms']==720 and len(data['results'])==720,'planned denominator mismatch')
 require(data['collection_status']==('complete' if terminal=='COLLECTION-COMPLETE.json' else 'held'),'terminal status mismatch')
 require(len(tasks)==240 and len(schedule)==240,'task schedule count')
 bytask={r['task_id']:r for r in tasks};bysched={r['task_id']:r for r in schedule}
 require(len(bytask)==240 and len(bysched)==240 and set(bytask)==set(bysched),'task schedule identity')
 for i,r in enumerate(schedule):
  require(r['task_id']==tasks[i]['task_id'] and r['block']==i//20+1 and sorted(r['arms'])==list(ARMS),'block/order schedule')
  require('private/'+r['task_id'].split('/')[1]+'.json' in release['files'],'private data release pin missing')
 require(all(sum(r['condition']==c for r in schedule)==60 for c in CONDITIONS),'assigned condition balance')
 rows=[];action_ids=set()
 for r in data['results']:
  tid=r['task_id'];require(tid in bysched and r['condition']==bysched[tid]['condition'] and r['arm'] in ARMS and r['block']==bysched[tid]['block'],'row identity')
  require(r['observation'] in ('observed','missing'),'observation status')
  if r['completion']!='not_started':require(evidence('result-'+tid.split('/')[1]+'-'+r['arm']+'.json')==r,'individual result binding')
  cf=None
  if r['final_candidate_path']:
   cf=(root/r['final_candidate_path']).resolve();require(cf.is_relative_to(root),'candidate path');pins[r['final_candidate_path']]=h(cf)
  require(r['final_code_present']==(cf is not None),'code presence binding')
  if r['observation']=='missing':require(r['passed'] is None and r['completion'] in ('incomplete','not_started'),'missing not null')
  else:
   require(type(r['passed']) is bool and r['completion']=='complete','observed score type')
   if r['final_grade_path']:
    g=evidence(r['final_grade_path']);require(g['status'] in ('pass','fail') and r['passed']==(g['status']=='pass') and g['task_id']==tid,'final grade binding')
    require(cf and g['solution_sha256']==h(cf),'final candidate binding')
    if g['status']=='pass':require(g['passed'] is True and g['test_run_valid'] is True and g['tests_run']==g['tests_expected'] and g['tests_expected']>0,'invalid all-tests pass')
    syntax=False if g['reason']=='syntax_error' else True if g['status']=='pass' or g['reason'] in ('test_failure','import_error') else None
    require(r['final_code_syntactically_valid'] is syntax and r['final_grade_reason']==g['reason'],'syntax/reason binding')
   else:require(r['passed'] is False and not r['final_code_present'],'no-candidate scoring')
  require(type(r['calls']) is int and 0<=r['calls']<=4,'call ceiling')
  if r['observation']=='observed':require(r['calls']>=1 or r['stop_reason']=='input_limit','observed without model attempt')
  for a in r.get('actions',[]):
   if a.get('call_consumed',True) and a.get('action')!='input_limit':
    require(a['call_id'] not in action_ids,'duplicate action call');action_ids.add(a['call_id'])
   if a.get('action_path') and a.get('action')!='pending':
    saved=evidence(a['action_path']);require(all(saved.get(k)==v for k,v in a.items()),'action binding')
  for e in r.get('evaluations',[]):
   if e.get('grade_path') and (root/e['grade_path']).exists():evidence(e['grade_path'])
   if e.get('report_path') and (root/e['report_path']).exists():evidence(e['report_path'])
  for f in r.get('feedback_paths',[]):evidence(f)
  if r.get('first_treatment_report_path'):evidence(r['first_treatment_report_path'])
  if r.get('first_actual_grade_path'):
   g=evidence(r['first_actual_grade_path']);require(g['task_id']==tid and g['status'] in ('pass','fail') and r['first_actual_passed']==(g['status']=='pass'),'first grade binding')
   first=r['evaluations'][0];actual=evidence(first['report_path']);shown=evidence(r['first_treatment_report_path'])
   require(actual['status']==g['status'] and r['first_report_differs']==(actual!=shown) and r['first_verdict_differs']==(actual['status']!=shown['status']),'exposure binding')
  rows.append({**r,'domain':bytask[tid]['domain'],'completed':r['completion']=='complete'})
 # Statistical functions below remain pure and inherited; no source/model/grader execution.
 require(len({(r['task_id'],r['arm']) for r in rows})==720,'duplicate task-arm')
 js="import {inspectCosts,inspectFinancialHistory} from './audit-costs.mjs'; const c=inspectCosts(process.cwd()); console.log(JSON.stringify({...c,financial:inspectFinancialHistory(process.cwd(),c.totals)}));"
 costs=json.loads(subprocess.check_output([node,'--input-type=module','-e',js],cwd=root));account=costs['totals'];financial=costs['financial'];pins.update(costs['pins'])
 require(account['settled_nano_usd']==data['settled_nano_usd'] and account['pending_nano_usd']==data['pending_nano_usd'],'accounting ledger mismatch')
 require(account['reserved_attempts']==data['calls'],'reserved attempt reconciliation')
 require(account['physical_post_intents']+account['known_undispatched']+account['uncertain_dispatch']==data['calls'],'dispatch state reconciliation')
 require(set(c['call_id'] for c in account['calls'])<=action_ids,'accounted attempt absent from actions')
 for k,v in financial['terminal'].items():require(data[k]==v and marker[k]==v,'terminal accounting binding: '+k)
 require(data['pilot_carry_nano_usd']==CARRY and data['infrastructure_reserve_nano_usd']==INFRA,'carry/infrastructure reserve binding')
 if data['collection_status']=='complete':require(all(r['observation']=='observed' for r in rows) and financial['actual_plus_pending_cap_satisfied'] and financial['remaining_forecast_cap_satisfied'] and not financial['stopped'],'invalid complete financial/coverage status')
 events=[json.loads(x) for x in (root/'EVENTS.jsonl').read_text().splitlines() if x.strip()]
 first_model=next((e['sequence'] for e in events if e['kind']=='model_intent'),None)
 caches=[e for e in events if e['kind']=='stale_cache'];expected_stale={r['task_id'] for r in schedule if r['condition']=='stale test report'}
 require(len({e['task_id'] for e in caches})==len(caches) and all(e['task_id'] in expected_stale and e['block']==1 for e in caches),'stale cache identity')
 for e in caches:evidence(e['grade_path']);evidence(e['report_path'])
 if first_model is not None or data['collection_status']=='complete':
  cache=evidence('STALE-CACHE-COMPLETE.json');require(cache['count']==60 and cache['host']==1 and cache['experimental_calls']==0 and len(caches)==60 and all(e['sequence']<(first_model if first_model is not None else float('inf')) for e in caches),'stale cache before POST')
  require(set(cache['reports'])==expected_stale,'stale mapping')
  for e in caches:require(cache['reports'][e['task_id']]==evidence(e['report_path']),'cached report binding')
 closures=data['resource_closures'];require(len(closures)<=12 and [c['block'] for c in closures]==list(range(1,len(closures)+1)),'resource block sequence')
 recorded={c['block'] for c in closures}
 for suffix in ('DISPATCH','HOST','RESOURCE-CLOSURE'):
  require(all(int(p.name.split('-')[1]) in recorded for p in root.glob('block-*-'+suffix+'.json')),'unreported resource evidence')
 unresolved=[]
 for c in closures:
  n=c['block'];require(evidence(f'block-{n}-RESOURCE-CLOSURE.json')==c,'resource closure binding')
  if c.get('creation_dispatched'):
   d=evidence(f'block-{n}-DISPATCH.json');require(d['name']==f'econ-tool-recovery-main-v1-20261027-{n}' and d['timeout_ms']==14400000 and d['infrastructure_reserve_usd']==2,'resource dispatch bounds')
  if c.get('creation_confirmed'):
   b=evidence(f'block-{n}-HOST.json');require(b['name']==c['name'] and b['vcpus']==2 and b['memory']==4096,'resource host bounds')
  good=c.get('stopped') and c.get('deleted') and c.get('verification',{}).get('empty') is True and isinstance(c.get('billable_egress_bytes'),(int,float)) and 0<=c['billable_egress_bytes']<=2e9 and isinstance(c.get('observed_resource_cost_upper_usd'),(int,float)) and 0<=c['observed_resource_cost_upper_usd']<=2
  if not good:unresolved.append(n)
 if data['collection_status']=='complete':require(len(closures)==12 and not unresolved,'complete resource closure')
 resource={'recorded':len(closures),'verified_closed':len(closures)-len(unresolved),'unresolved_blocks':unresolved,'planned_hosts':12}
 summary=summarize(rows,240,bootstrap=True)
 summary.update(accounting=account,financial_audit=financial,resource_audit=resource,resource_closures=closures,infrastructure_actual_usd=data['actual_infrastructure_usd'],infrastructure_reserve_usd=24,pilot_carry_usd=CARRY/1e9,human_codex_costs='unmeasured',collection_status=data['collection_status'])
 summary['secondary']={a:secondary_metrics([r for r in rows if r['arm']==a],account['by_arm'].get(a,{})) for a in ARMS}
 exposure_keys=('assigned','first_grade_observed','first_actual_failed','first_report_differs','first_verdict_differs','first_report_comparison_unknown','first_fail_final_pass')
 summary['descriptive_condition_exposure']={c:{a:{k:v for k,v in secondary_metrics([r for r in rows if r['arm']==a and r['condition']==c],{}).items() if k in exposure_keys} for a in ARMS} for c in CONDITIONS}
 summary['descriptive_domains']={d:{a:metrics([r for r in rows if r['domain']==d and r['arm']==a]) for a in ARMS} for d in sorted({t['domain'] for t in tasks})}
 for n in ('EVENTS.jsonl','REPORT-CLAIM.json'):pins[n]=h(root/n)
 audit={'accepted':True,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'main','assigned_arms':720,'observed_arms':sum(r['observation']=='observed' for r in rows),'verified_files':len(pins),'files':pins,'accounting':account,'financial_audit':financial,'resource_audit':resource,'no_execution_or_provider_calls':True,'independent_actual_review_pending':True,'further_study_authorized':False}
 write_once(root/'ACTUAL-AUDIT.json',audit);write_once(root/'ANALYSIS.json',summary);write_once(root/'REPORT.md',render_report(summary))
 return audit

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--actual',action='store_true',required=True);ap.parse_args()
 audit=audit_and_report();print(json.dumps({'audit':'accepted','assigned':720,'observed':audit['observed_arms'],'further_study_authorized':False}))
if __name__=='__main__':main()
