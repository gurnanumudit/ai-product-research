// Read-only accounting audit; never generates or executes task code.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {reconcile,generationId} from './billing-scoped.mjs';
const need=(b,m)=>{if(!b)throw Error(m)};
const sha=b=>createHash('sha256').update(b).digest('hex');
export function inspectCosts(root){
 const read=f=>JSON.parse(fs.readFileSync(f,'utf8')),directory=path.join(root,'calls');
 const eventsFile=path.join(root,'EVENTS.jsonl');
 const events=fs.existsSync(eventsFile)?fs.readFileSync(eventsFile,'utf8').trim().split('\n').filter(Boolean).map(JSON.parse):null;
 const intents=events?.filter(e=>e.kind==='model_intent')??null;
 const directories=fs.existsSync(directory)?fs.readdirSync(directory).filter(n=>fs.statSync(path.join(directory,n)).isDirectory()):[];
 const names=intents?intents.map(e=>e.call_id):directories;
 need(new Set(names).size===names.length,'duplicate reserved intent');
 need(directories.every(n=>names.includes(n)),'call directory without reserved intent');
 const totals={reserved_attempts:names.length,known_undispatched:0,uncertain_dispatch:0,physical_post_intents:0,settled_calls:0,settled_nano_usd:0,pending_nano_usd:0,receipt_gets:0,by_arm:{},calls:[]};
 const ids=new Set(),pins={};
 if(events)pins['EVENTS.jsonl']=sha(fs.readFileSync(eventsFile));
 for(const name of [...names].sort()){
  const d=path.join(directory,name),exists=n=>fs.existsSync(path.join(d,n));
  const pin=f=>{const full=path.join(d,f);pins[path.relative(root,full)]=sha(fs.readFileSync(full));return read(full)};
  const match=name.match(/^task-(\d+)-([ABC])-call-([1-4])$/);need(match,'call identity format');
  const record={call_id:name,task_id:'BigCodeBench/'+match[1],arm:match[2],round:Number(match[3]),dispatched:exists('DISPATCH.json'),settled_nano_usd:0,pending_nano_usd:0};
  const intent=intents?.find(e=>e.call_id===name);
  if(intent)need(intent.task_id===record.task_id&&intent.arm===record.arm,'intent task-arm binding');
  const a=totals.by_arm[record.arm]??={reserved_attempts:0,known_undispatched:0,uncertain_dispatch:0,physical_post_intents:0,settled_calls:0,settled_nano_usd:0,pending_nano_usd:0,known_input_tokens:0,known_output_tokens:0,known_reasoning_tokens:0,known_cached_tokens:0,known_provider_latency_ms:0,usage_known_calls:0,usage_unknown_calls:0,latency_known_calls:0,latency_unknown_calls:0};a.reserved_attempts++;
  const hold=exists('HOLD.json')?pin('HOLD.json'):null;
  if(hold)need(hold.call_id===name,'hold identity');
  const knownUndispatched=hold?.request_dispatched===false;
  need(!(knownUndispatched&&record.dispatched),'conflicting dispatch evidence');
  const r=exists('request.json')?pin('request.json'):null;
  if(r){
   need(r.call_id===name,'call directory identity');const body=r.body;
   need(r.request_sha256===sha(JSON.stringify(body)),'request body hash');
   need(body.model==='openai/gpt-6-luna'&&body.reasoning?.effort==='medium'&&body.max_output_tokens===8192&&body.providerOptions?.gateway?.only?.join(',')==='openai'&&body.service_tier==='default'&&body.tools?.length===0&&body.stream===false&&body.store===false,'model/configuration changed');
   need(r.reserve_nano_usd===50e6,'reserve mismatch');
  }else need(knownUndispatched||(!record.dispatched&&!exists('charge.json')),'request missing without pre-dispatch or uncertain pre-client evidence');
  for(const n of (fs.existsSync(d)?fs.readdirSync(d):[]).filter(n=>/^receipt-\d+\.http\.json$/.test(n))){pin(n);totals.receipt_gets++;}
  if(record.dispatched){const dis=pin('DISPATCH.json');need(dis.call_id===name&&dis.model_request_attempts===1,'dispatch identity');totals.physical_post_intents++;a.physical_post_intents++;}
  else if(knownUndispatched){record.dispatch_status='known_undispatched';totals.known_undispatched++;a.known_undispatched++;}
  else{record.dispatch_status='uncertain_dispatch';totals.uncertain_dispatch++;a.uncertain_dispatch++;}
  if(exists('charge.json')){
   need(record.dispatched,'settled without dispatch');
   const http=pin('response.http.json'),response=pin('response.json'),receipt=pin('receipt.json'),charge=pin('charge.json');
   need(http.status>=200&&http.status<300&&JSON.stringify(JSON.parse(http.body))===JSON.stringify(response),'raw response binding');
   const id=generationId(response);need(!ids.has(id),'duplicate physical charge');ids.add(id);
   const recomputed=reconcile(response,receipt,id);need(recomputed.cost_nano_usd===charge.cost_nano_usd,'charge reconciliation');
   need(JSON.stringify(recomputed.usage)===JSON.stringify(charge.usage),'derived usage mismatch');
   need(recomputed.raw_receipt_data?.latency===charge.raw_receipt_data?.latency,'derived latency mismatch');
   record.settled_nano_usd=recomputed.cost_nano_usd;record.usage=recomputed.usage;record.provider_latency_ms=recomputed.raw_receipt_data?.latency??null;
   totals.settled_calls++;a.settled_calls++;totals.settled_nano_usd+=record.settled_nano_usd;a.settled_nano_usd+=record.settled_nano_usd;a.usage_known_calls++;
   for(const [out,key] of [['known_input_tokens','input'],['known_output_tokens','output'],['known_reasoning_tokens','reasoning'],['known_cached_tokens','cached']])a[out]+=record.usage[key];
   if(Number.isFinite(record.provider_latency_ms)){a.known_provider_latency_ms+=record.provider_latency_ms;a.latency_known_calls++;}else a.latency_unknown_calls++;
  }else if(!knownUndispatched){record.pending_nano_usd=50e6;totals.pending_nano_usd+=50e6;a.pending_nano_usd+=50e6;record.usage=null;record.provider_latency_ms=null;a.usage_unknown_calls++;a.latency_unknown_calls++;}
  totals.calls.push(record);
 }
 need(totals.reserved_attempts<=480,'pilot attempt limit');
 for(const a of Object.values(totals.by_arm)){
  for(const k of ['input_tokens','output_tokens','reasoning_tokens','cached_tokens'])a[k]=a.usage_unknown_calls?null:a['known_'+k];
  a.provider_latency_ms=a.latency_unknown_calls?null:a.known_provider_latency_ms;
 }
 totals.note='Reserved attempts, known undispatched holds, dispatch intents and uncertain dispatch are distinct. Reasoning is included within output tokens. Known usage subtotals are not complete totals when unknown-call coverage is nonzero. Reserves are not active calls. Provider latency excludes client/receipt/setup overhead.';
 return {totals,pins};
}
