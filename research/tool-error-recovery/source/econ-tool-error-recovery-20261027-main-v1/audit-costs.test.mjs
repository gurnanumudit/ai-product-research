import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {createClient} from './model-client.mjs';import {inspectCosts} from './audit-costs.mjs';
const id='task-0-A-call-1';
const resp=()=>({id:'gen_synthetic',model:'gpt-6-luna',status:'completed',usage:{input_tokens:10,output_tokens:5,total_tokens:15,input_tokens_details:{cached_tokens:0},output_tokens_details:{reasoning_tokens:1}},output:[{type:'message',role:'assistant',status:'completed',content:[{type:'output_text',text:'code'}]}]});
const receipt=()=>({data:{id:'gen_synthetic',total_cost:'0.0000035',is_byok:false,provider_name:'openai',model:'openai/gpt-6-luna',tokens_prompt:10,tokens_completion:5,latency:7}});
function tmp(t){const d=fs.mkdtempSync(path.join(os.tmpdir(),'tool-report-synthetic-'));t.after(()=>fs.rmSync(d,{recursive:true,force:true}));fs.writeFileSync(path.join(d,'EVENTS.jsonl'),JSON.stringify({kind:'model_intent',call_id:id,task_id:'BigCodeBench/0',arm:'A'})+'\n');return d;}
async function call(d,fetcher,keyLoader=()=> 'SYNTHETIC_KEY_ONLY'){return createClient({fetcher,keyLoader})({input:'invented',outputDir:path.join(d,'calls'),callId:id});}
test('known predispatch HOLD without request preserves attempt and zero dispatch',async t=>{const d=tmp(t);await assert.rejects(call(d,()=>{throw Error('fetch forbidden')},()=>{throw Error('invented key failure')}));const {totals:s}=inspectCosts(d);assert.equal(s.reserved_attempts,1);assert.equal(s.known_undispatched,1);assert.equal(s.physical_post_intents,0);assert.equal(s.pending_nano_usd,0);});
test('unknown dispatched transport has fullreserve and unknown token totals',async t=>{const d=tmp(t);await assert.rejects(call(d,()=>{throw Error('invented transport failure')}));const {totals:s}=inspectCosts(d);assert.equal(s.physical_post_intents,1);assert.equal(s.pending_nano_usd,50e6);assert.equal(s.by_arm.A.input_tokens,null);assert.equal(s.by_arm.A.known_input_tokens,0);assert.equal(s.by_arm.A.usage_unknown_calls,1);assert.equal(s.by_arm.A.provider_latency_ms,null);});
test('unknown intent without client artifacts is reserved and not asserted dispatched',t=>{const d=tmp(t);const s=inspectCosts(d).totals;assert.equal(s.uncertain_dispatch,1);assert.equal(s.pending_nano_usd,50e6);assert.equal(s.physical_post_intents,0);});
test('raw-backed usage and latency; altered derived fields rejected',async t=>{const d=tmp(t);await call(d,async(u,o)=>new Response(JSON.stringify(o.method==='POST'?resp():receipt()),{status:200}));const s=inspectCosts(d).totals;assert.equal(s.by_arm.A.input_tokens,10);assert.equal(s.by_arm.A.provider_latency_ms,7);const f=path.join(d,'calls',id,'charge.json'),original=fs.readFileSync(f,'utf8'),j=JSON.parse(original);j.usage.input=999;fs.writeFileSync(f,JSON.stringify(j));assert.throws(()=>inspectCosts(d),/usage mismatch/);const k=JSON.parse(original);k.raw_receipt_data.latency=999;fs.writeFileSync(f,JSON.stringify(k));assert.throws(()=>inspectCosts(d),/latency mismatch/);});
import {inspectFinancialHistory,verifyMainAdmission} from './audit-costs.mjs';
function snapshot(calls=0,settled=0,pending=0,largest=0){const forecast=Math.max(2188000,2*largest);return {calls,settled_nano_usd:settled,pending_nano_usd:pending,pilot_carry_nano_usd:4091279770,infrastructure_reserve_nano_usd:24e9,forecast_per_call_nano_usd:forecast,largest_observed_main_call_nano_usd:largest,remaining_call_capacity:2880-calls,whole_completion_projection_nano_usd:4091279770+24e9+settled+pending+(2880-calls)*forecast,next_physical_reserve_total_nano_usd:4091279770+24e9+settled+pending+50e6};}
function history(t,events){const d=fs.mkdtempSync(path.join(os.tmpdir(),'main-financial-synthetic-'));t.after(()=>fs.rmSync(d,{recursive:true,force:true}));fs.writeFileSync(path.join(d,'EVENTS.jsonl'),events.map((e,i)=>JSON.stringify({sequence:i+1,...e})).join('\n')+'\n');return d;}
test('main financial replay binds carry,24infra, forecast and both dispatch caps',t=>{
 const call='task-900000-A-call-1';const d=history(t,[{kind:'claim',...snapshot()},{kind:'model_intent',call_id:call,...snapshot(1,0,50e6)},{kind:'model_settled',call_id:call,...snapshot(1,1500000,0,1500000)},{kind:'collection_complete',...snapshot(1,1500000,0,1500000)}]);
 const f=inspectFinancialHistory(d,{reserved_attempts:1,settled_nano_usd:1500000,pending_nano_usd:0,calls:[{call_id:call,settled_nano_usd:1500000,usage:{input:1}}]});
 assert.equal(f.terminal.forecast_per_call_nano_usd,3000000);assert.equal(f.terminal.pilot_carry_nano_usd,4091279770);assert.equal(f.dispatch_checks[0].forecast_before_reserve_nano_usd,34392719770);assert.equal(f.actual_plus_pending_cap_satisfied,true);
});
test('terminal forecast hold overcap is reportable without authorizing another dispatch',t=>{
 const call='task-900000-A-call-1',second='task-900000-A-call-2';
 const events=[{kind:'claim',...snapshot()},{kind:'model_intent',call_id:call,...snapshot(1,0,50e6)},{kind:'model_settled',call_id:call,...snapshot(1,3800000,0,3800000)},{kind:'model_intent',call_id:second,...snapshot(2,3800000,50e6,3800000)},{kind:'model_hold',call_id:second,...snapshot(2,3800000,50e6,3800000)},{kind:'hold',...snapshot(2,3800000,50e6,3800000)}];
 const d=history(t,events),f=inspectFinancialHistory(d,{reserved_attempts:2,settled_nano_usd:3800000,pending_nano_usd:50e6,calls:[{call_id:call,settled_nano_usd:3800000,usage:{input:1}},{call_id:second,settled_nano_usd:0,usage:null}]});
 assert.equal(f.stopped,true);assert.equal(f.actual_plus_pending_cap_satisfied,true);assert.equal(f.remaining_forecast_cap_satisfied,false);
});
test('physical reserve guard independently rejects fitting forecast near cap',()=>{
 assert.throws(()=>verifyMainAdmission({whole_completion_projection_nano_usd:49990000000,next_physical_reserve_total_nano_usd:50000000001}),/physical reserve/);
 assert.throws(()=>verifyMainAdmission({whole_completion_projection_nano_usd:50000000001,next_physical_reserve_total_nano_usd:49990000000}),/forecast/);
 verifyMainAdmission({whole_completion_projection_nano_usd:50e9,next_physical_reserve_total_nano_usd:50e9});
});
test('financial snapshot tampering and dispatch after terminal hold are rejected',t=>{
 const call='task-900000-A-call-1',totals={reserved_attempts:0,settled_nano_usd:0,pending_nano_usd:0,calls:[]};
 const d=history(t,[{kind:'claim',...snapshot(),pilot_carry_nano_usd:0},{kind:'hold',...snapshot()}]);assert.throws(()=>inspectFinancialHistory(d,totals),/snapshot mismatch/);
 const e=history(t,[{kind:'claim',...snapshot()},{kind:'hold',...snapshot()},{kind:'model_intent',call_id:call,...snapshot(1,0,50e6)},{kind:'hold',...snapshot(1,0,50e6)}]);assert.throws(()=>inspectFinancialHistory(e,{...totals,reserved_attempts:1,pending_nano_usd:50e6,calls:[{call_id:call}]}),/dispatch after hold/);
});
test('missing cache-write evidence remains unknown instead of zero',async t=>{
 const d=tmp(t);await call(d,async(u,o)=>new Response(JSON.stringify(o.method==='POST'?resp():receipt()),{status:200}));
 const a=inspectCosts(d).totals.by_arm.A;assert.equal(a.cache_write_tokens,null);assert.equal(a.known_cache_write_tokens,0);assert.equal(a.cache_write_unknown_calls,1);
});
test('raw receipt tampering cannot be hidden by derived charge',async t=>{
 const d=tmp(t);await call(d,async(u,o)=>new Response(JSON.stringify(o.method==='POST'?resp():receipt()),{status:200}));
 const f=path.join(d,'calls',id,'receipt-0.http.json'),j=JSON.parse(fs.readFileSync(f));j.body='{"data":{}}';fs.writeFileSync(f,JSON.stringify(j));assert.throws(()=>inspectCosts(d),/raw receipt binding/);
});
