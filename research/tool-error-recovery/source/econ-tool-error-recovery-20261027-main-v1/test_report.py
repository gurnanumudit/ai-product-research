import hashlib,json,re,shutil,tempfile,unittest
from pathlib import Path
from actual_report import audit_and_report,secondary_metrics,REPORT_SOURCES,PROJECTION,PRICE,NODE,CARRY,INFRA
HERE=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x))
def snapshot():return dict(calls=0,settled_nano_usd=0,pending_nano_usd=0,pilot_carry_nano_usd=CARRY,infrastructure_reserve_nano_usd=INFRA,forecast_per_call_nano_usd=2188000,largest_observed_main_call_nano_usd=0,remaining_call_capacity=2880,whole_completion_projection_nano_usd=34392719770,next_physical_reserve_total_nano_usd=28141279770)
def row(i,a,complete=True):
 return dict(task_id=f'BigCodeBench/{900000+i}',condition=('clean','test-tool execution error','misleading success','stale test report')[i//60],arm=a,block=i//20+1,passed=False if complete else None,observation='observed' if complete else 'missing',completion='complete' if complete else 'not_started',final_code_present=False,final_code_syntactically_valid=None,final_grade_reason=None,final_candidate_path=None,final_grade_path=None,first_actual_grade_path=None,first_treatment_report_path=None,calls=0,revisions=0,explicit_reruns=0,automatic_verifications=0,evaluator_count=0,evaluator_seconds=0,invalid_outputs=0,first_actual_passed=None,first_report_differs=None,first_verdict_differs=None,actions=[],evaluations=[],feedback_paths=[],stop_reason='input_limit' if complete else None)
def fixture(parent,complete=True):
 root=Path(parent)/'workstreams'/'invented-main';root.mkdir(parents=True)
 tasks=[dict(task_id=f'BigCodeBench/{900000+i}',domain='invented',instruct_prompt='Invented synthetic task only') for i in range(240)]
 orders=('ABC','ACB','BAC','BCA','CAB','CBA')
 schedule=[dict(task_id=t['task_id'],condition=row(i,'A')['condition'],arms=list(orders[i%6]),block=i//20+1) for i,t in enumerate(tasks)]
 for n in REPORT_SOURCES:save(root/n,{'synthetic':True})
 for n in ('actual_report.py','audit-costs.mjs','analyze.py','billing-scoped.mjs'):shutil.copy2(HERE/n,root/n)
 save(root/'TASKS.json',{'selected_rows':tasks});save(root/'SCHEDULE.json',schedule)
 save(root/PROJECTION,json.loads((HERE/PROJECTION).read_text()));save(root/PRICE,{'synthetic_price':True})
 names=[*REPORT_SOURCES,PROJECTION,PRICE]
 for t in tasks:
  n='private/'+t['task_id'].split('/')[1]+'.json';save(root/n,{'invented':True});names.append(n)
 release={'accepted':True,'phase':'main','independent_review_accepted':True,'files':{n:digest(root/n) for n in names}}
 save(root/'RELEASE.json',release);save(root/'CLAIM.json',{'phase':'main','release_sha256':digest(root/'RELEASE.json')})
 rr=[row(i,a,complete) for i in range(240) for a in 'ABC']
 if complete:
  for r in rr:save(root/f"result-{r['task_id'].split('/')[1]}-{r['arm']}.json",r)
 closures=[];events=[dict(sequence=1,kind='claim',**snapshot())]
 if complete:
  reports={}
  for t in schedule:
   if t['condition']!='stale test report':continue
   n='stale-'+t['task_id'].split('/')[1];g=n+'.grade.json';r=n+'.report.json';report={'status':'fail','feedback':'NotImplementedError: invented placeholder'}
   save(root/g,{'task_id':t['task_id'],'status':'fail'});save(root/r,report);reports[t['task_id']]=report
   events.append(dict(sequence=len(events)+1,kind='stale_cache',task_id=t['task_id'],block=1,grade_path=g,report_path=r,elapsed_seconds=.1))
  save(root/'STALE-CACHE-COMPLETE.json',dict(count=60,host=1,experimental_calls=0,reports=reports))
  for n in range(1,13):
   name=f'econ-tool-recovery-main-v1-20261027-{n}'
   c=dict(block=n,name=name,creation_dispatched=True,creation_confirmed=True,stopped=True,deleted=True,verification={'empty':True},billable_egress_bytes=1,observed_resource_cost_upper_usd=.1,infrastructure_reserve_usd=2)
   save(root/f'block-{n}-RESOURCE-CLOSURE.json',c);save(root/f'block-{n}-DISPATCH.json',dict(name=name,timeout_ms=14400000,infrastructure_reserve_usd=2));save(root/f'block-{n}-HOST.json',dict(name=name,vcpus=2,memory=4096));closures.append(c)
 marker='COLLECTION-COMPLETE.json' if complete else 'HOLD.json';save(root/marker,dict(**snapshot(),assigned_arms=720))
 events.append(dict(sequence=len(events)+1,kind='collection_complete' if complete else 'hold',**snapshot()))
 (root/'EVENTS.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
 save(root/'RESULTS.json',dict(phase='main',assigned_tasks=240,assigned_arms=720,results=rr,collection_status='complete' if complete else 'held',resource_closures=closures,actual_infrastructure_usd=None,**snapshot()))
 return root

class Tests(unittest.TestCase):
 def test_terminal_is_not_syntax(self):
  s=secondary_metrics([row(i,'A') for i in range(240)],{});self.assertEqual(s['terminal_complete'],240);self.assertEqual(s['syntax_valid'],0);self.assertEqual(s['assigned'],240)
 def test_efficiency_missing_bounds(self):
  rr=[row(i,'A') for i in range(240)];rr[0]['passed']=True;rr[1]=row(1,'A',False)
  s=secondary_metrics(rr,dict(settled_nano_usd=10**9,pending_nano_usd=50000000));self.assertEqual(s['success_per_api_usd_upper'],2);self.assertAlmostEqual(s['success_per_api_usd_lower'],1/1.05)
 def test_unknown_usage_not_zero(self):
  s=secondary_metrics([row(0,'A',False)],dict(input_tokens=None,known_input_tokens=17,usage_unknown_calls=1,provider_latency_ms=None));self.assertIsNone(s['input_tokens']);self.assertEqual(s['known_input_tokens'],17);self.assertIsNone(s['provider_latency_ms']);self.assertIsNone(s['success_per_api_usd_upper'])
 def test_complete_invented240_report_all15_intervals_and_exclusive_once(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(d);audit=audit_and_report(root,NODE);self.assertEqual(audit['observed_arms'],720);self.assertFalse(audit['further_study_authorized'])
   report=(root/'REPORT.md').read_text();ci=[l for l in report.splitlines() if re.search(r'\| (B-A|C-A|C-B) \|',l)]
   self.assertEqual(len(ci),15);self.assertTrue(all('20000 /' in l for l in ci));self.assertIn('Cache-write tokens',report);self.assertIn('Success / API USD',report);self.assertIn('First-fail → final-pass',report)
   analysis=json.loads((root/'ANALYSIS.json').read_text());self.assertNotIn('pilot_gate',analysis);self.assertEqual(analysis['resource_audit']['verified_closed'],12)
   before=digest(root/'REPORT.md')
   with self.assertRaisesRegex(ValueError,'overwrite/replay'):audit_and_report(root,NODE)
   self.assertEqual(digest(root/'REPORT.md'),before)
 def test_held_incomplete_all720_preserved_and_no_imputation(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(d,False);a=audit_and_report(root,NODE);self.assertEqual(a['observed_arms'],0)
   analysis=json.loads((root/'ANALYSIS.json').read_text());m=analysis['strata']['overall']['arms']['A'];self.assertEqual(m['missing'],240);self.assertEqual((m['success_lower'],m['success_upper']),(0,1));self.assertIsNone(analysis['strata']['overall']['contrasts'][0]['bootstrap95'])
   self.assertIn('unavailable: missing outcomes',(root/'REPORT.md').read_text())
 def test_no_terminal_no_claim_or_real_report(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(d,False);(root/'HOLD.json').unlink()
   with self.assertRaisesRegex(ValueError,'terminal marker'):audit_and_report(root,NODE)
   self.assertFalse((root/'REPORT-CLAIM.json').exists());self.assertFalse((root/'REPORT.md').exists())
 def test_tampered_source_fails_once_and_cannot_replay(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(d,False);(root/'analyze.py').write_text('tamper')
   with self.assertRaisesRegex(ValueError,'pin changed'):audit_and_report(root,NODE)
   self.assertTrue((root/'REPORT-HOLD.json').exists())
   with self.assertRaisesRegex(ValueError,'overwrite/replay'):audit_and_report(root,NODE)
 def test_resource_closure_binding_rejects_changed_saved_closure(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(d);p=root/'block-1-RESOURCE-CLOSURE.json';c=json.loads(p.read_text());c['deleted']=False;save(p,c)
   with self.assertRaisesRegex(ValueError,'resource closure binding'):audit_and_report(root,NODE)
 def test_held_unreported_resource_cannot_be_hidden(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(d,False);save(root/'block-1-DISPATCH.json',{'synthetic':True})
   with self.assertRaisesRegex(ValueError,'unreported resource evidence'):audit_and_report(root,NODE)
 def test_held_unresolved_recorded_resource_is_disclosed(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(d,False);c={'block':1,'closure_unknown':True,'infrastructure_reserve_usd':2}
   save(root/'block-1-RESOURCE-CLOSURE.json',c);p=root/'RESULTS.json';v=json.loads(p.read_text());v['resource_closures']=[c];save(p,v)
   a=audit_and_report(root,NODE);self.assertEqual(a['resource_audit']['unresolved_blocks'],[1]);self.assertEqual(a['resource_audit']['verified_closed'],0)
 def test_snapshot_carry_tampering_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=fixture(d,False);p=root/'RESULTS.json';v=json.loads(p.read_text());v['pilot_carry_nano_usd']=0;save(p,v)
   with self.assertRaisesRegex(ValueError,'accounting binding'):audit_and_report(root,NODE)
if __name__=='__main__':unittest.main()
