import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {Accounting,BOUNDS,projection,admit,validateSelection,makeTransport,CONDITIONS,closureVerified} from './runtime-controls.mjs';
import {runInteraction,parseOutput,sanitizeReport} from './interaction.mjs';
import {requestBody,createClient,extract} from './model-client.mjs';
import {money,reconcile} from './billing-scoped.mjs';
import {runPilot,REQUIRED_FILES,sha,writeNew,claim,verifyRelease} from './runner.mjs';
import {validateProjection,checkPrices,accountPreflight,freshCredentials} from './preflight.mjs';
const prompts=JSON.parse(fs.readFileSync(new URL('./PROMPTS.json',import.meta.url)));
const costProjection=JSON.parse(fs.readFileSync(new URL('./PILOT-COST-PROJECTION-v1.json',import.meta.url)));
const grade=(pass=false,reason=pass?'all_tests_passed':'test_failure')=>({status:pass?'pass':'fail',passed:pass,reason,feedback:pass?'':'AssertionError: synthetic',test_run_valid:true,tests_expected:1,tests_run:1,elapsed_seconds:.01});
const output=t=>({text:t,output_status:'ok',cost_nano_usd:1000});
const row={task_id:'BigCodeBench/0',condition:'clean',block:1};
function temp(t){const d=fs.mkdtempSync(path.join(os.tmpdir(),'econ-runtime-synthetic-'));t.after(()=>fs.rmSync(d,{recursive:true,force:true}));return d;}
async function engine({arm='A',condition='clean',outputs=['def f(): return 1','{"action":"finish"}'],grades=[],staleReport={status:'fail',feedback:'placeholder traceback'},modelHook=null}={}){
 const files=new Map(),inputs=[],evals=[],events=[];let cursor=0;
 const r=await runInteraction({row:{...row,condition},arm,task:{instruct_prompt:'Synthetic task only'},prompts,staleReport,
  write:(n,v)=>files.set(n,structuredClone(v)),emit:e=>events.push(e),
  model:async a=>{inputs.push(a.input);if(modelHook)return modelHook(a,inputs.length);const v=outputs[cursor++];return typeof v==='string'?output(v):v;},
  grade:async a=>{evals.push(a);return grades[evals.length-1]??grade();}});
 return {r,files,inputs,evals,events};
}
test('all arms keep deciding after a true pass; finish is paid and final grade private',async()=>{
 for(const arm of ['A','B','C']){
  const {r,inputs,evals}=await engine({arm,grades:Array(4).fill(grade(true))});
  assert.equal(r.calls,2);assert.equal(r.stop_reason,'finish');assert.equal(r.passed,true);
  assert.equal(evals.at(-1).kind,'final');assert.equal(inputs.length,2);assert.equal(r.automatic_verifications,arm==='C'?1:0);
  assert.equal(inputs[0][0].content,prompts.baseline+(arm==='B'?'\n\n'+prompts.warning:''));
  assert.deepEqual(inputs[1].filter(m=>m.role==='system').at(-1),{role:'system',content:prompts.action});
 }
});
test('four calls include rerun/revise/round-four revision, then fresh private grade',async()=>{
 const {r,evals,files}=await engine({outputs:['bad syntax !!!','{"action":"rerun"}','{"action":"revise","code":"def f(): return 2"}','{"action":"revise","code":"def f(): return 3"}']});
 assert.equal(r.calls,4);assert.equal(r.revisions,2);assert.equal(r.explicit_reruns,1);assert.equal(evals.length,5);
 assert.equal(evals[0].code,evals[1].code);assert.equal(evals.at(-1).code,'def f(): return 3');
 assert.equal(files.get(r.feedback_paths.at(-1)).delivered_to_model,false);
});
test('round-four finish still consumes fourth call, final grade not returned',async()=>{
 const {r,evals,inputs}=await engine({outputs:['x = 1','{"action":"rerun"}','{"action":"rerun"}','{"action":"finish"}']});
 assert.equal(r.calls,4);assert.equal(r.explicit_reruns,2);assert.equal(evals.length,4);assert.equal(inputs.length,4);
});
test('four incomplete/malformed outputs are ordinary observed no-candidate failure',async()=>{
 const {r,evals}=await engine({outputs:Array.from({length:4},(_,i)=>({output_status:i%2?'malformed':'incomplete',text:''}))});
 assert.equal(r.calls,4);assert.equal(r.invalid_outputs,4);assert.equal(r.passed,false);assert.equal(r.observation,'observed');assert.equal(r.final_code_present,false);assert.equal(evals.length,0);
});
test('invalid decisions preserve candidate; no extra calls and final syntax failure identified',async()=>{
 const {r,evals}=await engine({outputs:['invalid python !','garbage',{output_status:'incomplete',text:''},'{"action":"rerun","extra":1}'],grades:Array(2).fill(grade(false,'syntax_error'))});
 assert.equal(r.invalid_outputs,3);assert.equal(r.calls,4);assert.equal(evals.length,2);assert.equal(r.final_code_present,true);assert.equal(r.final_code_syntactically_valid,false);
});
test('first valid candidate on fourth call gets C fresh independent verification and private final',async()=>{
 const {r,evals,inputs}=await engine({arm:'C',outputs:[...Array(3).fill({output_status:'incomplete',text:''}),'x=1']});
 assert.equal(r.calls,4);assert.equal(evals.length,3);assert.deepEqual(evals.map(x=>x.kind),['candidate','automatic_verification','final']);
 assert.equal(new Set(evals.map(x=>x.label)).size,3);assert.ok(evals.every(x=>x.fresh_process));assert.equal(inputs.length,4);
});
test('C compares treatment to truthful fresh first-candidate rerun, hides private true grade',async()=>{
 const {r,inputs,files,evals}=await engine({arm:'C',condition:'misleading success',grades:[grade(false),grade(false),grade(false)]});
 const f=files.get(r.feedback_paths[0]);assert.equal(f.reports.length,2);assert.equal(f.reports[0].status,'pass');assert.equal(f.reports[1].status,'fail');
 assert.equal(evals[0].code,evals[1].code);assert.equal(r.first_actual_passed,false);assert.equal(r.first_report_differs,true);
 assert.ok(!JSON.stringify(inputs).includes('misleading'));assert.ok(!JSON.stringify(inputs).includes('first_actual'));
});
test('C displays one report when sanitized objects agree and two when only feedback differs',async()=>{
 const same=await engine({arm:'C',condition:'stale test report',staleReport:{status:'fail',feedback:'AssertionError: synthetic'}});
 assert.equal(same.files.get(same.r.feedback_paths[0]).reports.length,1);assert.equal(same.r.first_report_differs,false);
 const different=await engine({arm:'C',condition:'stale test report'});
 assert.equal(different.files.get(different.r.feedback_paths[0]).reports.length,2);assert.equal(different.r.first_verdict_differs,false);
});
test('test-tool error is first-only; explicit reruns are truthful',async()=>{
 const {r,files}=await engine({condition:'test-tool execution error',outputs:['x=1','{"action":"rerun"}','{"action":"finish"}']});
 assert.equal(files.get(r.feedback_paths[0]).reports[0].status,'error');assert.equal(files.get(r.feedback_paths[1]).reports[0].status,'fail');
});
test('private final grade can disagree with prior pass without another decision',async()=>{
 const {r,inputs}=await engine({grades:[grade(true),grade(false)]});assert.equal(r.first_actual_passed,true);assert.equal(r.passed,false);assert.equal(inputs.length,2);
});
test('sanitizer removes test/assertion source lines and grade-unknown stops',()=>{
 const g=grade();g.feedback='Traceback\n  File "hidden.py", line 7\n    assert SECRET\n    ^^^^^\nAssertionError';
 assert.deepEqual(sanitizeReport(g),{status:'fail',feedback:'Traceback\n  File "hidden.py", line 7\nAssertionError'});
 assert.throws(()=>sanitizeReport({...g,status:'unknown'}));assert.throws(()=>sanitizeReport({...grade(true),tests_run:0}));
});
test('unknown final grade preserves partial metrics as missing, never cognitive failure',async()=>{
 await assert.rejects(engine({grades:[grade(),{...grade(),status:'unknown'}]}),e=>e.partialResult.observation==='missing'&&e.partialResult.passed===null&&e.partialResult.calls===2);
});
test('parse strict JSON actions and syntax-invalid code remains submitted candidate',()=>{
 for(const text of ['{"action":"delete"}','[]','{"action":"finish","code":"x"}','```json\n{"action":"finish"}\n```','{"action":"revise","code":""}'])assert.equal(parseOutput(output(text),true).action,'invalid');
 assert.equal(parseOutput(output('not valid python !!!'),false).action,'submit');
});
test('input-limit admission ends arm without consuming a call; privately grades retained code',async()=>{
 const {r,evals}=await engine({modelHook:async(a,n)=>n===1?output('x=1'):{admission:'input_limit'}});
 assert.equal(r.calls,1);assert.equal(r.stop_reason,'input_limit');assert.equal(evals.length,2);assert.equal(r.observation,'observed');assert.equal(r.actions[1].call_consumed,false);
});
test('inherited request bound, model route/tier and inclusive output tokens fixed',()=>{
 const b=requestBody([{role:'system',content:'a'}]);assert.equal(b.model,'openai/gpt-6-luna');assert.equal(b.service_tier,'default');assert.equal(b.max_output_tokens,8192);assert.deepEqual(b.providerOptions.gateway.only,['openai']);assert.equal(b.reasoning.effort,'medium');
 assert.throws(()=>requestBody('x'.repeat(60001)),/serialized_input_limit/);
});
test('integer accounting cap, 480 calls, full unresolved reserve, single settlement',()=>{
 const s=new Accounting();assert.equal(projection(s),28e9);s.reserve('a');s.hold('a',{request_dispatched:true});assert.equal(s.pendingNano,50e6);assert.throws(()=>s.reserve('b'),/stopped/);
 const a=new Accounting();a.reserve('x');assert.throws(()=>a.reserve('x'),/duplicate/);a.settle('x',100);assert.throws(()=>a.settle('x',100),/settlement/);
 for(let i=1;i<480;i++){a.reserve('c'+i);a.settle('c'+i,50e6);}assert.throws(()=>a.reserve('last'),/call limit/);
 assert.throws(()=>admit({calls:1,settledNano:3e9,pendingNano:0}),/projection/);assert.throws(()=>admit(new Accounting(),BOUNDS.admissionHostMs),/host time/);
});
test('known pre-dispatch stop releases reserve; settled overshoot counted before hold',()=>{
 const a=new Accounting();a.reserve('x');a.hold('x',{request_dispatched:false});assert.equal(a.pendingNano,0);assert.equal(a.calls,1);
 const b=new Accounting();b.reserve('y');assert.throws(()=>b.settle('y',50e6+1),/exceeds reserve/);assert.equal(b.settledNano,50e6+1);assert.equal(b.pendingNano,0);assert.equal(b.stopped,true);
});
const response=()=>({id:'gen_synthetic',model:'gpt-6-luna',status:'completed',usage:{input_tokens:10,output_tokens:5,total_tokens:15,input_tokens_details:{cached_tokens:0},output_tokens_details:{reasoning_tokens:1}},output:[{type:'message',role:'assistant',status:'completed',content:[{type:'output_text',text:'{"action":"finish"}'}]}]});
const receipt=()=>({data:{id:'gen_synthetic',total_cost:'0.0000035',is_byok:false,provider_name:'openai',model:'openai/gpt-6-luna',tokens_prompt:10,tokens_completion:5}});
test('billing preserves usage, decimals round up, partial or conflicting receipt fails',()=>{
 assert.equal(money('0.0000000001'),1);assert.throws(()=>money(null));assert.equal(reconcile(response(),receipt(),'gen_synthetic').cost_nano_usd,3500);
 assert.throws(()=>reconcile(response(),{data:{...receipt().data,tokens_completion:4}},'gen_synthetic'));
 assert.throws(()=>reconcile(response(),{data:{...receipt().data,provider_name:'other'}},'gen_synthetic'));
 const r=response();delete r.usage.output_tokens_details;assert.throws(()=>reconcile(r,receipt(),'gen_synthetic'));
});
test('client one POST, raw response/receipt and exact charge; duplicate directory cannot replay',async t=>{
 const d=temp(t),requests=[];const client=createClient({keyLoader:()=> 'SYNTHETIC_KEY',fetcher:async(u,o)=>{requests.push(o.method);return new Response(JSON.stringify(o.method==='POST'?response():receipt()),{status:200});}});
 const r=await client({input:'synthetic',outputDir:d,callId:'one'});assert.deepEqual(requests,['POST','GET']);assert.equal(r.cost_nano_usd,3500);assert.equal(r.usage.total,15);
 assert.equal(fs.existsSync(path.join(d,'one','DISPATCH.json')),true);assert.equal(fs.existsSync(path.join(d,'one','charge.json')),true);
 await assert.rejects(client({input:'synthetic',outputDir:d,callId:'one'}));assert.deepEqual(requests,['POST','GET']);
 assert.ok(!fs.readFileSync(path.join(d,'one','request.json'),'utf8').includes('SYNTHETIC_KEY'));
});
test('model transport/receipt ambiguity retains reserve and never retries POST',async t=>{
 for(const failure of ['transport','receipt','receipt_shape']){
  const d=path.join(temp(t),failure);let posts=0;const client=createClient({keyLoader:()=> 'fake',fetcher:async(u,o)=>{
   if(o.method==='POST'){posts++;if(failure==='transport')throw Error('network synthetic');return new Response(JSON.stringify(response()));}
   if(failure==='receipt')throw Error('receipt synthetic');return new Response(JSON.stringify({data:{}}));}});
  await assert.rejects(client({input:'synthetic',outputDir:d,callId:'one'}),e=>e.pending_nano_usd===50e6&&e.request_dispatched===true);assert.equal(posts,1);
 }
});
test('incomplete model response still settles its charge and is an ordinary output',async t=>{
 const client=createClient({keyLoader:()=> 'fake',fetcher:async(u,o)=>new Response(JSON.stringify(o.method==='POST'?{...response(),status:'incomplete'}:receipt()))});
 const r=await client({input:'synthetic',outputDir:temp(t),callId:'incomplete'});assert.equal(r.output_status,'incomplete');assert.equal(r.cost_nano_usd,3500);
 assert.equal(extract({...response(),output:[]}).output_status,'malformed');
});
test('SDK transport blocks mutation replay, extra host and automatic resume',async()=>{
 let sent=0;const tr=makeTransport('s',{fetcher:async()=>{sent++;return new Response('{}',{status:200});}});
 const u='https://vercel.com/api/v2/sandboxes/sessions/x/cmd',o={method:'POST',body:'{"cmd":"synthetic"}'};await tr.fetch(u,o);await assert.rejects(tr.fetch(u,o),/replay/);assert.equal(sent,1);
 await assert.rejects(tr.fetch(u+'?resume=true'),/resume/);
 const create={method:'POST',body:JSON.stringify({name:'s',timeout:14400000,persistent:false,resources:{vcpus:2},region:'iad1',image:'vercel/sandbox/python:3.14'})};
 await tr.fetch('https://vercel.com/api/v2/sandboxes',create);await assert.rejects(tr.fetch('https://vercel.com/api/v3/sandboxes',create),/second host/);
});
test('SDK ambiguous mutation returns terminal abort and cannot be replayed',async()=>{
 let n=0;const t=makeTransport('s',{fetcher:async()=>{n++;return new Response('{}',{status:503});}});
 for(let i=0;i<2;i++)await assert.rejects(t.fetch('https://vercel.com/api/v2/sandboxes/sessions/x/cmd',{method:'POST',body:'x'}));assert.equal(n,1);
});
test('projection and read-only preflight reject price/route/account drift',async()=>{
 validateProjection(costProjection);assert.throws(()=>validateProjection({...costProjection,pilot:{...costProjection.pilot,max_model_calls:481}}));
 const raw={data:{id:'openai/gpt-6-luna',endpoints:[{provider_name:'openai',status:0,context_length:200000,max_completion_tokens:8192,pricing:costProjection.pricing_per_token}]}};
 const methods=[];await checkPrices({projection:costProjection,keyLoader:()=> 'fake',fetcher:async(u,o)=>{methods.push(o.method);return new Response(JSON.stringify(raw));}});assert.deepEqual(methods,['GET']);
 raw.data.endpoints[0].pricing={...costProjection.pricing_per_token,completion:'0.1'};await assert.rejects(checkPrices({projection:costProjection,keyLoader:()=> 'fake',fetcher:async()=>new Response(JSON.stringify(raw))}),/pricing changed/);
 await assert.rejects(accountPreflight({teamId:'synthetic',token:'fake'},{fetcher:async()=>new Response('{"billing":{"plan":"free","status":"active"}}')}),/account/);
});

function fixture(t){
 const root=temp(t),home=path.join(root,'workstreams','synthetic');fs.mkdirSync(home,{recursive:true});
 const orders=['ABC','ACB','BAC','BCA','CAB','CBA'];
 const schedule=Array.from({length:40},(_,i)=>({task_id:'BigCodeBench/'+i,condition:CONDITIONS[i%4],arms:[...(i<36?orders[i%6]:['ABC','BCA','CAB','ACB'][i-36])],block:Math.floor(i/20)+1}));
 const tasks=schedule.map(r=>({task_id:r.task_id,instruct_prompt:'Synthetic only',libraries:[],domain:'synthetic'}));
 const data={'TASKS.json':{selected_rows:tasks},'SCHEDULE.json':schedule,'PROMPTS.json':prompts,'PLACEHOLDERS.json':Object.fromEntries(schedule.filter(r=>r.condition==='stale test report').map(r=>[r.task_id,'def f(*args, **kwargs): raise NotImplementedError("placeholder candidate")'])),'PILOT-COST-PROJECTION-v1.json':costProjection};
 const names=[...REQUIRED_FILES,'vendor/synthetic.py',...schedule.map(r=>'private/'+r.task_id.split('/')[1]+'.json')];
 for(const n of names){const f=path.resolve(home,n);fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,JSON.stringify(data[n]??{synthetic:true}));}
 function pin(){fs.writeFileSync(path.join(home,'RELEASE.json'),JSON.stringify({accepted:true,phase:'pilot',independent_review_accepted:true,files:Object.fromEntries(names.map(n=>[n,sha(fs.readFileSync(path.resolve(home,n)))]))}));}pin();
 const trace=[];let posts=0;
 const preflight=async()=>{trace.push('preflight');return {credentials:{synthetic:true},account:{plan:'pro',status:'active'},prices:{at:new Date().toISOString()}};};
 const priceCheck=async()=>({at:new Date().toISOString(),synthetic:true});
 const client=async({callId})=>{posts++;trace.push('model');return output(callId.endsWith('-1')?'x=1':'{"action":"finish"}');};
 const hostFactory=async({number,write})=>({elapsed:()=>0,open:async()=>trace.push('open'+number),prepare:async rows=>trace.push('prepare'+rows.length),beforeCall:async()=>{},
  grade:async a=>{trace.push(a.kind);assert.equal(a.fresh_process,true);const g=grade();write(a.label+'.grade.json',g);return g;},
  close:async()=>({block:number,stopped:true,deleted:true,verification:{empty:true},billable_egress_bytes:5,observed_resource_cost_upper_usd:.1,infrastructure_reserve_usd:2})});
 return {home,preflight,priceCheck,client,hostFactory,schedule,tasks,pin,trace,posts:()=>posts};
}
test('full synthetic120-arm pilot: all10 caches before calls, first40/second20, no reference gate',async t=>{
 const f=fixture(t);const r=await runPilot(f);assert.equal(r.collection_status,'complete');assert.equal(r.results.length,120);assert.equal(r.calls,240);assert.equal(r.infrastructure_reserve_nano_usd,4e9);assert.equal(f.posts(),240);
 assert.equal(f.trace.filter(x=>x==='stale_placeholder').length,10);assert.equal(f.trace.slice(0,f.trace.indexOf('model')).filter(x=>x==='stale_placeholder').length,10);
 assert.ok(f.trace.includes('prepare40')&&f.trace.includes('prepare20'));assert.ok(!f.trace.some(x=>x.includes('reference')));assert.equal(r.results.filter(x=>x.arm==='C').every(x=>x.automatic_verifications===1),true);
 assert.ok(r.results.every(x=>x.calls===2&&x.passed===false));await assert.rejects(runPilot(f),/already claimed/);
});
test('global transport hold retains120 denominators, unresolved reserve, no second host',async t=>{
 const f=fixture(t);const r=await runPilot({...f,client:async()=>{throw Object.assign(Error('synthetic transport'),{request_dispatched:true});}});
 assert.equal(r.collection_status,'held');assert.equal(r.results.length,120);assert.equal(r.pending_nano_usd,50e6);assert.equal(r.calls,1);
 assert.equal(r.results.filter(x=>x.completion==='incomplete').length,1);assert.equal(r.results.filter(x=>x.completion==='not_started').length,119);assert.ok(r.results.every(x=>x.passed===null));assert.ok(!f.trace.includes('open2'));
});
test('history admission happens before reserve/price/POST; input_limit continues all assignments',async t=>{
 const f=fixture(t);const r=await runPilot({...f,client:async({callId})=>output(callId.endsWith('-1')?'x'.repeat(35000):JSON.stringify({action:'revise',code:'y'.repeat(35000)}))});
 assert.equal(r.collection_status,'complete');assert.equal(r.calls,240);assert.ok(r.results.every(x=>x.stop_reason==='input_limit'&&x.calls===2&&x.actions[2].call_consumed===false));
 assert.ok(r.results.every(x=>x.final_grade_path&&x.final_code_present));assert.equal(r.pending_nano_usd,0);
});
test('preflight failure cannot claim, missing release pins cannot launch, tampered bytes fail',async t=>{
 const f=fixture(t);await assert.rejects(runPilot({...f,preflight:async()=>{throw Error('offline');}}));assert.equal(fs.existsSync(path.join(f.home,'CLAIM.json')),false);
 const r=JSON.parse(fs.readFileSync(path.join(f.home,'RELEASE.json')));delete r.files['interaction.mjs'];fs.writeFileSync(path.join(f.home,'RELEASE.json'),JSON.stringify(r));assert.throws(()=>verifyRelease(f.home),/pin missing/);
 f.pin();fs.appendFileSync(path.join(f.home,'PROTOCOL.md'),'tamper');assert.throws(()=>verifyRelease(f.home),/freeze mismatch/);
});
test('exclusive CLAIM permits exactly one collector under concurrent admission',async t=>{
 const f=fixture(t);let n=0,release;const barrier=new Promise(r=>release=r);const preflight=async()=>{const p=await f.preflight();if(++n===2)release();await barrier;return p;};
 const both=await Promise.allSettled([runPilot({...f,preflight}),runPilot({...f,preflight})]);assert.equal(both.filter(x=>x.status==='fulfilled').length,1);assert.equal(both.filter(x=>x.status==='rejected').length,1);assert.equal(f.posts(),240);
});
test('resource closure uncertainty stops before next host and retains infrastructure reserve',async t=>{
 const f=fixture(t),hf=f.hostFactory;const r=await runPilot({...f,hostFactory:async args=>({...await hf(args),close:async()=>({stopped:true,deleted:false,verification:{empty:false}})})});
 assert.equal(r.collection_status,'held');assert.equal(r.results.filter(x=>x.observation==='observed').length,60);assert.equal(r.infrastructure_reserve_nano_usd,4e9);assert.ok(!f.trace.includes('open2'));
});
test('selection checks40 unique tasks,10 assigned per condition and balanced orders',t=>{
 const f=fixture(t);validateSelection(f.tasks,f.schedule);const bad=structuredClone(f.schedule);bad[0].condition='unknown';assert.throws(()=>validateSelection(f.tasks,bad));assert.throws(()=>validateSelection(f.tasks.slice(1),f.schedule));
});
test('infrastructure closure uses egress, not multi-GB download ingress, and rejects unknown/overspend',()=>{
 const c={stopped:true,deleted:true,verification:{empty:true},billable_egress_bytes:2e9,observed_resource_cost_upper_usd:1.6632006,usage:{network_transfer:{ingress:30e9,egress:2e9}}};
 assert.equal(closureVerified(c),true);assert.equal(closureVerified({...c,billable_egress_bytes:2e9+1}),false);
 assert.equal(closureVerified({...c,billable_egress_bytes:null}),false);assert.equal(closureVerified({...c,observed_resource_cost_upper_usd:2.01}),false);
 assert.equal(closureVerified({...c,billable_egress_bytes:-1}),false);
});
test('changing release during read-only preflight cannot consume CLAIM',async t=>{
 const f=fixture(t);await assert.rejects(runPilot({...f,preflight:async()=>{
  const pre=await f.preflight(),p=path.join(f.home,'RELEASE.json'),r=JSON.parse(fs.readFileSync(p));r.extra='changed';fs.writeFileSync(p,JSON.stringify(r));return pre;
 }}),/release changed/);assert.equal(fs.existsSync(path.join(f.home,'CLAIM.json')),false);assert.equal(f.posts(),0);
});
test('existing credential renewal is narrowly preclaim, same refresh token, no scope/account changes',async()=>{
 let saved={token:'old',refreshToken:'existing-refresh',expiresAt:new Date(1)},renewals=0;
 const auth={getAuth:()=>saved,credentials:()=>({token:saved.token,teamId:'same-team',projectId:'same-project'}),
  OAuth:async()=>({refreshToken:async token=>{assert.equal(token,'existing-refresh');renewals++;return {access_token:'new',expires_in:86400};}}),
  updateAuthConfig:value=>{saved=value;}};
 const c=await freshCredentials({auth,now:()=>1000});assert.equal(c.refreshed,true);assert.equal(renewals,1);assert.equal(c.teamId,'same-team');assert.equal(c.projectId,'same-project');assert.equal(saved.refreshToken,'existing-refresh');
 const again=await freshCredentials({auth,now:()=>1000,allowRefresh:false});assert.equal(again.refreshed,false);assert.equal(renewals,1);
 saved.expiresAt=new Date(1);await assert.rejects(freshCredentials({auth,now:()=>1000,allowRefresh:false}),/after claim/);assert.equal(renewals,1);
});
test('credential renewal errors are safe and do not expose provider secrets',async()=>{
 await assert.rejects(freshCredentials({now:()=>1000,auth:{getAuth:()=>({token:'old',refreshToken:'secret',expiresAt:new Date(1)}),OAuth:async()=>({refreshToken:async()=>{throw Error('SECRET_PROVIDER_BODY');}})}}),e=>e.message==='existing_credential_renewal_failed');
});
