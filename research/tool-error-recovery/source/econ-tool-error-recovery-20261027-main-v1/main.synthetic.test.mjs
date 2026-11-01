import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {BOUNDS,Accounting,projection,nextPhysicalReserve,admit,validateSelection,CONDITIONS,closureVerified,makeTransport} from './runtime-controls.mjs';
import {runMain,REQUIRED_FILES,claim,verifyRelease,sha} from './runner.mjs';
import {freshCredentials,validateProjection,checkPrices} from './preflight.mjs';
import {requestBody} from './model-client.mjs';
const mainProjection=JSON.parse(fs.readFileSync(new URL('../econ-tool-error-recovery-20261027/MAIN-COST-PROJECTION-v1.json',import.meta.url)));
const priceRecord=JSON.parse(fs.readFileSync(new URL('../econ-tool-error-recovery-20261027/MAIN-PRICE-CHECK-v1.json',import.meta.url)));
const prompts=JSON.parse(fs.readFileSync(new URL('./PROMPTS.json',import.meta.url)));
const inherited=['model-client.mjs','billing-scoped.mjs','interaction.mjs','worker.py','test_worker.py','PROMPTS.json'];
const grade=()=>({status:'fail',passed:false,reason:'test_failure',feedback:'AssertionError: invented',test_run_valid:true,tests_expected:1,tests_run:1,elapsed_seconds:.01});
function temp(t){const d=fs.mkdtempSync(path.join(os.tmpdir(),'econ-main-synthetic-'));t.after(()=>fs.rmSync(d,{recursive:true,force:true}));return d;}
function fixture(t){
 const home=path.join(temp(t),'workstreams','synthetic-main');fs.mkdirSync(home,{recursive:true});
 const orders=['ABC','ACB','BAC','BCA','CAB','CBA'];
 const schedule=Array.from({length:240},(_,i)=>({task_id:'BigCodeBench/'+(900000+i),condition:CONDITIONS[i%4],arms:[...orders[i%6]],block:Math.floor(i/20)+1}));
 const tasks=schedule.map(r=>({task_id:r.task_id,instruct_prompt:'Invented synthetic task only',libraries:[],domain:'synthetic'}));
 const data={'TASKS.json':{selected_rows:tasks},'SCHEDULE.json':schedule,'PROMPTS.json':prompts,'PLACEHOLDERS.json':Object.fromEntries(schedule.filter(r=>r.condition==='stale test report').map(r=>[r.task_id,'def synthetic(*args, **kwargs): raise NotImplementedError("placeholder candidate")'])),
  '../econ-tool-error-recovery-20261027/MAIN-COST-PROJECTION-v1.json':mainProjection};
 const names=[...REQUIRED_FILES,'vendor/synthetic.py',...schedule.map(r=>'private/'+r.task_id.split('/')[1]+'.json')];
 for(const n of names){const f=path.resolve(home,n);fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,JSON.stringify(data[n]??{synthetic:true}));}
 function pin(phase='main'){fs.writeFileSync(path.join(home,'RELEASE.json'),JSON.stringify({accepted:true,phase,independent_review_accepted:true,files:Object.fromEntries(names.map(n=>[n,sha(fs.readFileSync(path.resolve(home,n)))]))}));}pin();
 const trace=[];let calls=0,clock=0,renewals=0,saved={token:'synthetic',refreshToken:'same-refresh',expiresAt:new Date(1)};
 const auth={getAuth:()=>saved,credentials:()=>({token:saved.token,teamId:'same-team',projectId:'same-project'}),updateAuthConfig:v=>saved=v,OAuth:async()=>({refreshToken:async t=>{assert.equal(t,'same-refresh');renewals++;return {access_token:'synthetic-renewal',expires_in:6*3600};}})};
 const preflight=async o=>{trace.push(['preflight',o.allowRefresh]);const c=await freshCredentials({allowRefresh:o.allowRefresh,auth,now:()=>clock});clock+=4*3600000;return {credentials:c,account:{plan:'pro',status:'active'},prices:{at:new Date().toISOString()}};};
 const priceCheck=async()=>({synthetic:true});
 const client=async({callId})=>{trace.push(['model',callId]);calls++;return {text:callId.endsWith('-1')?'x=1':'{"action":"finish"}',output_status:'ok',cost_nano_usd:1000};};
 const hostFactory=async({number,write})=>({elapsed:()=>0,open:async()=>trace.push(['open',number]),prepare:async rows=>trace.push(['prepare',number,rows.length]),beforeCall:async()=>{},
  grade:async a=>{trace.push([a.kind,a.task_id]);assert.equal(a.fresh_process,true);const g=grade();write(a.label+'.grade.json',g);return g;},
  close:async()=>{trace.push(['close',number]);return {block:number,stopped:true,deleted:true,verification:{empty:true},billable_egress_bytes:1,observed_resource_cost_upper_usd:1,infrastructure_reserve_usd:2};}});
 return {home,preflight,priceCheck,client,hostFactory,schedule,tasks,pin,trace,calls:()=>calls,renewals:()=>renewals};
}
test('unchanged interaction/client/billing/grader/prompts retain exact pilot bytes',()=>{
 for(const n of inherited)assert.equal(sha(fs.readFileSync(new URL(n,import.meta.url))),sha(fs.readFileSync(new URL('../econ-tool-error-recovery-20261027/'+n,import.meta.url))),n);
 function check(rel){for(const e of fs.readdirSync(new URL(rel+'/',import.meta.url),{withFileTypes:true})){const n=rel+'/'+e.name;if(e.isDirectory())check(n);else assert.equal(sha(fs.readFileSync(new URL(n,import.meta.url))),sha(fs.readFileSync(new URL('../econ-tool-error-recovery-20261027/'+n,import.meta.url))),n);}}check('vendor');
 const b=requestBody('invented');assert.equal(b.max_output_tokens,8192);assert.equal(b.reasoning.effort,'medium');assert.equal(b.service_tier,'default');assert.deepEqual(b.providerOptions.gateway.only,['openai']);assert.throws(()=>requestBody('x'.repeat(60001)),/serialized_input_limit/);
});
test('initial forecast is34.39271977 while full hard reservations exceed combined50',()=>{
 const a=new Accounting();assert.equal(projection(a),34392719770);assert.equal(nextPhysicalReserve(a),28141279770);admit(a);
 assert.ok(BOUNDS.pilotCarryNano+BOUNDS.infraNano+BOUNDS.maxCalls*BOUNDS.callReserveNano>BOUNDS.capNano);
 assert.equal(a.snapshot().remaining_call_capacity,2880);
});
test('forecast monotonically retains twice largest observed main charge',()=>{
 const a=new Accounting();a.reserve('first');a.settle('first',1500000);assert.equal(a.forecastNano,3000000);
 a.reserve('second');a.settle('second',1000);assert.equal(a.forecastNano,3000000);assert.equal(a.largestObservedNano,1500000);
 assert.equal(projection(a),4091279770+24e9+1501000+2878*3000000);
});
test('price tail raises forecast and stops after recording exact known charge once',()=>{
 const a=new Accounting();a.reserve('tail');assert.throws(()=>a.settle('tail',4e6),/forecast/);assert.equal(a.forecastNano,8e6);assert.equal(a.settledNano,4e6);assert.equal(a.pendingNano,0);assert.equal(a.stopped,true);
 a.hold('tail',{});assert.equal(a.settledNano,4e6);assert.throws(()=>a.reserve('retry'),/stopped/);
});
test('independent next physical reserve rejects a tail that fits forecast',()=>{
 const a={calls:2879,settledNano:BOUNDS.capNano-BOUNDS.pilotCarryNano-BOUNDS.infraNano-40e6,pendingNano:0,forecastNano:BOUNDS.initialForecastNano};
 assert.ok(projection(a)<BOUNDS.capNano);assert.ok(nextPhysicalReserve(a)>BOUNDS.capNano);assert.throws(()=>admit(a),/next physical reserve/);
 a.settledNano-=10e6;assert.equal(nextPhysicalReserve(a),BOUNDS.capNano);admit(a);
 a.pendingNano=1;assert.throws(()=>admit(a),/next physical reserve/);
});
test('2880 total calls, four-call model contract and exhausted tail cannot restart',()=>{
 const a=new Accounting();for(let i=0;i<2880;i++){a.reserve('c'+i);a.settle('c'+i,1000);}
 assert.equal(a.calls,2880);assert.equal(a.snapshot().remaining_call_capacity,0);assert.equal(projection(a),BOUNDS.pilotCarryNano+BOUNDS.infraNano+2880000);assert.throws(()=>a.reserve('extra'),/call limit/);assert.equal(BOUNDS.maxCallsPerArm,4);
});
test('unknown charge keeps full .05 reserve; duplicate claims/settlements cannot replay',()=>{
 const a=new Accounting();a.reserve('unknown');a.hold('unknown',{request_dispatched:true});assert.equal(a.pendingNano,50e6);assert.equal(a.snapshot().pilot_carry_nano_usd,4091279770);assert.throws(()=>a.reserve('replacement'),/stopped/);
 const b=new Accounting();b.reserve('x');assert.throws(()=>b.reserve('x'),/duplicate/);b.settle('x',1);assert.throws(()=>b.settle('x',1),/settlement/);
});
test('known above-reservation charges are recorded before stop',()=>{
 const a=new Accounting();a.reserve('x');assert.throws(()=>a.settle('x',50e6+1),/exceeds reserve/);assert.equal(a.settledNano,50e6+1);assert.equal(a.pendingNano,0);
});
test('240-task schedule enforces12 blocks,60 per condition and40 of each arm order',t=>{
 const f=fixture(t);validateSelection(f.tasks,f.schedule);assert.equal(new Set(f.schedule.map(x=>x.block)).size,12);
 const bad=structuredClone(f.schedule);bad[239].block=11;assert.throws(()=>validateSelection(f.tasks,bad),/block/);
 const badCondition=structuredClone(f.schedule);badCondition[0].condition='stale test report';assert.throws(()=>validateSelection(f.tasks,badCondition),/balance/);
 assert.throws(()=>validateSelection(f.tasks.slice(0,40),f.schedule.slice(0,40)),/count/);
});
test('main release rejects pilot phase, missing pins and tampered sources',t=>{
 const f=fixture(t);f.pin('pilot');assert.throws(()=>verifyRelease(f.home),/main release/);f.pin();
 const file=path.join(f.home,'RELEASE.json'),r=JSON.parse(fs.readFileSync(file));delete r.files['interaction.mjs'];fs.writeFileSync(file,JSON.stringify(r));assert.throws(()=>verifyRelease(f.home),/pin missing/);
 f.pin();fs.appendFileSync(path.join(f.home,'runner.mjs'),'tampered');assert.throws(()=>verifyRelease(f.home),/freeze mismatch/);
});
test('exclusive distinct main CLAIM permits a single collector and preserves pilot claim',async t=>{
 const h=temp(t),pilot=path.join(h,'pilot'),main=path.join(h,'main');fs.mkdirSync(pilot);fs.mkdirSync(main);fs.writeFileSync(path.join(pilot,'CLAIM.json'),'unchanged pilot');
 const r=await Promise.allSettled([Promise.resolve().then(()=>claim(main,'a'.repeat(64))),Promise.resolve().then(()=>claim(main,'a'.repeat(64)))]);assert.equal(r.filter(x=>x.status==='fulfilled').length,1);
 const c=JSON.parse(fs.readFileSync(path.join(main,'CLAIM.json')));assert.equal(c.phase,'main');assert.equal(c.max_hosts,12);assert.equal(c.max_model_calls,2880);assert.equal(c.pilot_carry_nano_usd,4091279770);assert.equal(fs.readFileSync(path.join(pilot,'CLAIM.json'),'utf8'),'unchanged pilot');
});
test('fresh route/forecast validation uses main records with strict unchanged prices',async()=>{
 validateProjection(mainProjection);assert.throws(()=>validateProjection({...mainProjection,pilot_infrastructure_reserve_usd:0}),/carry/);assert.throws(()=>validateProjection({...mainProjection,forecast_per_call_usd:.001}),/accounting/);
 const methods=[];await checkPrices({projection:mainProjection,priceRecord,keyLoader:()=> 'synthetic-key',fetcher:async(u,o)=>{methods.push(o.method);return new Response(JSON.stringify(priceRecord.raw));}});assert.deepEqual(methods,['GET']);
 const changed=structuredClone(priceRecord.raw);changed.data.endpoints.find(e=>e.provider_name==='openai').pricing.completion='0.01';await assert.rejects(checkPrices({projection:mainProjection,priceRecord,keyLoader:()=> 'synthetic-key',fetcher:async()=>new Response(JSON.stringify(changed))}),/pricing changed/);
});
test('resource closure requires stopped/deleted/empty and bounded billable egress',()=>{
 const c={stopped:true,deleted:true,verification:{empty:true},billable_egress_bytes:2e9,observed_resource_cost_upper_usd:1.663201,usage:{network_transfer:{ingress:30e9}}};assert.equal(closureVerified(c),true);
 assert.equal(closureVerified({...c,deleted:false}),false);assert.equal(closureVerified({...c,billable_egress_bytes:2e9+1}),false);assert.equal(closureVerified({...c,observed_resource_cost_upper_usd:null}),false);
});
test('transport continues to prohibit ambiguous mutation replay and resume',async()=>{
 let sent=0;const tr=makeTransport('econ-tool-recovery-main-v1-20261027-1',{fetcher:async()=>{sent++;return new Response('{}',{status:503});}});
 const url='https://vercel.com/api/v2/sandboxes/sessions/s/cmd',o={method:'POST',body:'synthetic'};await assert.rejects(tr.fetch(url,o));await assert.rejects(tr.fetch(url,o));assert.equal(sent,1);await assert.rejects(tr.fetch(url+'?resume=true'),/resume/);
});
test('failed preclaim preflight creates neither CLAIM nor host',async t=>{
 const f=fixture(t);await assert.rejects(runMain({...f,preflight:async()=>{throw Error('synthetic account hold');}}));assert.equal(fs.existsSync(path.join(f.home,'CLAIM.json')),false);assert.equal(f.trace.length,0);
});
test('unknown first transport keeps720 denominators,60 caches, full reserve and closes host',async t=>{
 const f=fixture(t);const r=await runMain({...f,client:async()=>{throw Object.assign(Error('synthetic'),{request_dispatched:true});}});
 assert.equal(r.collection_status,'held');assert.equal(r.results.length,720);assert.equal(r.pending_nano_usd,50e6);assert.equal(r.pilot_carry_nano_usd,4091279770);assert.equal(r.infrastructure_reserve_nano_usd,24e9);
 assert.equal(r.results.filter(x=>x.completion==='incomplete').length,1);assert.equal(r.results.filter(x=>x.completion==='not_started').length,719);assert.ok(r.results.every(x=>x.passed===null));
 assert.equal(f.trace.filter(x=>x[0]==='stale_placeholder').length,60);assert.equal(f.trace.filter(x=>x[0]==='close').length,1);assert.ok(!f.trace.some(x=>x[0]==='open'&&x[1]===2));
});
test('full synthetic main:720 rows,60 caches before POST,12 sequential closures and renewals',async t=>{
 const f=fixture(t);const r=await runMain(f);assert.equal(r.collection_status,'complete');assert.equal(r.phase,'main');assert.equal(r.results.length,720);assert.equal(r.calls,1440);assert.equal(f.calls(),1440);
 assert.equal(r.assigned_tasks,240);assert.equal(r.planned_per_condition_arm,60);assert.equal(r.infrastructure_reserve_nano_usd,24e9);assert.equal(r.pilot_carry_nano_usd,4091279770);
 assert.equal(f.trace.slice(0,f.trace.findIndex(x=>x[0]==='model')).filter(x=>x[0]==='stale_placeholder').length,60);
 assert.deepEqual(f.trace.filter(x=>x[0]==='prepare').map(x=>x[2]),[240,...Array(11).fill(20)]);assert.equal(f.renewals(),12);assert.ok(f.trace.filter(x=>x[0]==='preflight').every(x=>x[1]===true));
 for(let n=2;n<=12;n++)assert.ok(f.trace.findIndex(x=>x[0]==='close'&&x[1]===n-1)<f.trace.findIndex(x=>x[0]==='open'&&x[1]===n));
 assert.ok(r.results.every(x=>x.observation==='observed'&&x.calls===2));assert.ok(r.results.filter(x=>x.arm==='C').every(x=>x.automatic_verifications===1));assert.equal(r.resource_closures.length,12);
 const events=fs.readFileSync(path.join(f.home,'EVENTS.jsonl'),'utf8').trim().split('\n').map(JSON.parse);const intents=events.filter(e=>e.kind==='model_intent');assert.equal(intents.length,1440);assert.equal(intents[0].forecast_per_call_nano_usd,2188000);assert.ok(intents.every(e=>e.pilot_carry_nano_usd===4091279770));
 await assert.rejects(runMain(f),/already claimed/);
});

test('new dependencies preserve inherited files and cover selected official direct pins',()=>{
 for(const [saved,original] of [['bootstrap.inherited.sh','bootstrap.sh'],['requirements.inherited.txt','requirements.txt']])assert.equal(sha(fs.readFileSync(new URL(saved,import.meta.url))),sha(fs.readFileSync(new URL('../econ-tool-error-recovery-20261027/'+original,import.meta.url))));
 const lock=JSON.parse(fs.readFileSync(new URL('DEPENDENCY-LOCK.json',import.meta.url)));
 for(const [f,h] of Object.entries(lock.files))assert.equal(sha(fs.readFileSync(new URL(f,import.meta.url))),h,f);
 const normalize=s=>s.toLowerCase().replace(/[-_.]+/g,'-');
 const installed=new Set(fs.readFileSync(new URL('requirements.txt',import.meta.url),'utf8').split('\n').filter(x=>/^\S+==/.test(x)).map(x=>normalize(x.split(/\s/)[0])));
 for(const line of fs.readFileSync(new URL('requirements.direct.txt',import.meta.url),'utf8').trim().split('\n'))assert.ok(installed.has(normalize(line)),line);
 const boot=fs.readFileSync(new URL('bootstrap.sh',import.meta.url),'utf8');assert.ok(boot.includes('tesseract --version'));assert.ok(boot.includes('dpkg-query -W tesseract-ocr'));
});
